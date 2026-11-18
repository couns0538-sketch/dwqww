"""Read only. Reconstruct clean Job 22 schedules and labels from UCI captures."""

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re

import chess


FIXTURE_SHA = '3c1b17332eca46a912f572eae8197324f466a8e2f909653104c427457ffb0521'


def check(test, message):
    if not test:
        raise ValueError(message)


def tsv(path):
    with path.open(encoding='ascii', newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def lines(path):
    return path.read_text(encoding='ascii').splitlines()


class Transcript:
    def __init__(self, directory, startup):
        self.output = iter(lines(directory / 'engine.stdout.txt'))
        self.commands = iter(lines(directory / 'engine.commands.txt'))
        self.rows = iter(tsv(directory / 'rows.tsv'))
        self.games = iter(tsv(directory / 'games.tsv'))
        self.timing = iter(tsv(directory / 'infinite.tsv'))
        self.duration = []
        self.ply_count = 0
        self.outcomes = Counter()
        self.search_count = 0
        self.phase_totals = defaultdict(Counter)
        self.d9_mismatch = []
        self.set_threads = []
        self.resets = 0
        self.readies = 0
        for command in startup:
            self.expect(command)
            if command.startswith('setoption name Threads value '):
                self.set_threads.append(int(command.split()[-1]))
        setup = self.until('readyok')
        self.readies += 1
        active = [line for line in setup if line.startswith('info string NNUE v3 active: ')]
        check(len(active) == 1 and 'hidden 768' in active[0] and 'checksum 30ab43b4ba5db5f3' in active[0]
              and setup.count('uciok') == 1 and setup.index('uciok') < setup.index(active[0]),
              'missing activation plus checksum proof or startup order')
        self.activation = active[0]

    def expect(self, command):
        got = next(self.commands, None)
        check(command == got, f'expected {command!r}, got {got!r}')

    def until(self, marker):
        result = []
        for line in self.output:
            result.append(line)
            if (line == 'readyok' if marker == 'readyok' else line.startswith('bestmove ')):
                return result
        raise ValueError(f'stdout ended before {marker!r}')

    def threads(self, count):
        self.expect(f'setoption name Threads value {count}')
        self.set_threads.append(count)

    def reset(self):
        self.expect('ucinewgame')
        self.expect('isready')
        check(next(self.output, None) == 'readyok', 'missing isolated ready acknowledgment')
        self.resets += 1
        self.readies += 1

    def search(self, fens, index, thread_count, mode, phase, board=None, moves=None):
        root = fens[index - 1]
        command = f'position fen {root}'
        if moves is not None:
            command += ' moves' + ''.join(f' {move}' for move in moves)
        self.expect(command)
        self.expect(mode)
        if mode == 'go infinite':
            self.expect('stop')
            receipt = next(self.timing, None)
            check(bool(receipt), 'missing timed stop receipt')
            start, due, stop, elapsed = map(int, (receipt[name] for name in (
                'go_monotonic_ns', 'scheduled_stop_monotonic_ns', 'stop_monotonic_ns', 'go_to_stop_ns')))
            check(receipt['w1_position'] == str(index) and receipt['threads'] == str(thread_count)
                  and due == start + 100_000_000 and stop >= due and stop - start == elapsed,
                  f'wrong timed stop receipt on W1 row {index}')
            if self.duration:
                check(start > self.duration[-1][1], 'timed searches overlap')
            self.duration.append((elapsed, stop))

        out = self.until('bestmove')
        check(not any(line in {'uciok', 'readyok'} or line.startswith('info string NNUE v3 active: ')
                      for line in out), 'unexpected handshake inside search output')
        best = re.fullmatch(r'bestmove (0000|[a-h][1-8][a-h][1-8][qrbn]?)(?: ponder [a-h][1-8][a-h][1-8][qrbn]?)?', out[-1])
        check(best is not None, f'invalid bestmove line {out[-1]!r}')
        fin = [line for line in out if line.startswith('info string softnodes nodes ')]
        depth_rows = [line for line in out if line.startswith('info depth ')]
        last = depth_rows[-1] if depth_rows else ''
        good = re.search(r'^info depth ([0-9]+)\b.*\bnodes ([0-9]+)\b', last) if last else None
        check(bool(good) == bool(last), 'malformed depth information')
        if mode == 'go softnodes 2000':
            check(len(fin) == 1 and out[-2] == fin[0] and re.fullmatch(r'info string softnodes nodes [0-9]+', fin[0]),
                  'missing or misplaced exact final softnodes marker')
            nodes = int(fin[0].split()[-1])
            if good:
                check(int(good[2]) <= nodes, 'last-info node count exceeds consumed nodes')
            source = 'final_softnodes'
        elif good:
            check(not fin, 'unexpected final softnodes marker in fixed or infinite search')
            nodes = int(good[2])
            source = 'last_info'
        else:
            check(not fin, 'unexpected final softnodes marker in fixed or infinite search')
            nodes = None
            source = 'no_node_info'

        self.search_count += 1
        totals = self.phase_totals[phase, thread_count]
        totals['searches'] += 1
        totals['missing_nodes'] += nodes is None
        totals['nodes'] += nodes or 0
        row = {'search': str(self.search_count), 'phase': phase, 'threads': str(thread_count), 'w1_position': str(index),
               'ply': str(len(moves) + 1) if moves is not None else '', 'fen': board.fen() if board is not None else root,
               'nodes': str(nodes) if nodes is not None else '', 'nodes_source': source, 'depth': good[1] if good else '',
               'bestmove': best[1], 'last_info_line': last, 'bestmove_line': out[-1]}
        check(row == next(self.rows, None), f'parsed row disagrees with raw command/stdout at search {self.search_count}')
        return row

    def play(self, fens, positions, phase):
        for index in positions:
            self.reset()
            board = chess.Board(fens[index - 1])
            moves = []
            total = 0
            while len(moves) < 200 and not board.is_game_over(claim_draw=True):
                row = self.search(fens, index, 1, 'go softnodes 2000', phase, board=board, moves=moves)
                candidate = chess.Move.from_uci(row['bestmove'])
                check(candidate in board.legal_moves, f'illegal game move {candidate.uci()}')
                board.push(candidate)
                moves.append(candidate.uci())
                total += int(row['nodes'])
            outcome = board.outcome(claim_draw=True)
            end = outcome.termination.name if outcome else 'PLY_CAP'
            self.outcomes[end] += 1
            self.ply_count += len(moves)
            row = {'phase': phase, 'threads': '1', 'w1_position': str(index), 'plies': str(len(moves)), 'nodes': str(total),
                   'termination': end, 'result': outcome.result() if outcome else '*', 'moves': ' '.join(moves)}
            check(row == next(self.games, None), f'game row differs from raw at W1 position {index}')

    def finish(self, summary):
        self.expect('quit')
        for table in (self.commands, self.output, self.rows, self.games, self.timing):
            check(next(table, None) is None, 'unexpected extra input/output/parsed row')
        check(self.search_count == summary['completed_searches'] == summary['raw_bestmove_lines']
              and sum(self.outcomes.values()) == summary['completed_games'] and self.activation == summary['net_active'],
              'summary does not match reconstructed counts')
        by_phase = defaultdict(Counter)
        for (phase, _), values in self.phase_totals.items():
            by_phase[phase].update(searches=values['searches'], known_nodes=values['nodes'],
                                   searches_without_nodes=values['missing_nodes'])
        check(dict(by_phase) == summary['phase_counts'], 'node total summary differs from replay')
        return {'label': summary['label'], 'engine_returncode': summary['engine_returncode'], 'searches': self.search_count,
                'threads_set': self.set_threads, 'resets': self.resets, 'readyoks': self.readies,
                'phase_totals': {f'{phase}/{thread}': values for (phase, thread), values in self.phase_totals.items()},
                'games': sum(self.outcomes.values()), 'game_plies': self.ply_count, 'game_ends': self.outcomes,
                'stops': len(self.duration),
                'go_to_stop_ns_range': (min(d[0] for d in self.duration), max(d[0] for d in self.duration)) if self.duration else None,
                'depth9_mismatches': self.d9_mismatch}


def audit(directory, fens, job19):
    summary = json.loads((directory / 'summary.json').read_text(encoding='ascii'))
    check(summary['fixture_sha256'] == FIXTURE_SHA
          and all(sha(directory / filename) == checksum for filename, checksum in summary['files_sha256'].items()),
          'fixture or raw artifact hash does not match summary')
    if not summary['workload_complete']:
        return {'label': summary['label'], 'status': 'incomplete', 'startup_complete': summary['startup_complete'],
                'stage': summary['stage'], 'error': summary['protocol_error'], 'engine_returncode': summary['engine_returncode'],
                'raw_bestmove_lines': sum(line.startswith(b'bestmove ') for line in (directory / 'engine.stdout.txt').read_bytes().splitlines()),
                'stderr_bytes': (directory / 'engine.stderr.txt').stat().st_size}
    arm = 'kF' if '-kF' in summary['label'] else 'r15d'
    baseline = job19 / 'W1' / arm
    start = lines(baseline / 'engine.commands.txt')
    run = Transcript(directory, start[:start.index('ucinewgame')])
    part = summary['part']
    if part == 't-clean':
        for thread_count, start in ((1, 1), (2, 31), (4, 61)):
            if thread_count != 1:
                run.threads(thread_count)
            run.reset()
            for index in range(start, start + 30):
                timed = index % 5 == 0
                run.search(fens, index, thread_count, 'go infinite' if timed else 'go nodes 50000',
                           't-infinite' if timed else 't-nodes')
        run.threads(1)
        run.play(fens, range(211, 215), 't-games')
    elif part == 'au-d9':
        baseline_rows = tsv(baseline / 'rows.tsv')
        for index in range(1, 201):
            run.reset()
            row = run.search(fens, index, 1, 'go depth 9', 'au-d9')
            expected = baseline_rows[index - 1]
            check(expected['row'] == str(index) and expected['fen'] == row['fen'], 'wrong baseline row')
            if (row['nodes'], row['bestmove']) != (expected['nodes'], expected['bestmove']):
                run.d9_mismatch.append({'row': index, 'reference_nodes': expected['nodes'], 'nodes': row['nodes'],
                                       'reference_bestmove': expected['bestmove'], 'bestmove': row['bestmove']})
    elif part == 'au-games':
        run.play(fens, range(201, 211), 'au-games')
    else:
        raise ValueError('only clean runs are in scope')
    return run.finish(summary)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--job19', required=True, type=Path)
    parser.add_argument('runs', nargs='+', type=Path)
    args = parser.parse_args()
    check(chess.__version__ == '1.11.2', 'mismatched python-chess')
    fixture = args.job19 / 'positions.txt'
    check(sha(fixture) == FIXTURE_SHA, 'wrong Job 19 fixture')
    fens = lines(fixture)
    print(json.dumps([audit(path, fens, args.job19) for path in args.runs], indent=2))
