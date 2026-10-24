#!/usr/bin/env python3
"""Original serial, cold-position WAC300 UCI runner; never reports Elo."""
import argparse
import csv
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import subprocess
import sys
import time

import chess


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def corpus(path):
    result = []
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            raise ValueError(f'empty corpus line {number}')
        board = chess.Board()
        operations = board.set_epd(line)
        label = operations.get('id')
        if not isinstance(label, str) or not re.fullmatch(r'WAC\.\d{3}', label):
            raise ValueError(f'bad WAC id at line {number}: {label!r}')
        best = operations.get('bm')
        if not isinstance(best, list) or not best or not all(move in board.legal_moves for move in best):
            raise ValueError(f'bad/illegal best-move field at {label}')
        if not board.is_valid():
            raise ValueError(f'invalid chess position at {label}: {board.status()}')
        result.append({'id': label, 'fen': board.fen(), 'bm_uci': [move.uci() for move in best],
                       'bm_san': [board.san(move) for move in best]})
    if len(result) != 300 or {row['id'] for row in result} != {f'WAC.{i:03d}' for i in range(1, 301)}:
        raise ValueError('corpus must contain exactly the complete 300 unique WAC IDs')
    return result


class Engine:
    def __init__(self, exe, cpu, out, name):
        self.directory = out / name
        self.directory.mkdir()
        self.events = (self.directory / 'events.jsonl').open('w', buffering=1)
        self.input = (self.directory / 'stdin.txt').open('w', buffering=1)
        self.stdout = (self.directory / 'stdout.raw').open('wb', buffering=0)
        self.stderr = (self.directory / 'stderr.raw').open('wb', buffering=0)
        self.command = ['taskset', '-c', str(cpu), str(exe)]
        self.process = subprocess.Popen(self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, bufsize=0)
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ, 'stdout')
        self.selector.register(self.process.stderr, selectors.EVENT_READ, 'stderr')
        self.pending = {'stdout': b'', 'stderr': b''}
        self.lines = []
        self.record('launch', {'command': self.command, 'pid': self.process.pid,
                               'affinity': sorted(os.sched_getaffinity(self.process.pid))})
        if os.sched_getaffinity(self.process.pid) != {cpu}:
            raise RuntimeError('child CPU affinity did not match the frozen CPU')

    def record(self, kind, value):
        self.events.write(json.dumps({'utc': utc(), 'monotonic': time.monotonic(),
                                      'kind': kind, 'value': value}) + '\n')

    def send(self, text):
        self.input.write(text + '\n')
        self.record('stdin', text)
        self.process.stdin.write((text + '\n').encode())
        self.process.stdin.flush()

    def until(self, predicate, seconds):
        deadline = time.monotonic() + seconds
        found = []
        while True:
            while self.lines:
                line = self.lines.pop(0)
                found.append(line)
                if predicate(line):
                    return found
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self.record('deadline', {'seconds': seconds, 'exit': self.process.poll()})
                raise TimeoutError(f'UCI deadline exceeded ({seconds}s)')
            if not self.selector.get_map():
                raise RuntimeError(f'engine closed output, exit={self.process.poll()}')
            for key, _ in self.selector.select(min(remaining, 0.5)):
                data = os.read(key.fd, 65536)
                stream = key.data
                if not data:
                    self.selector.unregister(key.fileobj)
                    if self.pending[stream]:
                        self.record(stream + '_partial', self.pending[stream].decode(errors='replace'))
                    continue
                (self.stdout if stream == 'stdout' else self.stderr).write(data)
                self.pending[stream] += data
                while b'\n' in self.pending[stream]:
                    raw, self.pending[stream] = self.pending[stream].split(b'\n', 1)
                    line = raw.rstrip(b'\r').decode('utf-8', errors='strict')
                    self.record(stream, line)
                    if stream == 'stdout':
                        self.lines.append(line)

    def close(self):
        try:
            if self.process.poll() is None:
                self.send('quit')
                deadline = time.monotonic() + 5
                while self.process.poll() is None and time.monotonic() < deadline:
                    try:
                        self.until(lambda line: False, 0.1)
                    except (TimeoutError, RuntimeError):
                        pass
                if self.process.poll() is None:
                    self.record('terminate_owned_child', self.process.pid)
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        self.record('kill_unresponsive_owned_child', self.process.pid)
                        self.process.kill()
                        self.process.wait(timeout=3)
            self.record('exit', self.process.wait(timeout=3))
            # Read through both EOFs after exit so the raw files also retain
            # final diagnostics emitted immediately before process shutdown.
            drain_deadline = time.monotonic() + 2
            while self.selector.get_map() and time.monotonic() < drain_deadline:
                try:
                    self.until(lambda line: False, 0.1)
                except (TimeoutError, RuntimeError):
                    pass
            return self.process.returncode
        finally:
            self.selector.close()
            for stream in (self.input, self.stdout, self.stderr, self.events):
                stream.close()


def run_pass(exe, active, name, positions, args, rows, writer, deadline):
    engine = Engine(exe, args.cpu, args.out, name)
    try:
        engine.send('uci')
        greeting = engine.until(lambda line: line == 'uciok', 10)
        for setting in ('Threads value 1', 'Hash value 16', 'OwnBook value false', 'Move Overhead value 10'):
            engine.send('setoption name ' + setting)
        if active:
            if 'option name NnueInt16 type check default false' not in greeting:
                raise RuntimeError('NnueInt16 option missing before activation')
            engine.send('setoption name NnueInt16 value true')
        engine.send('isready')
        ready = engine.until(lambda line: line == 'readyok', 10)
        if active and ('info string NnueInt16 active' not in ready or
                       'info string NnueInt16 unavailable; using float' in ready):
            raise RuntimeError('integer backend did not acknowledge actual activation')
        for position in positions:
            if time.monotonic() >= deadline:
                raise TimeoutError('whole-run deadline exceeded')
            engine.send('ucinewgame')
            engine.send('isready')
            engine.until(lambda line: line == 'readyok', 10)
            engine.send('position fen ' + position['fen'])
            engine.send('isready')
            position_reply = engine.until(lambda line: line == 'readyok', 10)
            position_errors = [line for line in position_reply if line.startswith(
                ('info string invalid FEN:', 'info string invalid position', 'info string illegal move '))]
            if position_errors:
                raise RuntimeError(f'engine rejected {position["id"]}: {position_errors}')
            if time.monotonic() >= deadline:
                raise TimeoutError('whole-run deadline exceeded before search')
            start = time.monotonic()
            engine.send(f'go movetime {args.movetime}')
            lines = engine.until(lambda line: line.startswith('bestmove '), args.search_timeout)
            elapsed = time.monotonic() - start
            if time.monotonic() >= deadline:
                raise TimeoutError('whole-run deadline exceeded during position')
            best_line = next(line for line in reversed(lines) if line.startswith('bestmove '))
            move_text = best_line.split()[1]
            board = chess.Board(position['fen'])
            move = chess.Move.from_uci(move_text)
            legal = move in board.legal_moves
            if not legal:
                raise RuntimeError(f'illegal bestmove at {position["id"]}: {move_text}')
            score_type = score = depth = ''
            for line in reversed(lines):
                match = re.search(r'\bscore (cp|mate) (-?\d+)', line)
                if match:
                    score_type, score = match.groups()
                    d = re.search(r'\bdepth (\d+)', line)
                    depth = d.group(1) if d else ''
                    break
            row = {'pass': name, 'id': position['id'], 'fen': position['fen'],
                   'bestmove': move_text, 'bestmove_san': board.san(move), 'legal': legal,
                   'bm_uci': ' '.join(position['bm_uci']), 'bm_san': ' '.join(position['bm_san']),
                   'matched': move_text in position['bm_uci'], 'score_type': score_type,
                   'score': score, 'depth': depth, 'wall_seconds': f'{elapsed:.6f}', 'watchdog_ok': True}
            rows.append(row)
            writer.writerow(row)
            engine.record('position_result', row)
            print(json.dumps({'pass': name, 'completed': len([r for r in rows if r['pass'] == name]),
                              'id': position['id'], 'matched': row['matched']}), flush=True)
    finally:
        code = engine.close()
    if code != 0:
        raise RuntimeError(f'engine exited abnormally ({code}) after {name}')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--corpus', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--a', type=Path)
    p.add_argument('--b', type=Path)
    p.add_argument('--a-receipt', type=Path)
    p.add_argument('--b-receipt', type=Path)
    p.add_argument('--b-int16', action='store_true')
    p.add_argument('--cpu', type=int, default=0)
    p.add_argument('--movetime', type=int, default=1000)
    p.add_argument('--search-timeout', type=float, default=5)
    p.add_argument('--whole-timeout', type=float, default=1200)
    p.add_argument('--validate-only', action='store_true')
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    positions = corpus(args.corpus)
    validation = {'utc': utc(), 'corpus': str(args.corpus), 'sha256': sha(args.corpus),
                  'positions': len(positions), 'complete_ids': True, 'all_bm_legal': True,
                  'all_boards_valid': True, 'python_chess': chess.__version__}
    (args.out / 'corpus-validation.json').write_text(json.dumps(validation, indent=2) + '\n')
    (args.out / 'positions.json').write_text(json.dumps(positions, indent=2) + '\n')
    print(json.dumps(validation), flush=True)
    if args.validate_only:
        return 0
    if not args.a or not args.b or not args.a_receipt or not args.b_receipt or args.movetime != 1000:
        raise ValueError('actual protocol requires --a, --b, both d11 receipts, --movetime 1000')
    receipts = {}
    for label, exe, path in (('a', args.a, args.a_receipt), ('b', args.b, args.b_receipt)):
        receipt = json.loads(path.read_text())
        d11_ok = receipt.get('d11') == 308972 or [11, 308972] in receipt.get('rows', [])
        if receipt.get('status') != 'PASS' or not d11_ok or receipt.get('engine_sha256') != sha(exe):
            raise ValueError(f'{label} d11 receipt is not a matching PASS')
        receipts[label] = {'path': str(path), 'sha256': sha(path), 'receipt': receipt}
    os.sched_setaffinity(0, {args.cpu})
    frozen = {'argv': sys.argv, 'utc': utc(), 'runner_pid': os.getpid(), 'cpu': args.cpu,
              'python': sys.executable, 'python_chess': chess.__version__,
              'parent_affinity': sorted(os.sched_getaffinity(0)),
              'runner_sha256': sha(__file__), 'corpus_sha256': sha(args.corpus),
              'a': {'path': str(args.a), 'sha256': sha(args.a)},
              'b': {'path': str(args.b), 'sha256': sha(args.b)},
              'b_int16': args.b_int16, 'order': ['OFF_A1', 'B_ON' if args.b_int16 else 'B_OFF', 'OFF_A2'],
              'd11_receipts': receipts,
              'settings': {'Threads': 1, 'Hash': 16, 'OwnBook': False, 'Move Overhead': 10,
                           'movetime_ms': 1000, 'ucinewgame_per_position': True},
              'search_deadline_seconds': args.search_timeout, 'whole_deadline_seconds': args.whole_timeout,
              'watchdog_note': '5-second search watchdog is not a 1-second game-forfeit threshold; requested movetime is 1000ms',
              'precondition': 'Root must qualify every binary d11=308972 with all options OFF before launch'}
    (args.out / 'frozen.json').write_text(json.dumps(frozen, indent=2) + '\n')
    rows = []
    deadline = time.monotonic() + args.whole_timeout
    names = frozen['order']
    with (args.out / 'positions.csv').open('w', newline='', buffering=1) as f:
        fields = ['pass', 'id', 'fen', 'bestmove', 'bestmove_san', 'legal', 'bm_uci', 'bm_san',
                  'matched', 'score_type', 'score', 'depth', 'wall_seconds', 'watchdog_ok']
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for exe, active, name in ((args.a, False, names[0]), (args.b, args.b_int16, names[1]),
                                  (args.a, False, names[2])):
            if time.monotonic() >= deadline:
                raise TimeoutError('whole-run deadline exceeded before pass')
            run_pass(exe, active, name, positions, args, rows, writer, deadline)
    summary = {'result': 'PASS', 'utc': utc(), 'rows': len(rows), 'elo_claim': None,
               'passes': {name: {'positions': sum(r['pass'] == name for r in rows),
                                 'matched': sum(r['pass'] == name and r['matched'] for r in rows),
                                 'legal': sum(r['pass'] == name and r['legal'] for r in rows)} for name in names}}
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary), flush=True)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        failure = {'result': 'FAIL', 'error': str(error), 'utc': utc()}
        if '--out' in sys.argv:
            failure_directory = Path(sys.argv[sys.argv.index('--out') + 1])
            if failure_directory.is_dir():
                (failure_directory / 'FAILURE.json').write_text(json.dumps(failure, indent=2) + '\n')
        print(json.dumps(failure), file=sys.stderr, flush=True)
        raise
