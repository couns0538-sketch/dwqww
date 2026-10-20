#!/usr/bin/env python3
"""Full-engine UCI TT concurrency/lifecycle evidence; stdlib plus optional python-chess.

All lifecycle mutations follow stop/bestmove/isready. No concurrent external TT
mutation is attempted. This is correctness/sanitizer evidence, not a speed test.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import sys
import threading
import time

try:
    import chess
except ImportError:
    chess = None

POSITIONS = [
    'startpos',
    'fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1',
    'fen 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1',
]
TERMINALS = [
    ('mate', 'fen 7k/6Q1/6K1/8/8/8/8/8 b - - 0 1', 'mate 0'),
    ('stalemate', 'fen 7k/5Q2/6K1/8/8/8/8/8 b - - 0 1', 'cp 0'),
    ('draw-with-legal-moves', 'fen 7k/8/8/8/8/8/8/K7 w - - 0 1', 'cp 0'),
]


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')


class Evidence:
    def __init__(self, directory):
        self.file = (directory / 'events.jsonl').open('x', encoding='utf-8')
        self.lock = threading.Lock()
        self.sequence = 0
        self.closed = False

    def record(self, kind, **data):
        with self.lock:
            if self.closed:
                return
            self.sequence += 1
            event = dict(sequence=self.sequence, monotonic_ns=time.monotonic_ns(),
                         wall_ns=time.time_ns(), kind=kind, **data)
            self.file.write(json.dumps(event, sort_keys=True) + '\n')
            self.file.flush()

    def close(self):
        with self.lock:
            self.closed = True
            self.file.close()


class Engine:
    def __init__(self, args, evidence, index, result):
        self.args, self.evidence, self.index, self.result = args, evidence, index, result
        self.active = False
        self.lines = queue.Queue()
        self.directory = args.output / f'process-{index:02d}'
        self.directory.mkdir()
        self.raw = {name: (self.directory / (name + '.bin')).open('xb')
                    for name in ('stdin', 'stdout', 'stderr')}
        self.process = subprocess.Popen(
            [str(args.engine), *args.engine_arg], cwd=args.cwd, env=args.environment,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            bufsize=0)
        result.update(pid=self.process.pid, argv=[str(args.engine), *args.engine_arg],
                      cwd=str(args.cwd), searches=[], completed=False, cleanup=[], reader_errors=[])
        evidence.record('spawn', process=index, pid=self.process.pid, argv=result['argv'], cwd=result['cwd'])
        self.readers = [threading.Thread(target=self.read, args=(name,), daemon=True)
                        for name in ('stdout', 'stderr')]
        for reader in self.readers:
            reader.start()

    def record(self, kind, **data):
        self.evidence.record(kind, process=self.index, **data)

    def read(self, name):
        pipe = getattr(self.process, name)
        pending = b''
        try:
            while True:
                chunk = os.read(pipe.fileno(), 4096)
                observed_ns, observed_wall_ns = time.monotonic_ns(), time.time_ns()
                if not chunk:
                    break
                self.raw[name].write(chunk)
                self.raw[name].flush()
                self.record('bytes', stream=name, base64=base64.b64encode(chunk).decode('ascii'),
                            observed_monotonic_ns=observed_ns, observed_wall_ns=observed_wall_ns)
                if name == 'stdout':
                    pending += chunk
                    while b'\n' in pending:
                        line, pending = pending.split(b'\n', 1)
                        self.lines.put(line.rstrip(b'\r').decode('utf-8', errors='replace'))
            if name == 'stdout' and pending:
                self.lines.put(pending.rstrip(b'\r').decode('utf-8', errors='replace'))
        except BaseException as error:
            self.result['reader_errors'].append(name + ': ' + repr(error))
            self.record('reader_error', stream=name, error=repr(error))
        finally:
            self.record('eof', stream=name)
            if name == 'stdout':
                self.lines.put(None)

    def send(self, command):
        if self.active and command not in ('stop', 'isready', 'quit'):
            raise AssertionError('unsupported lifecycle mutation during search: ' + command)
        payload = (command + '\n').encode('ascii')
        written = 0
        self.record('command', text=command)
        while written < len(payload):
            count = os.write(self.process.stdin.fileno(), payload[written:])
            observed_ns, observed_wall_ns = time.monotonic_ns(), time.time_ns()
            if count <= 0:
                raise RuntimeError('engine input pipe did not accept bytes')
            chunk = payload[written:written + count]
            self.raw['stdin'].write(chunk)
            self.raw['stdin'].flush()
            self.record('bytes', stream='stdin', base64=base64.b64encode(chunk).decode('ascii'),
                        observed_monotonic_ns=observed_ns, observed_wall_ns=observed_wall_ns)
            written += count

    def until(self, predicate, timeout, purpose, accept_bestmove=False):
        deadline = time.monotonic() + timeout
        seen = []
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('absolute UCI deadline exceeded: ' + purpose)
            try:
                line = self.lines.get(timeout=remaining)
            except queue.Empty as error:
                raise TimeoutError('absolute UCI deadline exceeded: ' + purpose) from error
            if line is None:
                raise RuntimeError('engine stdout EOF before ' + purpose)
            self.record('line', text=line, purpose=purpose)
            if line.startswith('bestmove ') and not accept_bestmove:
                raise AssertionError('unexpected bestmove outside its search: ' + line)
            seen.append(line)
            if predicate(line):
                return seen

    def ready(self):
        self.send('isready')
        self.until(lambda line: line == 'readyok', self.args.handshake_timeout, 'readyok')

    def quiesce(self):
        if self.active:
            raise AssertionError('quiesce requires bestmove to have been received')
        self.send('stop')
        self.ready()  # stop joins; isready is the subsequent UCI processing barrier.

    def option(self, name, value=None):
        self.quiesce()
        self.send('setoption name ' + name + ('' if value is None else ' value ' + str(value)))
        self.ready()

    def handshake(self):
        self.send('uci')
        lines = self.until(lambda line: line == 'uciok', self.args.handshake_timeout, 'uciok')
        self.result['identification'] = lines
        for name in ('Threads', 'Hash', 'OwnBook', 'Clear Hash'):
            if not any(line.startswith('option name ' + name + ' type ') for line in lines):
                raise AssertionError('engine does not advertise required option ' + name)
        for name, value in [('OwnBook', 'false'), ('Ponder', 'false'), ('Hash', 1), ('Threads', 4)]:
            self.option(name, value)

    def search(self, label, position, stop=False, terminal=None):
        self.quiesce()
        self.send('position ' + position)
        self.ready()
        nodes = self.args.stop_nodes if stop else self.args.nodes
        item = dict(label=label, position=position, nodes_limit=nodes, stopped=stop,
                    start_monotonic_ns=time.monotonic_ns(), completed=False)
        self.result['searches'].append(item)
        self.record('search_start', **item)
        self.send('go nodes ' + str(nodes))
        self.active = True
        lines = []
        if stop:
            lines = self.until(lambda line: bool(re.match(r'^info depth .*\bnodes [1-9][0-9]*\b', line)),
                               self.args.search_timeout, label + ': positive-node info')
            self.send('stop')
        lines += self.until(lambda line: line.startswith('bestmove '),
                            self.args.stop_timeout if stop else self.args.search_timeout,
                            label + ': bestmove', accept_bestmove=True)
        self.active = False
        item['finish_monotonic_ns'] = time.monotonic_ns()
        item['bestmove_line'] = lines[-1]
        item['info'] = [line for line in lines if line.startswith('info ')]
        fields = lines[-1].split()
        if len(fields) not in (2, 4) or (len(fields) == 4 and fields[2] != 'ponder'):
            raise AssertionError('malformed bestmove record: ' + lines[-1])
        move = fields[1]
        if not re.fullmatch(r'0000|[a-h][1-8][a-h][1-8][qrbn]?', move):
            raise AssertionError('malformed bestmove: ' + move)
        is_no_move = terminal in ('mate', 'stalemate')
        if (move == '0000') != is_no_move:
            raise AssertionError('incorrect terminal bestmove for ' + label + ': ' + move)
        if chess is not None:
            board = chess.Board() if position == 'startpos' else chess.Board(position.removeprefix('fen '))
            if move == '0000':
                if any(board.legal_moves):
                    raise AssertionError('null bestmove while legal moves exist')
            elif chess.Move.from_uci(move) not in board.legal_moves:
                raise AssertionError('illegal bestmove for ' + label + ': ' + move)
            item['legality'] = 'checked_with_python_chess'
        else:
            item['legality'] = 'skipped_python_chess_unavailable; syntax_and_terminal_contract_only'
        structured = []
        for line in item['info']:
            if not line.startswith('info depth '):
                continue
            node = re.search(r'\bnodes ([0-9]+)\b', line)
            fullness = re.search(r'\bhashfull ([0-9]+)\b', line)
            if node and fullness:
                if not 0 <= int(fullness[1]) <= 1000:
                    raise AssertionError('hashfull outside UCI per-mille range')
                structured.append(dict(nodes=int(node[1]), hashfull=int(fullness[1])))
        if not structured:
            raise AssertionError('no structured info with nodes/hashfull for ' + label)
        item['node_hashfull_samples'] = structured
        if terminal:
            expected = next(score for name, _, score in TERMINALS if name == terminal)
            if not any('score ' + expected in line for line in item['info']):
                raise AssertionError('missing expected terminal score ' + expected)
        item['completed'] = True
        self.record('search_complete', label=label, bestmove=move, samples=len(structured))
        self.quiesce()

    def workload(self):
        self.handshake()
        for cycle in range(self.args.cycles):
            for index, position in enumerate(POSITIONS):
                self.search(f'cycle-{cycle}/threads4-hash1-position-{index}', position)
            self.search(f'cycle-{cycle}/stop-join', POSITIONS[1], stop=True)
            self.option('Clear Hash')
            self.search(f'cycle-{cycle}/after-clear', POSITIONS[1])
            self.option('Hash', 4)
            self.option('Threads', 2)
            self.search(f'cycle-{cycle}/threads2-hash4', POSITIONS[2])
            self.option('Hash', 1)
            self.option('Threads', 1)
            self.search(f'cycle-{cycle}/threads1-hash1', POSITIONS[0])
            self.option('Threads', 4)
            self.quiesce()
            self.send('ucinewgame')
            self.ready()
            self.search(f'cycle-{cycle}/newgame-threads4-hash1', POSITIONS[1])
        for label, position, _ in TERMINALS:
            self.search(label, position, terminal=label)
        self.result['completed'] = True

    def shutdown(self):
        if self.process.poll() is None:
            for command in ('stop', 'quit'):
                try:
                    self.send(command)
                    self.result['cleanup'].append('sent ' + command)
                except (OSError, ValueError) as error:
                    self.result['cleanup'].append(repr(error))
                    break
            try:
                self.process.wait(timeout=self.args.quit_timeout)
            except subprocess.TimeoutExpired:
                self.record('forced_kill', reason='quit deadline exceeded')
                self.result['cleanup'].append('quit deadline exceeded; killed')
                self.process.kill()
                self.process.wait(timeout=self.args.quit_timeout)
        else:
            self.process.wait()
        for reader in self.readers:
            reader.join(timeout=self.args.quit_timeout)
        self.result['reader_threads_joined'] = all(not reader.is_alive() for reader in self.readers)
        self.result['capture_complete'] = self.result['reader_threads_joined'] and not self.result['reader_errors']
        self.result['exit_code'] = self.process.returncode
        self.result['signal'] = -self.process.returncode if self.process.returncode < 0 else None
        self.record('exit', exit_code=self.process.returncode)
        if self.result['reader_threads_joined']:
            for stream in self.raw.values():
                stream.close()
            for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
                stream.close()
        else:
            # Never close a file under a live producer. The run fails, hashes
            # are explicitly provisional, and process teardown reclaims them.
            self.result['cleanup'].append('unjoined readers; capture incomplete; streams not closed under producers')
        stderr = (self.directory / 'stderr.bin').read_bytes()
        if b'ThreadSanitizer: data race' in stderr:
            classification = 'tsan_data_race'
        elif b'ThreadSanitizer' in stderr:
            classification = 'tsan_runtime_failure'
        elif re.search(rb'(AddressSanitizer|UndefinedBehaviorSanitizer|runtime error:)', stderr):
            classification = 'other_sanitizer_report'
        else:
            classification = 'none'
        self.result['sanitizer_classification'] = classification
        self.result['stream_sha256'] = {name: digest(self.directory / (name + '.bin')) for name in self.raw}
        self.result['stream_hashes_final'] = self.result['reader_threads_joined']
        save_json(self.directory / 'result.json', self.result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', type=Path, required=True)
    parser.add_argument('--engine-arg', action='append', default=[])
    parser.add_argument('--output', type=Path, required=True, help='must not already exist')
    parser.add_argument('--cwd', type=Path)
    parser.add_argument('--nodes', type=int, default=50000)
    parser.add_argument('--stop-nodes', type=int, default=1000000000)
    parser.add_argument('--cycles', type=int, default=2)
    parser.add_argument('--restarts', type=int, default=2, help='number of independent engine processes')
    parser.add_argument('--handshake-timeout', type=float, default=60)
    parser.add_argument('--search-timeout', type=float, default=120)
    parser.add_argument('--stop-timeout', type=float, default=30)
    parser.add_argument('--quit-timeout', type=float, default=30)
    parser.add_argument('--tsan-options', help='explicit child TSAN_OPTIONS; default inherits existing value')
    parser.add_argument('--allow-tsan-exit66', action='store_true', help='accept actual data-race exit66 as expected partial evidence, never as a pass')
    args = parser.parse_args()
    if min(args.nodes, args.stop_nodes, args.cycles, args.restarts) <= 0:
        parser.error('node limits, cycles and restarts must be positive')
    if min(args.handshake_timeout, args.search_timeout, args.stop_timeout, args.quit_timeout) <= 0:
        parser.error('all deadlines must be positive')
    args.engine = args.engine.resolve(strict=True)
    args.cwd = (args.cwd or args.engine.parent).resolve(strict=True)
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    args.environment = os.environ.copy()
    if args.tsan_options is not None:
        args.environment['TSAN_OPTIONS'] = args.tsan_options
    evidence = Evidence(args.output)
    configuration = {key: (str(value) if isinstance(value, Path) else value)
                     for key, value in vars(args).items() if key != 'environment'}
    configuration['effective_tsan_options'] = args.environment.get('TSAN_OPTIONS')
    configuration['positions'] = POSITIONS
    configuration['terminal_cases'] = TERMINALS
    configuration['driver_sha256'] = digest(Path(__file__))
    configuration['python'] = dict(executable=sys.executable, version=sys.version)
    save_json(args.output / 'configuration.json', configuration)
    summary = dict(status='running', completed_all_scenarios=False, sessions=[],
                   engine_sha256_before=digest(args.engine),
                   legal_validation=dict(available=chess is not None,
                                         module='python-chess',
                                         version=getattr(chess, '__version__', None)),
                   configuration_sha256=digest(args.output / 'configuration.json'))
    error = None
    try:
        for index in range(args.restarts):
            result = dict(index=index)
            summary['sessions'].append(result)
            engine = None
            try:
                engine = Engine(args, evidence, index, result)
                engine.workload()
            finally:
                if engine is not None:
                    engine.shutdown()
            if result['exit_code'] != 0:
                raise RuntimeError('engine exited ' + str(result['exit_code']))
            if not result['capture_complete'] or any('deadline exceeded' in x for x in result['cleanup']):
                raise RuntimeError('engine cleanup was not clean')
            if result['sanitizer_classification'] != 'none':
                raise RuntimeError('sanitizer report: ' + result['sanitizer_classification'])
        summary.update(status='passed', completed_all_scenarios=True)
    except BaseException as failure:
        error = failure
        summary.update(status='failed', error=repr(failure))
        if summary['sessions']:
            last = summary['sessions'][-1]
            if args.allow_tsan_exit66 and last.get('capture_complete') and last.get('exit_code') == 66 and last.get('sanitizer_classification') == 'tsan_data_race':
                summary['status'] = 'expected_tsan_race'
    finally:
        summary['engine_sha256_after'] = digest(args.engine)
        if summary['engine_sha256_after'] != summary['engine_sha256_before']:
            summary.update(status='failed', completed_all_scenarios=False, error='engine bytes changed during run')
        evidence.record('run_complete', status=summary['status'])
        evidence.close()
        summary['events_sha256'] = digest(args.output / 'events.jsonl')
        save_json(args.output / 'summary.json', summary)
    print(json.dumps(dict(status=summary['status'], output=str(args.output),
                          completed_all_scenarios=summary['completed_all_scenarios'],
                          error=summary.get('error')), sort_keys=True), flush=True)
    return 0 if summary['status'] in ('passed', 'expected_tsan_race') else 1


if __name__ == '__main__':
    sys.exit(main())
