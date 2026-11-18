"""Run the Job 23 known answer, discovered-check control, or clean asserts."""

import argparse
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

JOB = Path(__file__).resolve().parent
sys.path.insert(0, str(JOB.parent / 'job22'))
from sanitizer_uci import Session, digest, fixture_fens, parse_search
from identity import NET_SHA, PC20
from parse_sanitizers import parse_run

ASSERT = re.compile(r'^job23 assert (A[123]) move (\S+)(.*)$', re.MULTILINE)
FEN = re.compile(r'^job23 (?:assert )?fen (.+)$', re.MULTILINE)
GLIBC_ASSERT = re.compile(r'Assertion .+ failed\.')
FIELDS = ('search', 'process', 'row', 'ply', 'fen', 'status', 'nodes',
          'nodes_source', 'depth', 'bestmove', 'last_info_line', 'bestmove_line')
GAME_FIELDS = ('row', 'plies', 'nodes', 'termination', 'result', 'moves')


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
        expected = ['fen', 'classes', 'discovered_moves', 'double_checks']
        if reader.fieldnames != expected:
            raise ValueError(f'unexpected P columns {reader.fieldnames}')
        positions = list(reader)
    if not 0 < len(positions) <= 2000 or len({p['fen'] for p in positions}) != len(positions):
        raise ValueError('P must have 1–2000 distinct FENs')
    for row in positions:
        board = chess.Board(row['fen'])
        if not board.is_valid() or board.is_check() or not row['classes']:
            raise ValueError(f'invalid P row {row}')
    return list(enumerate(positions, 1))


class Matrix:
    def __init__(self, args, stack):
        self.args = args
        self.output = args.output
        self.rows = tsv(args.output / 'rows.tsv', FIELDS, stack)
        self.games = tsv(args.output / 'games.tsv', GAME_FIELDS, stack)
        self.processes = []
        self.attempts = 0
        self.completed = 0
        self.game_count = 0
        self.nodes = 0
        self.nodes_without_label = 0
        self.findings = []
        self.active = None
        self.last = None
        self.stack = None
        self.session = None
        self.stdout_count = 0

    def start(self):
        self.stack = ExitStack()
        self.dir = self.output / f'process-{len(self.processes) + 1:04d}'
        self.dir.mkdir()
        self.active = None
        self.last = None
        self.started = utc()
        streams = [self.stack.enter_context((self.dir / name).open('xb'))
                   for name in ('stdout.txt', 'stderr.txt', 'commands.txt')]
        self.session = Session([str(self.args.engine)], *streams, self.args.timeout)
        self.session.launch()
        self.active = self.session.setup(self.args.net, PC20)

    def close(self, failed=False, error=None):
        if self.session is None:
            return None
        session, self.session = self.session, None
        try:
            status = session.close(failed)
        finally:
            self.stack.close()
        with (self.dir / 'stdout.txt').open('rb') as stdout:
            bestmoves = sum(line.startswith(b'bestmove ') for line in stdout)
        self.stdout_count += bestmoves
        stderr = self.dir / 'stderr.txt'
        content = stderr.read_text(encoding='utf-8', errors='replace')
        hit = ASSERT.search(content)
        fen = FEN.search(content)
        report = parse_run(self.dir.name, stderr)
        process = {
            'process': self.dir.name, 'exit': status, 'bestmoves': bestmoves,
            'net_active': self.active, 'started_utc': self.started, 'finished_utc': utc(),
            'error': error, 'shutdown_interventions': session.interventions,
            'assert': hit[1] if hit else 'engine' if GLIBC_ASSERT.search(content) else None,
            'assert_move': hit[2] if hit else None,
            'assert_fen': fen[1] if fen else None,
            'assert_detail': hit[3].strip() if hit else None,
            'checker_reports': report['total_blocks'] - report['runtime_failure_blocks'],
            'runtime_failure_blocks': report['runtime_failure_blocks'],
            'stderr_bytes': stderr.stat().st_size,
            'sha256': {path.name: digest(path) for path in sorted(self.dir.iterdir())},
        }
        self.processes.append(process)
        if process['assert'] or process['checker_reports']:
            self.findings.append({'search': self.last, **process,
                                  'first_30_lines': content.splitlines()[:30],
                                  'checker_excerpts': [finding['first_30_lines'] for finding in report['reports']]})
        return process

    def run_move(self, index, board, command, go, ply=''):
        if self.session is None:
            self.start()
        self.session.send(command)
        self.attempts += 1
        row = {'search': self.attempts, 'process': self.dir.name,
               'row': index, 'ply': ply, 'fen': board.fen()}
        self.last = row.copy()
        try:
            label = parse_search(self.session.search(go), go)
            move = board.parse_uci(label['bestmove'])
            if not move and any(board.legal_moves):
                raise ValueError('null bestmove at a root with legal moves')
        except KeyboardInterrupt:
            self.rows.writerow({**row, 'status': 'cutoff'})
            raise
        except (OSError, RuntimeError, ValueError) as error:
            self.rows.writerow({**row, 'status': 'interrupted'})
            result = self.close(True, str(error))
            if result['assert'] or result['checker_reports']:
                return None
            raise RuntimeError(f'unclassified failed search {row}: {error}') from error
        self.rows.writerow({**row, 'status': 'bestmove', **label})
        self.completed += 1
        if label['nodes'] == '':
            self.nodes_without_label += 1
        else:
            self.nodes += label['nodes']
        return label, move

    def depth(self, positions):
        for index, fen in positions:
            if self.session is None:
                self.start()
            self.session.reset()
            result = self.run_move(index, chess.Board(fen), f'position fen {fen}', 'go depth 9')
            if result is None and self.args.part in ('known', 'control'):
                break

    def play(self, positions):
        for index, fen in positions:
            if self.session is None:
                self.start()
            self.session.reset()
            board = chess.Board(fen)
            command = f'position fen {fen}'
            moves = []
            used_nodes = 0
            while len(moves) < 200 and not board.is_game_over(claim_draw=True):
                sequence = command + ' moves' + ''.join(f' {move}' for move in moves)
                result = self.run_move(index, board, sequence, 'go softnodes 2000', len(moves) + 1)
                if result is None:
                    break
                label, move = result
                moves.append(label['bestmove'])
                used_nodes += label['nodes']
                board.push(move)
            outcome = board.outcome(claim_draw=True)
            if self.session is None:
                termination = 'FINDING'
            else:
                self.game_count += 1
                termination = outcome.termination.name if outcome is not None else 'PLY_CAP'
            self.games.writerow({'row': index, 'plies': len(moves), 'nodes': used_nodes,
                                 'termination': termination, 'result': outcome.result() if outcome else '*',
                                 'moves': ' '.join(moves)})

    def run(self, positions):
        error = None
        try:
            if self.args.part == 'r2':
                self.play(positions)
            else:
                self.depth(positions)
        except (RuntimeError, OSError, ValueError, KeyboardInterrupt) as exc:
            error = f'{type(exc).__name__}: {exc}'
        exit_record = self.close(error is not None, error)
        if exit_record and exit_record['exit'] and not (exit_record['assert'] or exit_record['checker_reports']):
            error = error or f"unexpected process exit {exit_record['exit']}"
        if self.stdout_count != self.completed:
            error = error or 'raw bestmove and successfully parsed search counts differ'
        return error


def matrix_arguments(args):
    if args.part == 'known':
        return list(enumerate(fixture_fens(args.fixture)[:200], 1))
    positions = position_set(args.fixture)
    if args.part in ('control', 'r2'):
        positions = [(index, entry) for index, entry in positions if 'D' in entry['classes']]
    if args.part == 'r2':
        positions.sort(key=lambda row: (-int(row[1]['discovered_moves']), row[1]['fen']))
        if len(positions) < 10:
            raise ValueError('fewer than ten class-D starts available')
        positions = positions[:10]
    return [(index, entry['fen']) for index, entry in positions]


def terminate(signum, frame):
    raise KeyboardInterrupt('minute-50 cutoff received')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--part', choices=('known', 'control', 'r1', 'r2'), required=True)
    for name in ('engine', 'net', 'fixture', 'output'):
        parser.add_argument(f'--{name}', type=Path, required=True)
    for name in ('engine', 'fixture'):
        parser.add_argument(f'--{name}-sha256', required=True)
    parser.add_argument('--timeout', type=float, default=45)
    args = parser.parse_args()
    if chess.__version__ != '1.11.2':
        parser.error(f'mismatched python-chess {chess.__version__}')
    args.engine = args.engine.resolve(strict=True)
    args.net = args.net.resolve(strict=True)
    wanted = ((args.engine, args.engine_sha256), (args.net, NET_SHA), (args.fixture, args.fixture_sha256))
    for path, expected in wanted:
        if digest(path) != expected:
            parser.error(f'SHA-256 mismatch for {path}')
    positions = matrix_arguments(args)
    if not positions:
        parser.error(f'no {args.part} starts')
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.signal(signal.SIGTERM, terminate)
    args.output.mkdir(parents=True)
    started = utc()
    with ExitStack() as stack:
        run = Matrix(args, stack)
        error = run.run(positions)
    result = {
        'part': args.part, 'engine_sha256': args.engine_sha256, 'net_sha256': NET_SHA,
        'fixture_sha256': args.fixture_sha256, 'options': PC20,
        'sanitizers': {key: os.environ.get(key) for key in ('ASAN_OPTIONS', 'UBSAN_OPTIONS')},
        'started_utc': started, 'finished_utc': utc(), 'scheduled_rows': [index for index, _ in positions],
        'searches': run.attempts, 'bestmoves': run.stdout_count, 'completed_searches': run.completed,
        'reported_nodes': run.nodes, 'completed_without_nodes': run.nodes_without_label,
        'completed_games': run.game_count,
        'assert_stops': sum(bool(process['assert']) for process in run.processes),
        'checker_reports': sum(process['checker_reports'] for process in run.processes),
        'runtime_failures': sum(process['runtime_failure_blocks'] for process in run.processes),
        'processes': run.processes, 'findings': run.findings, 'error': error,
    }
    (args.output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    if error is not None:
        print(error, file=sys.stderr)
    return int(error is not None)


if __name__ == '__main__':
    raise SystemExit(main())
