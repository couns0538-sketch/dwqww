import argparse
import os
import re
import selectors
import subprocess
import sys
import time
from pathlib import Path


PC20 = {
    'Threads': 1, 'Hash': 16, 'MultiPV': 1, 'UseNNUE': 'true', 'OwnBook': 'false',
    'LmrQuietBase': 93, 'LmrQuietDivisor': 205, 'LmrNoisyBase': 13, 'LmrNoisyDivisor': 333,
    'LmrHistoryDivisor': 5643, 'NullMoveBase': 5, 'LmpBase': 8,
    'HistoryPruneMultiplier': 2220, 'HistoryBonusQuadratic': 24, 'HistoryBonusLinear': 54,
    'HistoryBonusMax': 2212, 'SingularDepth': 6, 'IirDepth': 2, 'NonPawnCorrection': 'true',
    'CuckooRep': 'true', 'HistRework': 2, 'TtPruneV2': 'true', 'CorrHistV2': 'true',
    'MateAlphaGuard': 'true',
}
BENCH_PINS = {11: 278024, 13: 587276}
REFUSAL = re.compile(rb'unknown option|invalid value|\bERROR\b|invalid FEN', re.IGNORECASE)
OPTION = re.compile(rb'^option name (.+?) type ')
NODES = re.compile(rb'\bnodes (\d+)\b')
BESTMOVE = re.compile(rb'^bestmove (0000|[a-h][1-8][a-h][1-8][qrbn]?)(?: ponder [a-h][1-8][a-h][1-8][qrbn]?)?$')


class EngineRun:
    def __init__(self, executable, stdout, stderr, commands, timeout):
        self.executable = executable
        self.stdout = stdout
        self.stderr = stderr
        self.commands = commands
        self.timeout = timeout
        self.pending = bytearray()
        self.eof = False

    def __enter__(self):
        self.process = subprocess.Popen(
            [self.executable], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr,
        )
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)
        return self

    def send(self, command):
        data = command.encode('ascii') + b'\n'
        self.commands.write(data)
        self.commands.flush()
        self.process.stdin.write(data)
        self.process.stdin.flush()

    def read_chunk(self, deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not self.selector.select(remaining):
            return None
        data = os.read(self.process.stdout.fileno(), 65536)
        if data:
            self.stdout.write(data)
            self.stdout.flush()
        else:
            self.eof = True
        return data

    def receive(self, done, description):
        deadline = time.monotonic() + self.timeout
        lines = []
        while True:
            newline = self.pending.find(b'\n')
            if newline < 0:
                data = self.read_chunk(deadline)
                if data is None:
                    raise RuntimeError(f'timed out waiting for {description}')
                if not data:
                    raise RuntimeError(f'engine stdout closed before {description}')
                self.pending.extend(data)
                continue
            line = bytes(self.pending[:newline]).rstrip(b'\r')
            del self.pending[:newline + 1]
            if REFUSAL.search(line):
                raise RuntimeError(f'engine refused protocol: {line!r}')
            lines.append(line)
            if done(line):
                return lines

    def set_up(self):
        self.send('uci')
        hello = self.receive(lambda line: line == b'uciok', 'uciok')
        advertised = {match[1].decode('ascii') for line in hello if (match := OPTION.match(line))}
        if missing := PC20.keys() - advertised:
            raise RuntimeError(f'engine omitted PC20 options: {sorted(missing)}')
        for name, value in PC20.items():
            self.send(f'setoption name {name} value {value}')
        self.ready()

    def ready(self):
        self.send('isready')
        self.receive(lambda line: line == b'readyok', 'readyok')

    def __exit__(self, error_type, error, traceback):
        failure = None
        try:
            if self.process.poll() is None:
                try:
                    if error_type is not None:
                        self.send('stop')
                    self.send('quit')
                except BrokenPipeError:
                    pass
            deadline = time.monotonic() + 5
            while not self.eof and self.read_chunk(deadline):
                pass
            try:
                status = self.process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.process.kill()
                status = self.process.wait(timeout=2)
                failure = RuntimeError('engine failed to exit after quit')
            if not self.eof:
                deadline = time.monotonic() + 1
                while not self.eof and self.read_chunk(deadline):
                    pass
            if status != 0 and failure is None:
                failure = RuntimeError(f'engine exited with status {status}')
        finally:
            self.selector.close()
            self.process.stdout.close()
            try:
                self.process.stdin.close()
            except BrokenPipeError:
                pass
        if error_type is None and failure is not None:
            raise failure


def run_benches(executable, files, timeout):
    results = {}
    for depth in BENCH_PINS:
        with EngineRun(executable, *files, timeout) as engine:
            engine.set_up()
            engine.send(f'bench {depth}')
            prefix = f'info string bench depth {depth} nodes '.encode('ascii')
            bench = engine.receive(lambda line: line.startswith(prefix), f'bench {depth}')[-1]
            match = re.match(rb'(\d+)(?:\s|$)', bench[len(prefix):])
            if match is None:
                raise RuntimeError(f'could not read bench {depth} node count: {bench!r}')
            results[depth] = int(match[1])
    return results


def run_positions(executable, fens, files, rows, timeout):
    with EngineRun(executable, *files, timeout) as engine:
        engine.set_up()
        for index, fen in enumerate(fens, 1):
            engine.send('ucinewgame')
            engine.ready()
            engine.send(f'position fen {fen}')
            engine.send('go depth 10')
            result = engine.receive(lambda line: line.startswith(b'bestmove '), f'bestmove on row {index}')
            bestmove = BESTMOVE.fullmatch(result[-1])
            last_info = next((line for line in reversed(result[:-1]) if line.startswith(b'info depth ')), b'')
            nodes = NODES.search(last_info)
            if bestmove is None or nodes is None:
                raise RuntimeError(f'bad bestmove or missing search info on row {index}: {result[-1]!r}, {last_info!r}')
            rows.write(f'{index}\t{int(nodes[1])}\t{bestmove[1].decode("ascii")}\n')
            rows.flush()


def read_fens(path):
    fens = []
    for line_number, raw_line in enumerate(path.read_text(encoding='ascii').splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        fields = line.split()
        if len(fields) != 6 or fields[1] not in {'w', 'b'} or any(';' in field for field in fields):
            raise ValueError(f'expected a six-field FEN on line {line_number} of {path}')
        fens.append(' '.join(fields))
    if not fens:
        raise ValueError(f'no FENs in {path}')
    return fens


def check_logs(stdout, stderr):
    for path in (stdout, stderr):
        with path.open('rb') as log:
            for line in log:
                if REFUSAL.search(line):
                    raise RuntimeError(f'engine refused protocol in {path}: {line.strip()!r}')


def main():
    parser = argparse.ArgumentParser(description='Record PC20 bench pins and measure cold depth-10 identity.')
    parser.add_argument('executable', type=Path)
    parser.add_argument('positions', type=Path, help='one bare six-field FEN per line, in fixture order')
    parser.add_argument('output', type=Path)
    parser.add_argument('arm', help='suffix used in evidence filenames, e.g. A')
    parser.add_argument('--timeout', type=float, default=30, help='seconds allowed for each UCI response')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', args.arm) or not 0 < args.timeout <= 600:
        parser.error('use a simple arm suffix and a timeout between 0 and 600 seconds')
    executable = args.executable.resolve(strict=True)
    fens = read_fens(args.positions)
    args.output.mkdir(parents=True, exist_ok=True)
    arm = args.arm
    bench = args.output / f'bench_{arm}.txt'
    bench_stderr = args.output / f'bench_{arm}.stderr.txt'
    bench_commands = args.output / f'bench_{arm}.commands.txt'
    raw = args.output / f'identity_{arm}.stdout.txt'
    raw_stderr = args.output / f'identity_{arm}.stderr.txt'
    raw_commands = args.output / f'identity_{arm}.commands.txt'
    rows = args.output / f'rows_{arm}.txt'
    for path in (bench, bench_stderr, bench_commands, raw, raw_stderr, raw_commands, rows):
        if path.exists():
            raise FileExistsError(path)
    with bench.open('xb') as out, bench_stderr.open('xb') as err, bench_commands.open('xb') as commands:
        results = run_benches(executable, (out, err, commands), args.timeout)
    check_logs(bench, bench_stderr)
    for depth, actual in results.items():
        expected = BENCH_PINS[depth]
        verdict = 'match' if actual == expected else 'mismatch'
        print(f'{arm}: PC20 bench {depth} {actual} nodes, expected {expected} ({verdict})', flush=True)
    with raw.open('xb') as out, raw_stderr.open('xb') as err, raw_commands.open('xb') as commands, rows.open('x', encoding='ascii') as row_file:
        run_positions(executable, fens, (out, err, commands), row_file, args.timeout)
    check_logs(raw, raw_stderr)
    print(f'{arm}: {len(fens)} depth-10 rows written to {rows}')


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError) as error:
        print(f'identity run failed: {error}', file=sys.stderr)
        raise SystemExit(1) from error
