import argparse
import hashlib
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
CELLS = ('B2', 'N2')
NODE_LIMITS = (50000, 250000)
POSITIONS_SHA = 'd0630396e9e937318bf83e542d2f168c6216831e0dd83283875172d6ff72a2b2'
NET_SHA = 'c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7'
NET_CHECKSUM = b'30ab43b4ba5db5f3'
NET_ACTIVE = b'info string NNUE v3 active: '
REFUSAL = re.compile(
    rb'unknown option|invalid value|\bERROR\b|invalid FEN|no (?:v3 )?network (?:is )?loaded',
    re.IGNORECASE,
)
OPTION = re.compile(rb'^option name (.+?) type ')
UCI_MOVE = rb'[a-h][1-8][a-h][1-8][qrbn]?'
MOVE = re.compile(UCI_MOVE)
BESTMOVE = re.compile(rb'bestmove (0000|' + UCI_MOVE + rb')(?: ponder ' + UCI_MOVE + rb')?')
FINAL_NODES = re.compile(rb'info string final nodes ([0-9]+)')


def check_refusal(line):
    if REFUSAL.search(line):
        raise RuntimeError(f'engine refused protocol: {line!r}')


class EngineRun:
    def __init__(self, executable, stdout, stderr, commands, timeout):
        self.executable = executable
        self.stdout = stdout
        self.stderr = stderr
        self.commands = commands
        self.timeout = timeout
        self.pending = bytearray()
        self.stderr_offset = 0
        self.stderr_pending = bytearray()
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
                    self.check_stderr()
                    raise RuntimeError(f'timed out waiting for {description}')
                if not data:
                    self.check_stderr()
                    raise RuntimeError(f'engine stdout closed before {description}')
                self.pending.extend(data)
                continue
            line = bytes(self.pending[:newline]).rstrip(b'\r')
            del self.pending[:newline + 1]
            check_refusal(line)
            lines.append(line)
            if done(line):
                self.check_stderr()
                return lines

    def check_stderr(self):
        while data := os.pread(self.stderr.fileno(), 65536, self.stderr_offset):
            self.stderr_offset += len(data)
            self.stderr_pending.extend(data)
        complete, newline, partial = self.stderr_pending.rpartition(b'\n')
        if newline:
            self.stderr_pending = partial
            for line in complete.splitlines():
                check_refusal(line)

    def set_up(self, net):
        self.send('uci')
        hello = self.receive(lambda line: line == b'uciok', 'uciok')
        advertised = {match[1].decode('ascii') for line in hello if (match := OPTION.match(line))}
        required = PC20.keys() | ({'NNUEArch', 'NNUEArchFile'} if net is not None else set())
        if missing := required - advertised:
            raise RuntimeError(f'engine omitted requested options: {sorted(missing)}')
        if net is None and 'NNUEArch' in advertised:
            if b'option name NNUEArch type check default false' not in hello:
                raise RuntimeError('built-in cell requires NNUEArch default false')
        for name, value in PC20.items():
            self.send(f'setoption name {name} value {value}')
        if net is not None:
            self.send(f'setoption name NNUEArchFile value {net}')
            self.send('setoption name NNUEArch value true')
        ready = self.ready()
        active = [line for line in ready if line.startswith(NET_ACTIVE)]
        if net is not None:
            marker = re.compile(rb'\bhidden 768\b.*\bchecksum ' + NET_CHECKSUM + rb'\b')
            if len(active) != 1 or not marker.search(active[0]):
                raise RuntimeError(f'expected one active net768 checksum line, got {active!r}')
        elif active:
            raise RuntimeError(f'unexpected NNUE v3 activation in built-in cell: {active!r}')

    def ready(self):
        self.send('isready')
        return self.receive(lambda line: line == b'readyok', 'readyok')

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


def label(result, index):
    best = BESTMOVE.fullmatch(result[-1])
    info = next((line for line in reversed(result[:-1]) if line.startswith(b'info depth ')), b'')
    finals = [line for line in result[:-1] if line.startswith(b'info string final nodes')]
    final = FINAL_NODES.fullmatch(finals[0]) if len(finals) == 1 else None
    if final is None:
        raise RuntimeError(f'row {index}: expected one final node count before bestmove, got {finals!r}')
    fields = info.split()
    try:
        depth = int(fields[2])
        pv_start = fields.index(b'pv')
        nodes = int(fields[fields.index(b'nodes', 3, pv_start) + 1])
        score_at = fields.index(b'score', 3, pv_start)
        score_kind, score_value = fields[score_at + 1: score_at + 3]
    except (IndexError, ValueError) as error:
        raise RuntimeError(f'row {index}: malformed or missing last search-info line {info!r}') from error
    pv_head = fields[pv_start + 1] if pv_start + 1 < len(fields) else b'-'
    if (best is None or depth < 0 or nodes < 0 or (pv_head != b'-' and not MOVE.fullmatch(pv_head))
            or score_kind not in (b'cp', b'mate') or not re.fullmatch(rb'-?[0-9]+', score_value)):
        raise RuntimeError(f'row {index}: invalid search label {info!r}, {result[-1]!r}')
    return f'{index}\t{int(final[1])}\t{best[1].decode("ascii")}\t{score_kind.decode("ascii")}\t{int(score_value)}\n'


def run_positions(executable, fens, files, rows, timeout, node_limit, net):
    with EngineRun(executable, *files, timeout) as engine:
        engine.set_up(net)
        for index, fen in enumerate(fens, 1):
            engine.send('ucinewgame')
            engine.ready()
            engine.send(f'position fen {fen}')
            engine.send(f'go nodes {node_limit}')
            result = engine.receive(lambda line: line.startswith(b'bestmove '), f'bestmove on row {index}')
            rows.write(label(result, index))
            rows.flush()


def read_fens(path):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != POSITIONS_SHA:
        raise ValueError(f'position fixture SHA-256 mismatch: {path}')
    fens = []
    for line_number, line in enumerate(data.decode('ascii').splitlines(), 1):
        fields = line.split()
        if len(fields) != 6 or fields[1] not in {'w', 'b'} or any(';' in field for field in fields):
            raise ValueError(f'expected a six-field FEN on line {line_number} of {path}')
        fens.append(' '.join(fields))
    if len(fens) != 389:
        raise ValueError(f'expected 389 FENs but read {len(fens)}: {path}')
    return fens


def check_logs(stdout, stderr):
    for path in (stdout, stderr):
        with path.open('rb') as log:
            for line in log:
                check_refusal(line.strip())


def main():
    parser = argparse.ArgumentParser(description='Record one Job 7 PC20 node-limit identity cell.')
    parser.add_argument('executable', type=Path)
    parser.add_argument('positions', type=Path, help='one bare six-field FEN per line, in fixture order')
    parser.add_argument('output', type=Path)
    parser.add_argument('tree', choices=('10', '11', 'P'))
    parser.add_argument('cell', choices=CELLS)
    parser.add_argument('--nodes', type=int, choices=NODE_LIMITS, required=True)
    parser.add_argument('--net', type=Path, help='pinned net768 file, required in N2')
    parser.add_argument('--timeout', type=float, default=30, help='seconds allowed for each UCI response')
    args = parser.parse_args()
    if not 0 < args.timeout <= 600:
        parser.error('use a timeout between 0 and 600 seconds')
    if (args.cell == 'N2') != (args.net is not None):
        parser.error('pass --net for the N2 cell only')
    net = args.net.resolve(strict=True) if args.net is not None else None
    if net is not None:
        if '\n' in str(net) or '\r' in str(net):
            raise ValueError('net path must fit on one UCI line')
        with net.open('rb') as file:
            if hashlib.file_digest(file, 'sha256').hexdigest() != NET_SHA:
                raise ValueError(f'net768 SHA-256 mismatch: {net}')
    executable = args.executable.resolve(strict=True)
    fens = read_fens(args.positions)
    args.output.mkdir(parents=True, exist_ok=True)
    arm = f'{args.tree}_{args.cell}'
    raw = args.output / f'identity_{arm}.stdout.txt'
    raw_stderr = args.output / f'identity_{arm}.stderr.txt'
    raw_commands = args.output / f'identity_{arm}.commands.txt'
    rows = args.output / f'rows_{arm}.txt'
    for path in (raw, raw_stderr, raw_commands, rows):
        if path.exists():
            raise FileExistsError(path)
    with raw.open('xb') as out, raw_stderr.open('x+b') as err, raw_commands.open('xb') as commands, rows.open('x', encoding='ascii') as row_file:
        run_positions(executable, fens, (out, err, commands), row_file, args.timeout, args.nodes, net)
    check_logs(raw, raw_stderr)
    print(f'{arm}: {len(fens)} PC20 rows for go nodes {args.nodes} written to {rows}')


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError) as error:
        print(f'identity run failed: {error}', file=sys.stderr)
        raise SystemExit(1) from error
