#!/usr/bin/env python3
"""Capture raw UCI and exit status for Job 22 controls and checker workloads."""

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import selectors
import signal
import subprocess
import time

import chess

import identity


FIXTURE_SHA = '3c1b17332eca46a912f572eae8197324f466a8e2f909653104c427457ffb0521'
HELPER_SHA = '4a51fe258b610b32055cc7e42614640d9dd0abb8988fdb304d1ad31f7fbcef61'
PYTHON_CHESS = '1.11.2'
PARTS = ('au-d9', 'au-games', 't-control', 't-clean')
ROW_FIELDS = ('search', 'phase', 'threads', 'w1_position', 'ply', 'fen', 'nodes', 'nodes_source',
              'depth', 'bestmove', 'last_info_line', 'bestmove_line')
GAME_FIELDS = ('phase', 'threads', 'w1_position', 'plies', 'nodes', 'termination', 'result', 'moves')
INFINITE_FIELDS = ('w1_position', 'threads', 'go_monotonic_ns', 'scheduled_stop_monotonic_ns',
                   'stop_monotonic_ns', 'go_to_stop_ns')
NET_LINE = re.compile(rb'\bhidden 768\b.*\bchecksum 30ab43b4ba5db5f3\b')
INFO_NODES = re.compile(rb'\bnodes ([0-9]+)\b')
INFO_DEPTH = re.compile(rb'info depth ([0-9]+)\b')
SOFT_NODES = re.compile(rb'info string softnodes nodes ([0-9]+)')
ENV_KEYS = ('ASAN_OPTIONS', 'UBSAN_OPTIONS', 'TSAN_OPTIONS')


def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def decode(line):
    return line.decode('ascii', errors='backslashreplace')


def fixture_fens(path):
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != FIXTURE_SHA or b'\r' in content or not content.endswith(b'\n'):
        raise ValueError('wrong Job19 W1 fixture or line endings')
    lines = content.decode('ascii').splitlines()
    if len(lines) != 1000:
        raise ValueError('expected exactly 1,000 fixture rows')
    return lines


class Session:
    def __init__(self, argv, stdout, stderr, commands, timeout):
        self.argv = argv
        self.stdout = stdout
        self.stderr = stderr
        self.commands = commands
        self.timeout_ns = round(timeout * 1_000_000_000)
        self.process = None
        self.selector = None
        self.pending = bytearray()
        self.eof = False
        self.in_search = False
        self.interventions = []
        self.failed_command = None

    def launch(self):
        self.process = subprocess.Popen(self.argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr)
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)

    def send(self, line):
        payload = line.encode('ascii') + b'\n'
        self.commands.write(payload)
        self.commands.flush()
        try:
            before_write = time.monotonic_ns()
            self.process.stdin.write(payload)
            self.process.stdin.flush()
        except OSError:
            if self.failed_command is None:
                self.failed_command = line
            raise
        return before_write

    def read_chunk(self, deadline):
        wait_ns = deadline - time.monotonic_ns()
        if wait_ns <= 0 or not self.selector.select(wait_ns / 1_000_000_000):
            return False
        data = os.read(self.process.stdout.fileno(), 65536)
        if not data:
            self.eof = True
            return False
        self.stdout.write(data)
        self.stdout.flush()
        self.pending.extend(data)
        return True

    def receive(self, done, label, deadline=None):
        timed_poll = deadline is not None
        if deadline is None:
            deadline = time.monotonic_ns() + self.timeout_ns
        lines = []
        while not timed_poll or time.monotonic_ns() < deadline:
            newline = self.pending.find(b'\n')
            if newline < 0:
                if self.read_chunk(deadline):
                    continue
                if self.eof:
                    raise RuntimeError(f'engine stdout closed before {label}')
                if not timed_poll:
                    raise RuntimeError(f'timed out waiting for {label}')
                continue
            line = bytes(self.pending[:newline]).rstrip(b'\r')
            del self.pending[:newline + 1]
            identity.check_refusal(line)
            lines.append(line)
            if done(line):
                return lines, True
        return lines, False

    def ready(self):
        self.send('isready')
        return self.receive(lambda line: line == b'readyok', 'readyok')[0]

    def setup(self, net, options):
        self.send('uci')
        hello, _ = self.receive(lambda line: line == b'uciok', 'uciok')
        advertised = {decode(match[1]) for line in hello if (match := identity.OPTION.match(line))}
        if missing := (options.keys() | {'NNUEArchFile', 'NNUEArch'}) - advertised:
            raise RuntimeError(f'missing requested UCI options: {sorted(missing)}')
        for name, value in options.items():
            self.send(f'setoption name {name} value {value}')
        self.send(f'setoption name NNUEArchFile value {net}')
        self.send('setoption name NNUEArch value true')
        ready = self.ready()
        active = [line for line in ready if line.startswith(identity.NET_ACTIVE)]
        if len(active) != 1 or NET_LINE.search(active[0]) is None:
            raise RuntimeError(f'expected one active net768 checksum line, got {active!r}')
        return decode(active[0])

    def reset(self):
        self.send('ucinewgame')
        if self.ready() != [b'readyok']:
            raise RuntimeError('unexpected output at newgame ready barrier')

    def search(self, go, on_stop=None):
        self.in_search = True
        started = self.send(go)

        def bestmove(line):
            return line.startswith(b'bestmove ')

        lines = []
        if go == 'go infinite':
            due = started + 100_000_000
            lines, finished = self.receive(bestmove, '100 ms infinite-search window', deadline=due)
            if finished:
                raise RuntimeError('bestmove received during go infinite before stop')
            sent_stop = self.send('stop')
            on_stop(started, due, sent_stop)
        remainder, _ = self.receive(bestmove, 'bestmove')
        self.in_search = False
        return lines + remainder

    def close(self, failed):
        if self.process is None:
            return None
        try:
            if self.eof and self.process.poll() is None:
                try:
                    self.process.wait(timeout=0.25)
                except subprocess.TimeoutExpired:
                    pass
            if self.process.poll() is None:
                try:
                    if failed and self.in_search and not self.eof:
                        self.interventions.append('sent stop during shutdown of incomplete search')
                        self.send('stop')
                    self.send('quit')
                except BrokenPipeError:
                    pass
            for sig, label in ((None, 'quit'), (signal.SIGTERM, 'SIGTERM'), (signal.SIGKILL, 'SIGKILL')):
                if self.process.poll() is None and sig is not None:
                    self.interventions.append(f'sent {label} after shutdown timeout')
                    self.process.send_signal(sig)
                deadline = time.monotonic_ns() + 3_000_000_000
                while self.selector is not None and not self.eof and self.read_chunk(deadline):
                    pass
                try:
                    return self.process.wait(timeout=0.25)
                except subprocess.TimeoutExpired:
                    continue
            return self.process.wait()
        finally:
            if self.selector is not None:
                self.selector.close()
            self.process.stdout.close()
            try:
                self.process.stdin.close()
            except BrokenPipeError:
                pass


def parse_search(lines, go):
    best = identity.BESTMOVE.fullmatch(lines[-1])
    if best is None:
        raise ValueError(f'malformed bestmove: {lines[-1]!r}')
    last = next((line for line in reversed(lines[:-1]) if line.startswith(b'info depth ')), b'')
    last_nodes = INFO_NODES.search(last)
    depth = INFO_DEPTH.match(last)
    if last and (last_nodes is None or depth is None):
        raise ValueError(f'malformed last depth info: {last!r}')
    if go == 'go softnodes 2000':
        finals = [line for line in lines[:-1] if line.startswith(b'info string softnodes nodes')]
        final = SOFT_NODES.fullmatch(finals[0]) if len(finals) == 1 else None
        if final is None:
            raise ValueError('expected one exact final softnodes marker')
        value, source = int(final[1]), 'final_softnodes'
    elif last_nodes is not None:
        value, source = int(last_nodes[1]), 'last_info'
    else:
        value, source = '', 'no_node_info'
    return {
        'nodes': value, 'nodes_source': source, 'depth': int(depth[1]) if depth is not None else '',
        'bestmove': decode(best[1]), 'last_info_line': decode(last), 'bestmove_line': decode(lines[-1]),
    }


class Workload:
    def __init__(self, session, fens, rows, games, timing):
        self.session = session
        self.fens = fens
        self.rows = rows
        self.games = games
        self.timing = timing
        self.stage = 'startup'
        self.counts = {}
        self.searches = 0
        self.completed_games = 0

    def search(self, phase, threads, index, fen, go, ply='', game_moves=None):
        self.stage = f'{phase} W1 position {index}' + (f' ply {ply}' if ply != '' else '')
        root = self.fens[index - 1]
        position = f'position fen {root}'
        if game_moves is not None:
            position += ' moves' + ''.join(f' {move}' for move in game_moves)
        self.session.send(position)

        def stop_receipt(start, target, actual):
            self.timing.writerow(dict(zip(INFINITE_FIELDS, (index, threads, start, target, actual, actual - start), strict=True)))

        result = parse_search(self.session.search(go, on_stop=stop_receipt), go)
        self.searches += 1
        self.rows.writerow({'search': self.searches, 'phase': phase, 'threads': threads,
                            'w1_position': index, 'ply': ply, 'fen': fen, **result})
        cell = self.counts.setdefault(phase, {'searches': 0, 'known_nodes': 0, 'searches_without_nodes': 0})
        cell['searches'] += 1
        if result['nodes'] == '':
            cell['searches_without_nodes'] += 1
        else:
            cell['known_nodes'] += result['nodes']
        return result

    def fixed(self, phase, threads, low, high, go, reset_each=False, every_fifth_infinite=False):
        self.stage = f'{phase} reset before W1 position {low}'
        if not reset_each:
            self.session.reset()
        for index in range(low, high + 1):
            if reset_each:
                self.stage = f'{phase} reset before W1 position {index}'
                self.session.reset()
            action = 'go infinite' if every_fifth_infinite and index % 5 == 0 else go
            self.search('t-infinite' if action == 'go infinite' else phase,
                        threads, index, self.fens[index - 1], action)

    def play(self, phase, low, high):
        for index in range(low, high + 1):
            self.stage = f'{phase} newgame from W1 position {index}'
            self.session.reset()
            board = chess.Board(self.fens[index - 1])
            if not board.is_valid():
                raise ValueError(f'invalid game start at W1 position {index}')
            moves = []
            nodes = 0
            while len(moves) < 200 and not board.is_game_over(claim_draw=True):
                result = self.search(phase, 1, index, board.fen(), 'go softnodes 2000', len(moves) + 1, moves)
                move = board.parse_uci(result['bestmove'])
                if not move:
                    raise ValueError('null bestmove at a playable root')
                nodes += result['nodes']
                moves.append(result['bestmove'])
                board.push(move)
            outcome = board.outcome(claim_draw=True)
            self.games.writerow({'phase': phase, 'threads': 1, 'w1_position': index, 'plies': len(moves),
                                 'nodes': nodes, 'termination': outcome.termination.name if outcome else 'PLY_CAP',
                                 'result': outcome.result() if outcome else '*', 'moves': ' '.join(moves)})
            self.completed_games += 1

    def run(self, part, count, control_position):
        if part == 'au-d9':
            self.fixed('au-d9', 1, 1, count, 'go depth 9', reset_each=True)
        elif part == 'au-games':
            self.play('au-games', 201, 210)
        elif part == 't-control':
            first, last = (control_position, control_position) if control_position else (1, 5)
            self.fixed('t-control', 2, first, last, 'go nodes 50000')
        else:
            for threads, first in ((1, 1), (2, 31), (4, 61)):
                if threads != 1:
                    self.stage = f'setting Threads {threads}'
                    self.session.send(f'setoption name Threads value {threads}')
                self.fixed('t-nodes', threads, first, first + 29, 'go nodes 50000', every_fifth_infinite=True)
            self.stage = 'restoring Threads 1 before games'
            self.session.send('setoption name Threads value 1')
            self.play('t-games', 211, 214)
        self.stage = 'complete'


def tsv(stream, fields):
    writer = csv.DictWriter(stream, fieldnames=fields, delimiter='\t', lineterminator='\n')
    writer.writeheader()
    return writer


def run(args):
    if chess.__version__ != PYTHON_CHESS:
        raise ValueError(f'expected python-chess module {PYTHON_CHESS}; got {chess.__version__}')
    if not 0 < args.timeout <= 300:
        raise ValueError('timeout must be positive and at most 300 seconds')
    if args.count is not None and args.part != 'au-d9':
        raise ValueError('--count applies to au-d9 only')
    if args.control_position is not None and args.part != 't-control':
        raise ValueError('--control-position applies to T controls only')
    if args.setarch_r and not args.part.startswith('t-'):
        raise ValueError('--setarch-r applies to T runs only')
    executable, fixture, net = (path.resolve(strict=True) for path in (args.engine, args.fixture, args.net))
    if digest(executable) != args.exe_sha256 or digest(net) != identity.NET_SHA or digest(Path(identity.__file__)) != HELPER_SHA:
        raise ValueError('engine, net or identity helper SHA-256 mismatch')
    if any(char in str(net) for char in '\r\n'):
        raise ValueError('invalid multiline net path')
    fens = fixture_fens(fixture)
    count = (args.count or 200) if args.part == 'au-d9' else None
    options = {**identity.PC20, 'Threads': 2 if args.part == 't-control' else 1}
    argv = ['setarch', platform.machine(), '-R', str(executable)] if args.setarch_r else [str(executable)]
    output = args.output
    output.mkdir(parents=True, exist_ok=False)
    started = utc()
    error = None
    close_error = None
    active = None
    returncode = None
    with ((output / 'engine.stdout.txt').open('xb') as stdout,
          (output / 'engine.stderr.txt').open('xb') as stderr,
          (output / 'engine.commands.txt').open('xb') as commands,
          (output / 'rows.tsv').open('x', encoding='ascii', newline='', buffering=1) as rows,
          (output / 'games.tsv').open('x', encoding='ascii', newline='', buffering=1) as games,
          (output / 'infinite.tsv').open('x', encoding='ascii', newline='', buffering=1) as timing):
        child = Session(argv, stdout, stderr, commands, args.timeout)
        work = Workload(child, fens, tsv(rows, ROW_FIELDS), tsv(games, GAME_FIELDS), tsv(timing, INFINITE_FIELDS))
        try:
            child.launch()
            active = child.setup(net, options)
            work.run(args.part, count, args.control_position)
        except (OSError, RuntimeError, ValueError, KeyboardInterrupt) as err:
            error = f'{type(err).__name__}: {err}'
        finally:
            try:
                returncode = child.close(error is not None)
            except (OSError, RuntimeError, ValueError, KeyboardInterrupt) as err:
                close_error = f'{type(err).__name__}: {err}'
                if child.process is not None:
                    returncode = child.process.poll()
    with (output / 'engine.stdout.txt').open('rb') as raw_stdout:
        raw_bestmoves = sum(line.startswith(b'bestmove ') for line in raw_stdout)
    summary = {
         'label': args.label, 'part': args.part, 'control_position': args.control_position, 'argv': argv, 'engine_sha256': args.exe_sha256,
        'net_sha256': identity.NET_SHA, 'fixture_sha256': FIXTURE_SHA, 'identity_helper_sha256': HELPER_SHA,
        'runner_sha256': digest(Path(__file__)), 'python_chess': PYTHON_CHESS, 'initial_uci_options': options,
        'net_active': active, 'net_path': str(net), 'startup_complete': active is not None,
        'sanitizer_environment': {name: os.environ[name] for name in ENV_KEYS if name in os.environ},
        'engine_returncode': returncode, 'workload_complete': work.stage == 'complete', 'stage': work.stage,
        'protocol_error': error, 'shutdown_error': close_error, 'shutdown_interventions': child.interventions,
        'failed_command_write': child.failed_command, 'completed_searches': work.searches,
        'raw_bestmove_lines': raw_bestmoves,
        'completed_games': work.completed_games, 'phase_counts': work.counts, 'au_d9_requested_rows': count,
        'started_utc': started, 'finished_utc': utc(),
        'files_sha256': {path.name: digest(path) for path in sorted(output.iterdir())},
    }
    encoded = json.dumps(summary, indent=2) + '\n'
    with (output / 'summary.json').open('x', encoding='ascii') as report:
        report.write(encoded)
    print(encoded, end='', flush=True)
    if returncode not in (None, 0):
        return returncode if returncode > 0 else 128 - returncode
    return int(returncode is None or error is not None or close_error is not None)


def terminate(signum, frame):
    raise InterruptedError('run interrupted by SIGTERM')


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--part', choices=PARTS, required=True)
    cli.add_argument('--label', required=True)
    cli.add_argument('--exe-sha256', required=True)
    for option in ('engine', 'net', 'fixture', 'output'):
        cli.add_argument('--' + option, type=Path, required=True)
    cli.add_argument('--count', choices=(1, 200), type=int)
    cli.add_argument('--setarch-r', action='store_true')
    cli.add_argument('--control-position', type=int, choices=range(1, 6))
    cli.add_argument('--timeout', default=60.0, type=float)
    args = cli.parse_args()
    signal.signal(signal.SIGTERM, terminate)
    try:
        return run(args)
    except (OSError, ValueError) as err:
        cli.exit(1, f'{err}\n')


if __name__ == '__main__':
    raise SystemExit(main())
