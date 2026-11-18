#!/usr/bin/env python3
"""Run the Job 24 known answers, controls, and game replay with raw UCI evidence."""

import argparse
from collections import Counter
from contextlib import ExitStack
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import resource
import signal
import sys

import chess

JOB22 = Path(__file__).resolve().parent.parent / 'job22'
if JOB22.is_dir():
    sys.path.insert(0, str(JOB22))
from identity import NET_SHA, PC20
from parse_sanitizers import parse_run
from sanitizer_uci import Session, digest, fixture_fens, parse_search


PARTS = ('known', 'r1', 'wrong2', 'new-blind', 'old-blind', 'r2')
BLIND = ('new-blind', 'old-blind')
W1_SHA = '3c1b17332eca46a912f572eae8197324f466a8e2f909653104c427457ffb0521'
P_SHA = 'e7100aae3c0a8ac1a9966fb8d746ec9511bbd63513ef4ecea99bd38b6255dfae'
ASSERT = re.compile(r'^job2[34] assert (A1s|A2s|A[12347]) move (\S+)(.*)$', re.MULTILINE)
FEN = re.compile(r'^job2[34] (?:assert )?fen (.+)$', re.MULTILINE)
GLIBC_ASSERT = re.compile(r'Assertion .+ failed\.')
ROW_FIELDS = ('search', 'process', 'row', 'ply', 'fen', 'go', 'search_sent', 'status', 'nodes', 'nodes_source',
              'depth', 'bestmove', 'last_info_line', 'bestmove_line', 'error')
GAME_FIELDS = ('row', 'plies', 'nodes', 'termination', 'result', 'moves')
BLIND_FIELDS = ('rank', 'row', 'fen', 'process', 'status', 'exit', 'search_sent', 'raw_bestmoves', 'nodes', 'bestmove',
                'assert', 'assert_move', 'assert_fen', 'assert_detail', 'checker_reports', 'runtime_failures', 'error')
PLAN_FIELDS = ('rank', 'row', 'fen', 'classes', 'pieces')


def utc():
    return datetime.now(timezone.utc).isoformat()


def tsv(path, fields, stack):
    stream = stack.enter_context(path.open('x', newline='', encoding='utf-8', buffering=1))
    writer = csv.DictWriter(stream, fieldnames=fields, delimiter='\t', lineterminator='\n')
    writer.writeheader()
    return writer


def position_set(path):
    with path.open(newline='', encoding='ascii') as source:
        reader = csv.DictReader(source, delimiter='\t')
        if reader.fieldnames != ['fen', 'classes', 'discovered_moves', 'double_checks']:
            raise ValueError(f'unexpected P columns {reader.fieldnames}')
        rows = list(reader)
    if len(rows) != 2000 or len({entry['fen'] for entry in rows}) != len(rows):
        raise ValueError('P must have 2,000 distinct FENs')
    for index, row in enumerate(rows, 1):
        board = chess.Board(row['fen'])
        if not board.is_valid() or board.is_check() or not row['classes']:
            raise ValueError(f'invalid P row {index}')
        row.update(row=index, pieces=board.occupied.bit_count())
    return rows


def plan(part, path):
    if part == 'known':
        return [{'row': index, 'fen': fen} for index, fen in enumerate(fixture_fens(path)[:200], 1)]
    rows = position_set(path)
    if part == 'wrong2':
        if rows[0]['classes'] != 'DQ':
            raise ValueError('P row one must be class DQ')
        return rows[:1]
    if part in BLIND:
        rows = [row for row in rows if 'X' in row['classes']][:20]
    elif part == 'r2':
        rows = sorted((row for row in rows if 'P' in row['classes'] or 'X' in row['classes']),
                      key=lambda row: (-row['pieces'], row['fen']))[:20]
    if part != 'r1' and len(rows) != 20:
        raise ValueError('fewer than twenty control or game starts')
    return rows


def write_plan(fixture_path, output):
    if digest(fixture_path) != P_SHA:
        raise ValueError('wrong published Job23 P fixture')
    output.mkdir(parents=True, exist_ok=False)
    ranks = {name: plan(part, fixture_path) for name, part in (('blind', 'new-blind'), ('r2', 'r2'))}
    with ExitStack() as stack:
        for name, starts in ranks.items():
            writer = tsv(output / f'{name}.tsv', PLAN_FIELDS, stack)
            for rank, record in enumerate(starts, 1):
                writer.writerow({'rank': rank, **{key: record[key] for key in PLAN_FIELDS[1:]}})
    receipt = {'fixture_sha256': P_SHA, 'python_chess': chess.__version__,
               'blind_order': 'published P order, first twenty rows tagged X',
               'r2_order': 'P or X, descending pieces including both kings, ties by lexical FEN',
               'selected_indices': {name: [row['row'] for row in starts] for name, starts in ranks.items()},
               'piece_histogram': {name: dict(sorted(Counter(row['pieces'] for row in starts).items()))
                                   for name, starts in ranks.items()},
               'sha256': {path.name: digest(path) for path in sorted(output.iterdir())}}
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='ascii')
    return receipt


class Matrix:
    def __init__(self, args, stack):
        self.args = args
        self.rows = tsv(args.output / 'rows.tsv', ROW_FIELDS, stack)
        self.games = tsv(args.output / 'games.tsv', GAME_FIELDS, stack)
        self.blind = tsv(args.output / 'blind.tsv', BLIND_FIELDS, stack) if args.part in BLIND else None
        self.processes = []
        self.findings = []
        self.statuses = Counter()
        self.trials = 0
        self.sent = 0
        self.completed = 0
        self.game_count = 0
        self.nodes = 0
        self.nodes_without_label = 0
        self.stack = None
        self.session = None
        self.active = None
        self.last = None

    def start(self):
        self.stack = ExitStack()
        self.dir = self.args.output / f'process-{len(self.processes) + 1:04d}'
        self.dir.mkdir()
        self.started = utc()
        self.active = None
        streams = [self.stack.enter_context((self.dir / name).open('xb'))
                   for name in ('stdout.txt', 'stderr.txt', 'commands.txt')]
        self.session = Session([str(self.args.engine)], *streams, self.args.timeout)
        self.session.launch()
        self.active = self.session.setup(self.args.net, PC20)

    def close(self, error=None):
        if self.session is None:
            return None
        session, self.session = self.session, None
        close_error = None
        try:
            status = session.close(error is not None)
        except (ValueError, OSError, RuntimeError) as exc:
            status = session.process.poll() if session.process is not None else None
            close_error = f'{type(exc).__name__}: {exc}'
        finally:
            self.stack.close()
        with (self.dir / 'stdout.txt').open('rb') as stdout:
            bestmoves = sum(line.startswith(b'bestmove ') for line in stdout)
        stderr = self.dir / 'stderr.txt'
        content = stderr.read_text(encoding='utf-8', errors='replace')
        hit = ASSERT.search(content)
        fen = FEN.search(content, pos=hit.end() if hit else 0)
        report = parse_run(self.dir.name, stderr)
        process = {
            'process': self.dir.name, 'exit': status, 'bestmoves': bestmoves, 'net_active': self.active,
            'started_utc': self.started, 'finished_utc': utc(), 'error': error, 'shutdown_error': close_error,
            'failed_command_write': session.failed_command, 'shutdown_interventions': session.interventions,
            'assert': hit[1] if hit else 'engine' if GLIBC_ASSERT.search(content) else None,
            'assert_move': hit[2] if hit else None, 'assert_fen': fen[1] if fen else None,
            'assert_detail': hit[3].strip() if hit else None,
            'checker_reports': report['total_blocks'] - report['runtime_failure_blocks'],
            'runtime_failure_blocks': report['runtime_failure_blocks'], 'stderr_bytes': stderr.stat().st_size,
            'sha256': {path.name: digest(path) for path in sorted(self.dir.iterdir())},
        }
        self.processes.append(process)
        if process['assert'] or process['checker_reports'] or process['runtime_failure_blocks'] or error or close_error or status:
            self.findings.append({'search': self.last, **process, 'first_30_lines': content.splitlines()[:30],
                                  'checker_excerpts': [finding['first_30_lines'] for finding in report['reports']]})
        return process

    @staticmethod
    def classify(process, stage, error):
        if process and process['assert']:
            return 'assert_stop'
        if process and process['checker_reports']:
            return 'checker_report'
        if process and process['runtime_failure_blocks']:
            return 'sanitizer_runtime_failure'
        if stage == 'startup' and error:
            return 'startup_failure'
        if stage == 'ready' and error:
            return 'reset_failure'
        if stage == 'legality' and error:
            return 'illegal_bestmove'
        if stage == 'label' and error:
            return 'unusable_bestmove_label'
        if process and process['exit'] not in (None, 0):
            return 'native_exit_after_bestmove' if stage == 'done' else 'native_exit_before_bestmove'
        if error:
            return 'protocol_failure_before_bestmove'
        if process and process['shutdown_error']:
            return 'shutdown_failure'
        return 'bestmove'

    def search(self, index, board, command, go, *, fresh=False, reset=False, ply=''):
        self.trials += 1
        row = {'search': self.trials, 'process': '', 'row': index, 'ply': ply,
               'fen': board.fen(), 'go': go, 'search_sent': 0}
        self.last = row.copy()
        move = None
        label = {}
        error = None
        stage = 'startup'
        try:
            if self.session is None:
                self.start()
            row['process'] = self.dir.name
            stage = 'ready'
            if reset:
                self.session.reset()
            stage = 'search'
            self.session.send(command)
            self.sent += 1
            row['search_sent'] = 1
            self.last = row.copy()
            result = self.session.search(go)
            stage = 'label'
            label = parse_search(result, go)
            stage = 'legality'
            move = board.parse_uci(label['bestmove'])
            if not move and any(board.legal_moves):
                raise ValueError('null bestmove at a root with legal moves')
            stage = 'done'
        except KeyboardInterrupt:
            self.rows.writerow({**row, 'status': 'cutoff'})
            self.statuses['cutoff'] += 1
            raise
        except (ValueError, OSError, RuntimeError) as exc:
            error = f'{type(exc).__name__}: {exc}'
        if not row['process'] and self.session is not None:
            row['process'] = self.dir.name
        self.last = row.copy()
        process = self.close(error) if fresh or error else None
        status = self.classify(process, stage, error)
        self.statuses[status] += 1
        receipt = {**row, **label, 'status': status, 'error': error}
        self.rows.writerow(receipt)
        if label:
            if label['nodes'] == '':
                self.nodes_without_label += 1
            else:
                self.nodes += label['nodes']
        valid = status == 'bestmove'
        self.completed += valid
        return receipt, move if valid else None, process

    def depth(self, positions):
        for rank, entry in enumerate(positions, 1):
            fen, index = entry['fen'], entry['row']
            is_blind = self.blind is not None
            row, _, process = self.search(index, chess.Board(fen), f'position fen {fen}',
                                          'go depth 4' if is_blind else 'go depth 9', fresh=is_blind, reset=True)
            if is_blind:
                raw = process or {}
                self.blind.writerow({**{key: row.get(key) for key in ('row', 'fen', 'process', 'status', 'search_sent',
                                                                      'nodes', 'bestmove', 'error')},
                                     **{key: raw.get(key) for key in ('exit', 'assert', 'assert_move', 'assert_fen',
                                                                    'assert_detail', 'checker_reports')},
                                     'rank': rank, 'raw_bestmoves': raw.get('bestmoves', 0),
                                     'runtime_failures': raw.get('runtime_failure_blocks', 0)})
                if self.args.part == 'new-blind' and rank == 1 and not (
                        row['status'] == 'assert_stop' and raw.get('assert') in ('A2s', 'A4')):
                    raise RuntimeError(f"first new-blind position missed required A2s/A4 stop: {row['status']}, {raw.get('assert')}")
            elif row['status'] != 'bestmove':
                if self.args.part in ('known', 'r1'):
                    raise RuntimeError(f"required known-answer row {index} failed: {row['status']}")
                break

    def play(self, positions):
        for entry in positions:
            fen, index = entry['fen'], entry['row']
            board = chess.Board(fen)
            moves = []
            nodes = 0
            failed = False
            while len(moves) < 200 and not board.is_game_over(claim_draw=True):
                prefix = f'position fen {fen} moves' + ''.join(f' {move}' for move in moves)
                row, move, _ = self.search(index, board, prefix, 'go softnodes 2000', reset=not moves, ply=len(moves) + 1)
                if row['status'] != 'bestmove':
                    failed = True
                    break
                if move is None or not move:
                    raise RuntimeError(f'no legal move on R2 row {index}')
                nodes += row['nodes']
                moves.append(row['bestmove'])
                board.push(move)
            outcome = board.outcome(claim_draw=True)
            termination = 'FINDING' if failed else outcome.termination.name if outcome else 'PLY_CAP'
            self.games.writerow({'row': index, 'plies': len(moves), 'nodes': nodes, 'termination': termination,
                                 'result': outcome.result() if outcome else '*', 'moves': ' '.join(moves)})
            self.game_count += not failed

    def run(self, positions):
        error = None
        try:
            if self.args.part == 'r2':
                self.play(positions)
            else:
                self.depth(positions)
        except (RuntimeError, OSError, ValueError, KeyboardInterrupt) as exc:
            error = f'{type(exc).__name__}: {exc}'
        final = self.close(error)
        if final and (final['exit'] != 0 or final['shutdown_error'] or final['assert'] or final['checker_reports']):
            error = error or f"unfinished process close: exit {final['exit']}"
        return error


def terminate(signum, frame):
    raise KeyboardInterrupt('minute-50 cutoff received')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--part', choices=PARTS + ('plan',), required=True)
    for option in ('engine', 'net', 'fixture', 'output'):
        parser.add_argument('--' + option, type=Path, required=option in ('fixture', 'output'))
    for option in ('engine', 'fixture'):
        parser.add_argument(f'--{option}-sha256')
    parser.add_argument('--timeout', type=float, default=45)
    args = parser.parse_args()
    if chess.__version__ != '1.11.2':
        parser.error(f'mismatched python-chess {chess.__version__}')
    if args.part == 'plan':
        print(json.dumps(write_plan(args.fixture, args.output), indent=2))
        return 0
    if not (args.engine and args.net and args.engine_sha256 and args.fixture_sha256 and 0 < args.timeout <= 300):
        parser.error('engine, net, both hashes, and a timeout up to 300 seconds are required')
    args.engine = args.engine.resolve(strict=True)
    args.net = args.net.resolve(strict=True)
    fixture_pin = W1_SHA if args.part == 'known' else P_SHA
    if args.fixture_sha256 != fixture_pin:
        parser.error('requested fixture is outside the published Job24 plan')
    wanted = ((args.engine, args.engine_sha256), (args.net, NET_SHA), (args.fixture, args.fixture_sha256))
    for path, expected in wanted:
        if digest(path) != expected:
            parser.error(f'SHA-256 mismatch for {path}')
    positions = plan(args.part, args.fixture)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.signal(signal.SIGTERM, terminate)
    args.output.mkdir(parents=True, exist_ok=False)
    started = utc()
    with ExitStack() as stack:
        matrix = Matrix(args, stack)
        error = matrix.run(positions)
    result = {
        'part': args.part, 'engine_sha256': args.engine_sha256, 'net_sha256': NET_SHA, 'net_path': str(args.net),
        'fixture_sha256': fixture_pin, 'options': PC20,
        'sanitizers': {key: os.environ.get(key) for key in ('ASAN_OPTIONS', 'UBSAN_OPTIONS')},
        'runner_sha256': digest(Path(__file__)), 'started_utc': started, 'finished_utc': utc(),
        'scheduled_rows': [entry['row'] for entry in positions], 'trials': matrix.trials, 'searches': matrix.sent,
        'bestmoves': sum(process['bestmoves'] for process in matrix.processes), 'completed_searches': matrix.completed,
        'reported_nodes': matrix.nodes, 'labels_without_nodes': matrix.nodes_without_label, 'completed_games': matrix.game_count,
        'statuses': dict(matrix.statuses), 'assert_stops': sum(bool(process['assert']) for process in matrix.processes),
        'checker_reports': sum(process['checker_reports'] for process in matrix.processes),
        'runtime_failures': sum(process['runtime_failure_blocks'] for process in matrix.processes),
        'processes': matrix.processes, 'findings': matrix.findings, 'error': error,
    }
    (args.output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    if error is not None:
        print(error, file=sys.stderr)
    return int(error is not None)


if __name__ == '__main__':
    raise SystemExit(main())
