"""Independent streamed qualification of a frozen native legal-chain candidate."""
import argparse
import ctypes
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
import hashlib
import json
import math
import msvcrt
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import time

import chess
import psutil

ROOT = Path('D:/a14')
DEFAULT_CANDIDATE = ROOT / 'tools/r14_native/build/chain_native_r03.exe'
DEFAULT_SHA256 = 'f1827f44d1e10ab503aed1ac9d1fb4bacc23d8a2cc1199d78ac0aea36a6c446a'


@dataclass(eq=True)
class Pair:
    ident: str
    start: str
    target: str
    result1: float
    result2: float
    depth: int
    stratum: str
    expected: bool
    oracle_witness: list

    def wire(self, node_limit):
        return '\t'.join((self.ident, self.start, str(self.result1), self.target,
                          str(self.result2), '8', str(node_limit)))


def state(board):
    return (board.pawns, board.knights, board.bishops, board.rooks, board.queens,
            board.kings, board.occupied_co[chess.WHITE], board.occupied_co[chess.BLACK],
            board.turn, board.castling_rights, board.ep_square,
            board.halfmove_clock, board.fullmove_number)


def oracle_exact(start, target, depth, node_limit):
    """Unpruned exhaustive external-oracle DFS; None means its budget ran out."""
    target_key = state(target)
    visited = 0

    def visit(board, remaining):
        nonlocal visited
        if visited >= node_limit:
            return None
        visited += 1
        if remaining == 0:
            return state(board) == target_key
        for move in board.legal_moves:
            board.push(move)
            result = visit(board, remaining - 1)
            board.pop()
            if result is not False:
                return result
        return False

    return visit(start.copy(stack=False), depth)


class Walk:
    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.board = chess.Board()

    def next(self):
        if self.board.is_game_over() or self.board.ply() >= 240:
            self.board = chess.Board()
        self.board.push(self.rng.choice(list(self.board.legal_moves)))
        if not any(self.board.legal_moves):
            self.board = chess.Board()
        return self.board.copy(stack=False)


def one_ply_pairs(count, seed):
    walk = Walk(seed)
    rng = random.Random(seed ^ 140014)
    for i in range(count):
        board = walk.next()
        move = rng.choice(list(board.legal_moves))
        target = board.copy(stack=False)
        target.push(move)
        result1 = rng.choice([0.0, 0.5, 1.0])
        result2 = result1
        expected = True
        witness = [move.uci()]
        if i % 2:
            mutation = (i // 2) % 3
            if mutation == 0:
                target.halfmove_clock += rng.randrange(1, 5)
            elif mutation == 1:
                occupied = list(target.piece_map())
                empties = list(chess.SquareSet(~target.occupied & chess.BB_ALL))
                for _ in range(20):
                    probe = target.copy(stack=False)
                    source = rng.choice(occupied)
                    piece = probe.remove_piece_at(source)
                    probe.set_piece_at(rng.choice(empties), piece)
                    if probe.is_valid() and state(probe) != state(target):
                        target = probe
                        break
                else:
                    target.halfmove_clock += 1
            else:
                result2 = (result1 + 0.5) % 1.5
            expected = False if result1 != result2 else oracle_exact(board, target, 1, 1000)
            if expected is None:
                raise RuntimeError('one-ply oracle unexpectedly exhausted')
            if not expected:
                witness = []
            else:
                # A mutation that happens to be legal is counted according to the oracle.
                witness = []
                for actual in board.legal_moves:
                    child = board.copy(stack=False)
                    child.push(actual)
                    if state(child) == state(target):
                        witness = [actual.uci()]
                        break
        yield Pair(f'one-{i}', board.fen(en_passant='fen'), target.fen(en_passant='fen'),
                   result1, result2, 1, 'one_ply', bool(expected), witness)


def deep_pairs(per_depth, seed):
    walk = Walk(seed)
    rng = random.Random(seed ^ 140028)
    for depth in range(2, 9):
        emitted = 0
        while emitted < per_depth:
            start = walk.next()
            target = start.copy(stack=False)
            witness = []
            for _ in range(depth):
                moves = list(target.legal_moves)
                if not moves:
                    break
                move = rng.choice(moves)
                witness.append(move.uci())
                target.push(move)
            if len(witness) != depth:
                continue
            result = rng.choice([0.0, 0.5, 1.0])
            yield Pair(f'deep-{depth}-{emitted}', start.fen(en_passant='fen'), target.fen(en_passant='fen'),
                       result, result, depth, 'deep_positive', True, witness)
            emitted += 1


def exhaustive_negatives(count, seed):
    walk = Walk(seed)
    rng = random.Random(seed ^ 140042)
    emitted = 0
    while emitted < count:
        start = walk.next()
        target = start.copy(stack=False)
        for _ in range(2):
            choices = list(target.legal_moves)
            if not choices:
                break
            target.push(rng.choice(choices))
        if target.ply() - start.ply() != 2:
            continue
        target.halfmove_clock += rng.randrange(1, 4)
        answer = oracle_exact(start, target, 2, 100000)
        if answer is None:
            raise RuntimeError('two-ply oracle exhausted; no negative certified')
        if answer:
            continue
        yield Pair(f'negative-{emitted}', start.fen(en_passant='fen'), target.fen(en_passant='fen'),
                   0.5, 0.5, 2, 'exhaustive_negative', False, [])
        emitted += 1


SPECIAL_FENS = [
    'r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 7 15',
    'r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 7 15',
    '4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 2',
    '4k3/8/8/8/3Pp3/8/8/4K3 b - d3 0 2',
    'k3r3/8/8/3pP3/8/8/8/4K3 w - d6 0 2',
    '4k3/P7/8/8/8/8/7p/4K3 w - - 0 10',
    '4k3/P7/8/8/8/8/7p/4K3 b - - 0 10',
    '1r2k3/P7/8/8/8/8/7p/4K3 w - - 0 10',
    '4k3/8/8/8/8/8/4r3/4K3 w - - 4 15',
    '7k/6Q1/6K1/8/8/8/8/8 b - - 0 20',
    '7k/5Q2/6K1/8/8/8/8/8 b - - 0 20',
]


def special_pairs(seed):
    rng = random.Random(seed)
    for index, fen in enumerate(SPECIAL_FENS):
        board = chess.Board(fen)
        for first in list(board.legal_moves):
            if not (board.is_castling(first) or board.is_en_passant(first) or first.promotion):
                continue
            target = board.copy(stack=False)
            target.push(first)
            witness = [first.uci()]
            for _ in range(3):
                choices = list(target.legal_moves)
                if not choices:
                    break
                move = rng.choice(choices)
                target.push(move)
                witness.append(move.uci())
            yield Pair(f'special-{index}-{first.uci()}', fen, target.fen(en_passant='fen'),
                       0.5, 0.5, len(witness), 'special_positive', True, witness)
    for index, sequence in enumerate([
        ['g1f3', 'g8f6', 'b1c3', 'b8c6'],
        ['b1c3', 'b8c6', 'g1f3', 'g8f6'],
        ['g1f3', 'g8f6', 'e2e4', 'e7e5'],
    ]):
        start = chess.Board()
        start.halfmove_clock = 12
        target = start.copy(stack=False)
        for token in sequence:
            target.push_uci(token)
        yield Pair(f'transpose-{index}', start.fen(en_passant='fen'), target.fen(en_passant='fen'),
                   1.0, 1.0, len(sequence), 'clock_and_transposition', True, sequence)


def compare(item, reply, cap):
    if not isinstance(reply, dict) or reply.get('id') != item.ident:
        return 'disagree', 'response ID or object mismatch'
    nodes = reply.get('nodes')
    if type(nodes) is not int or nodes < 0 or nodes > cap:
        return 'disagree', 'invalid or over-budget node count'
    witness = reply.get('witness')
    if not isinstance(witness, list) or not all(isinstance(token, str) for token in witness):
        return 'disagree', 'invalid witness array'
    status = reply.get('status')
    if status == 'UNKNOWN':
        if witness or reply.get('reason') != 'node_limit':
            return 'disagree', 'invalid unknown response'
        return 'unknown', None
    if status == 'UNREACHABLE':
        if witness:
            return 'disagree', 'unreachable response supplied a witness'
        return ('disagree', 'native contradicts positive oracle') if item.expected else ('agree', None)
    if status != 'REACHABLE':
        return 'disagree', 'unknown status value'
    if not item.expected:
        return 'disagree', 'native contradicts negative oracle'
    if len(witness) != item.depth or item.result1 != item.result2:
        return 'disagree', 'witness depth or result mismatch'
    board = chess.Board(item.start)
    try:
        for token in witness:
            move = chess.Move.from_uci(token)
            if move not in board.legal_moves:
                return 'disagree', 'illegal witness move'
            board.push(move)
    except ValueError:
        return 'disagree', 'unparsable witness move'
    if state(board) != state(chess.Board(item.target)):
        return 'disagree', 'witness does not reach exact target'
    return 'agree', None


def hashes(path):
    md5, sha = hashlib.md5(), hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            md5.update(block)
            sha.update(block)
    return dict(path=str(Path(path).resolve()), md5=md5.hexdigest(), sha256=sha.hexdigest())


def owned_bytes():
    total = 0
    for directory, dirs, files in os.walk(ROOT, followlinks=False):
        retained = []
        for name in dirs:
            path = Path(directory) / name
            if path.is_symlink() or os.path.isjunction(path):
                total += path.lstat().st_size
            else:
                retained.append(name)
        dirs[:] = retained
        for name in files:
            path = Path(directory) / name
            if path.is_symlink():
                total += path.lstat().st_size
            else:
                total += path.stat().st_size
    return total


def resource_guard(child=None, reserve_bytes=1048576):
    if shutil.disk_usage('D:/').free < 50 * 1024**3 + reserve_bytes or shutil.disk_usage('C:/').free < 30 * 1024**3:
        raise RuntimeError('disk floor breached')
    if owned_bytes() + reserve_bytes >= 5000000000:
        raise OSError('shared owned storage cap exceeded')
    if psutil.virtual_memory().available < 8 * 1024**3:
        raise RuntimeError('free RAM floor breached')
    used = psutil.Process().memory_info().rss
    if child is not None and child.poll() is None:
        used += psutil.Process(child.pid).memory_info().rss
    if used > 2 * 1024**3:
        raise RuntimeError('owned computation RAM cap exceeded')


def check_duration(value):
    if not math.isfinite(value) or value <= 0:
        raise ValueError('finite positive deadline required')
    return value


def finish_status(report, *, fixture, foundation_requested, close_error=None):
    if close_error is not None:
        report['reasons'].append('native close: ' + close_error)
        report['complete'] = report['completed'] = False
        report['smoke_status'] = 'UNVERIFIED'
        report['status'] = 'FAIL' if report['status'] == 'FAIL' else 'UNVERIFIED'
        return
    foundation = report.get('by_stratum', {}).get('one_ply', {}).get('resolved', 0)
    clean = not report['pairs']['disagreements'] and not report['moves']['disagreements']
    complete = report.get('complete') is True and report.get('completed') is True
    foundation_ok = foundation >= foundation_requested and (fixture or foundation_requested >= 1000000)
    if not clean:
        report['status'] = 'FAIL'
        report['smoke_status'] = 'UNVERIFIED'
    elif not complete or not foundation_ok:
        report['status'] = 'UNVERIFIED'
        report['smoke_status'] = 'UNVERIFIED'
        if not foundation_ok:
            report['reasons'].append('resolved one-ply foundation is below its required count; extra strata cannot compensate')
    elif fixture:
        report['status'] = 'UNVERIFIED'
        report['smoke_status'] = 'PASS'
    else:
        report['status'] = 'PASS'


def success_exit(report, *, fixture):
    return report['status'] == 'PASS' or (fixture and report.get('smoke_status') == 'PASS'
                                         and report.get('complete') is True)


def publish_report(report, path):
    payload = json.dumps(report, sort_keys=True, indent=2) + '\n'
    try:
        resource_guard(reserve_bytes=len(payload.encode('utf-8')) + 4096)
    except Exception as error:
        report['complete'] = report['completed'] = False
        report['smoke_status'] = 'UNVERIFIED'
        report['status'] = 'FAIL' if report['status'] == 'FAIL' else 'UNVERIFIED'
        report['reasons'].append(f'final resource refusal: {type(error).__name__}: {error}')
        return False
    try:
        pending = path.with_name(path.name + '.part')
        with pending.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        resource_guard(reserve_bytes=4096)
        os.rename(pending, path)
    except Exception as error:
        report['complete'] = report['completed'] = False
        report['smoke_status'] = 'UNVERIFIED'
        report['status'] = 'FAIL' if report['status'] == 'FAIL' else 'UNVERIFIED'
        report['reasons'].append(f'final publication failed: {type(error).__name__}: {error}')
        return False
    return True


class Native:
    def __init__(self, executable, mode, stderr, deadline=None):
        env = dict(os.environ, CUDA_VISIBLE_DEVICES='-1', HIP_VISIBLE_DEVICES='-1',
                   OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
                   TEMP=str(stderr.parent), TMP=str(stderr.parent))
        self.err = stderr.open('ab')
        self.process = subprocess.Popen([str(executable), mode], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=self.err, bufsize=0, env=env,
                                        creationflags=subprocess.IDLE_PRIORITY_CLASS | subprocess.CREATE_NO_WINDOW)
        self.sent = self.received = 0
        self.deadline = deadline
        self.buffer = bytearray()
        self.closed = self.aborted = False

    def available(self):
        count = ctypes.c_ulong()
        handle = ctypes.c_void_p(msvcrt.get_osfhandle(self.process.stdout.fileno()))
        ok = ctypes.windll.kernel32.PeekNamedPipe(handle, None, 0, None, ctypes.byref(count), None)
        if not ok:
            error = ctypes.windll.kernel32.GetLastError()
            if error in (109, 232):
                return 0
            if self.process.poll() is not None:
                return 0
            raise RuntimeError('owned native pipe inspection failed')
        return count.value

    def read_ready(self):
        count = self.available()
        return os.read(self.process.stdout.fileno(), min(count, 65536)) if count else b''

    def query(self, line):
        return self.query_many([line])[0]

    def query_many(self, lines):
        if not 1 <= len(lines) <= 8 or any(not isinstance(line, str) or '\n' in line or '\r' in line for line in lines):
            raise ValueError('batch requires one to eight single-line requests')
        identifiers = [line.split('\t', 1)[0] for line in lines]
        if any(not ident for ident in identifiers) or len(set(identifiers)) != len(identifiers):
            raise ValueError('batch identifiers must be nonempty and unique')
        payload = ('\n'.join(lines) + '\n').encode('utf-8')
        if len(payload) > 2048:
            raise ValueError('generated batch exceeds bounded pipe-write size')
        if self.deadline is not None and time.monotonic() >= self.deadline:
            self.aborted = True
            raise Deadline('deadline reached before native batch')
        if self.buffer:
            raise RuntimeError('unsolicited native bytes precede request')
        if self.process.stdin.write(payload) != len(payload):
            raise RuntimeError('partial native request write')
        self.sent += len(lines)
        started = last_guard = time.monotonic()
        replies = []
        while len(replies) < len(lines):
            now = time.monotonic()
            if self.deadline is not None and now >= self.deadline:
                self.aborted = True
                raise Deadline('deadline reached while waiting on owned native request')
            if now - started >= 30:
                self.aborted = True
                raise RuntimeError('native response exceeded 30-second request limit')
            if now - last_guard >= 1:
                resource_guard(self.process)
                last_guard = now
            self.buffer.extend(self.read_ready())
            if len(self.buffer) > 1048576:
                self.aborted = True
                raise RuntimeError('native response exceeded one MiB')
            while b'\n' in self.buffer and len(replies) < len(lines):
                reply, _, remaining = self.buffer.partition(b'\n')
                self.buffer = bytearray(remaining)
                decoded = json.loads(reply.decode('utf-8'))
                self.received += 1
                if not isinstance(decoded, dict) or decoded.get('id') != identifiers[len(replies)]:
                    raise RuntimeError('native response object or identifier mismatch')
                replies.append(decoded)
            if len(replies) == len(lines):
                break
            if self.process.poll() is not None:
                raise RuntimeError('native response stream ended early')
            time.sleep(0.0005)
        if self.buffer or self.available():
            raise RuntimeError('native batch produced unsolicited extra output')
        return replies

    def close(self):
        if self.closed:
            return
        self.closed = True
        try:
            self.process.stdin.close()
            extra = len(self.buffer)
            deadline = time.monotonic() + 2
            while self.process.poll() is None and not self.aborted:
                extra += len(self.read_ready())
                if time.monotonic() >= deadline:
                    self.aborted = True
                    break
                time.sleep(0.001)
            if self.aborted:
                if self.process.poll() is None:
                    self.process.kill()
                    self.process.wait(timeout=5)
                raise RuntimeError('owned native child required bounded termination')
            extra += len(self.read_ready())
            code = self.process.returncode
            if code != 0 or extra or self.sent != self.received:
                raise RuntimeError('native exit, response count, or unsolicited output mismatch')
        finally:
            if self.process.poll() is None:
                self.process.kill()
                self.process.wait()
            self.process.stdout.close()
            self.err.close()


def path_features(item):
    board = chess.Board(item.start)
    result = Counter(black_start=int(not board.turn), nonzero_halfmove_start=int(board.halfmove_clock > 0))
    for token in item.oracle_witness:
        move = chess.Move.from_uci(token)
        result['castling'] += int(board.is_castling(move))
        result['en_passant'] += int(board.is_en_passant(move))
        result['promotion'] += int(bool(move.promotion))
        result['capture'] += int(board.is_capture(move))
        result['clock_reset'] += int(board.is_zeroing(move))
        board.push(move)
    result['nonzero_halfmove_with_reset'] = int(bool(result['nonzero_halfmove_start'] and result['clock_reset']))
    result['nonzero_halfmove_without_reset'] = int(bool(result['nonzero_halfmove_start'] and item.oracle_witness and not result['clock_reset']))
    return result


class Deadline(Exception):
    pass


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument('--candidate-sha256', default=DEFAULT_SHA256)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--seed', type=int, default=140020261103)
    parser.add_argument('--pairs', type=int, default=1000000)
    parser.add_argument('--move-positions', type=int, default=10000)
    parser.add_argument('--deep-pairs-per-depth', type=int, default=256)
    parser.add_argument('--exhaustive-negatives', type=int, default=256)
    parser.add_argument('--node-limit', type=int, default=100000)
    parser.add_argument('--deadline-seconds', type=float, default=5400)
    parser.add_argument('--fixture', action='store_true')
    parser.add_argument('--cpu', type=int, default=3)
    args = parser.parse_args(argv)
    if any(value < 1 for value in (args.pairs, args.move_positions, args.deep_pairs_per_depth,
                                   args.exhaustive_negatives, args.node_limit)):
        parser.error('positive counts, node cap, and deadline required')
    try:
        check_duration(args.deadline_seconds)
    except ValueError as error:
        parser.error(str(error))
    if not args.fixture and args.pairs < 1000000:
        parser.error('fewer than one million foundation pairs requires --fixture')
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
    if args.cpu not in (0, 1, 2, 3) or args.cpu not in psutil.Process().cpu_affinity():
        parser.error('requested CPU is unavailable to this process')
    samples = [psutil.cpu_percent(interval=0.25, percpu=True)[args.cpu] for _ in range(2)]
    if sum(samples) / len(samples) > 70:
        parser.error('requested CPU is busy; qualification admission refused')
    psutil.Process().cpu_affinity([args.cpu])
    resource_guard()
    out = args.out.resolve()
    if ROOT.resolve() not in out.parents:
        parser.error('output must be a new directory below D:/a14')
    candidate = hashes(args.candidate)
    if candidate['sha256'] != args.candidate_sha256:
        parser.error('candidate identity mismatch')
    out.mkdir(parents=True, exist_ok=False)
    began = time.monotonic()
    report = dict(schema=1, mode='fixture' if args.fixture else 'qualification',
                  scope='qualification_smoke' if args.fixture else 'production_helper_qualification', status='UNVERIFIED',
                  start_vienna=datetime.now().strftime('%Y-%m-%d %H:%M:%S Vienna'),
                  candidate=candidate, harness=hashes(__file__), seed=args.seed,
                  python=sys.version, chess_version=chess.__version__,
                  requested=dict(one_ply=args.pairs, move_positions=args.move_positions,
                                 deep_per_depth=args.deep_pairs_per_depth, exhaustive_negatives=args.exhaustive_negatives),
                  node_limit=args.node_limit, deadline_seconds=args.deadline_seconds,
                  cpu=args.cpu, cpu_admission_samples=samples,
                  pairs=dict(attempted=0, resolved=0, unknown=0, disagreements=0),
                  by_depth={}, by_stratum={}, moves=dict(attempted=0, resolved=0, disagreements=0, legal_successors=0,
                                                       special_positions=0, random_positions=0),
                  path_features={}, reasons=[], completed=False)
    by_depth, by_stratum = defaultdict(Counter), defaultdict(Counter)
    features = Counter()
    last_progress = began
    child = None
    close_error = None

    def checkpoint(force=False):
        nonlocal last_progress
        now = time.monotonic()
        if force or now - last_progress >= 30:
            resource_guard(child.process if child else None)
            progress = dict(elapsed_seconds=round(now - began, 3), pairs=report['pairs'], moves=report['moves'])
            text = json.dumps(progress, sort_keys=True)
            with (out / 'progress.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(text + '\n')
            print(text, flush=True)
            last_progress = now
        if now - began >= args.deadline_seconds:
            raise Deadline('cooperative deadline reached between bounded native requests')

    try:
        child = Native(args.candidate, '--moves', out / 'native.stderr.log', began + args.deadline_seconds)
        walk = Walk(args.seed ^ 141000)
        for index in range(len(SPECIAL_FENS) + args.move_positions):
            checkpoint()
            board = chess.Board(SPECIAL_FENS[index]) if index < len(SPECIAL_FENS) else walk.next()
            ident = f'moves-{index}'
            reply = child.query(ident + '\t' + board.fen(en_passant='fen'))
            report['moves']['attempted'] += 1
            expected = {}
            for move in board.legal_moves:
                target = board.copy(stack=False)
                target.push(move)
                expected[move.uci()] = target.fen(en_passant='fen')
            valid = isinstance(reply, dict) and reply.get('id') == ident and reply.get('status') == 'OK'
            actual = reply.get('moves') if valid else None
            valid = valid and isinstance(actual, list) and all(isinstance(m, dict) and set(m) == {'uci', 'fen'} for m in actual)
            valid = valid and actual == [dict(uci=token, fen=expected[token]) for token in sorted(expected)]
            if not valid:
                report['moves']['disagreements'] += 1
                (out / 'failure.json').write_text(json.dumps(dict(id=ident, fen=board.fen(en_passant='fen'),
                                                                expected=expected, native=reply), indent=2), encoding='utf-8')
                raise RuntimeError('legal successor-set disagreement')
            report['moves']['resolved'] += 1
            report['moves']['legal_successors'] += len(expected)
            report['moves']['special_positions' if index < len(SPECIAL_FENS) else 'random_positions'] += 1
        child.close()
        child = Native(args.candidate, '--pairs', out / 'native.stderr.log', began + args.deadline_seconds)
        generators = [one_ply_pairs(args.pairs, args.seed), deep_pairs(args.deep_pairs_per_depth, args.seed ^ 142000),
                      exhaustive_negatives(args.exhaustive_negatives, args.seed ^ 143000), special_pairs(args.seed ^ 144000)]
        unknown_samples = 0
        for generator in generators:
            for item in generator:
                checkpoint()
                reply = child.query(item.wire(args.node_limit))
                outcome, reason = compare(item, reply, args.node_limit)
                report['pairs']['attempted'] += 1
                report_key = dict(agree='resolved', unknown='unknown', disagree='disagreements')[outcome]
                report['pairs'][report_key] += 1
                for counter in (by_depth[str(item.depth)], by_stratum[item.stratum]):
                    counter['attempted'] += 1
                    counter[report_key] += 1
                    counter['oracle_positive' if item.expected else 'oracle_negative'] += 1
                    counter['native_nodes'] += reply.get('nodes', 0) if type(reply.get('nodes')) is int else 0
                    if outcome == 'unknown':
                        counter['unknown_' + str(reply.get('reason'))] += 1
                features.update(path_features(item))
                if outcome == 'unknown' and unknown_samples < 100:
                    with (out / 'unknown_samples.jsonl').open('a', encoding='utf-8') as stream:
                        stream.write(json.dumps(dict(pair=asdict(item), native=reply), sort_keys=True) + '\n')
                    unknown_samples += 1
                if outcome == 'disagree':
                    (out / 'failure.json').write_text(json.dumps(dict(pair=asdict(item), native=reply, reason=reason), indent=2), encoding='utf-8')
                    raise RuntimeError('pair disagreement: ' + reason)
        report['completed'] = True
        foundation_resolved = by_stratum['one_ply']['resolved']
        report['status'] = 'UNVERIFIED' if args.fixture else ('PASS' if foundation_resolved >= args.pairs else 'UNVERIFIED')
        if args.fixture:
            report['smoke_status'] = 'PASS'
            report['reasons'].append('fixture scope; production qualification requires at least one million requested/resolved pairs')
        elif foundation_resolved < args.pairs:
            report['reasons'].append('resolved one-ply foundation count is below requested count')
        required_features = ('castling', 'en_passant', 'promotion', 'capture', 'black_start',
                             'nonzero_halfmove_with_reset', 'nonzero_halfmove_without_reset')
        missing_features = [feature for feature in required_features if not features[feature]]
        if missing_features:
            report['status'] = 'UNVERIFIED'
            report['smoke_status'] = 'UNVERIFIED'
            report['completed'] = False
            report['reasons'].append('missing required special coverage: ' + ', '.join(missing_features))
    except Deadline as error:
        report['status'] = 'UNVERIFIED'
        report['reasons'].append(str(error))
    except Exception as error:
        report['status'] = 'FAIL' if report['pairs']['disagreements'] or report['moves']['disagreements'] else 'UNVERIFIED'
        report['reasons'].append(f'{type(error).__name__}: {error}')
    finally:
        if child is not None:
            try:
                child.close()
            except Exception as error:
                close_error = f'{type(error).__name__}: {error}'
        report['by_depth'] = {key: dict(value) for key, value in sorted(by_depth.items())}
        report['by_stratum'] = {key: dict(value) for key, value in sorted(by_stratum.items())}
        report['path_features'] = dict(features)
        report['deep_coverage_status'] = 'UNVERIFIED' if by_stratum['deep_positive']['unknown'] else ('COMPLETE' if report['completed'] else 'INCOMPLETE')
        report['end_vienna'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S Vienna')
        report['elapsed_seconds'] = time.monotonic() - began
        report['candidate_after'] = hashes(args.candidate)
        if report['candidate_after'] != candidate:
            report['status'] = 'UNVERIFIED'
            report['smoke_status'] = 'UNVERIFIED'
            report['completed'] = False
            report['reasons'].append('candidate changed during qualification')
        report['native_exe'] = candidate['path']
        report['native_md5'] = candidate['md5']
        report['native_sha256'] = candidate['sha256']
        report['requested_pairs'] = args.pairs
        report['resolved_pairs'] = report['pairs']['resolved']
        report['unknown_pairs'] = report['pairs']['unknown']
        report['disagreements'] = report['pairs']['disagreements'] + report['moves']['disagreements']
        report['per_depth'] = {str(depth): {field: by_depth[str(depth)][field]
                                         for field in ('attempted', 'resolved', 'unknown', 'disagreements')}
                               for depth in range(1, 9)}
        report['complete'] = report['completed']
        finish_status(report, fixture=args.fixture, foundation_requested=args.pairs, close_error=close_error)
        report['meaning'] = 'Sampled executable/oracle agreement only; no authentic game or production separation claim.'
        published = publish_report(report, out / 'REPORT.json')
        print(json.dumps(dict(status=report['status'], pairs=report['pairs'], moves=report['moves'],
                              complete=report['complete'], reasons=report['reasons'], published=published,
                              elapsed_seconds=report['elapsed_seconds'], report=str(out / 'REPORT.json') if published else None), sort_keys=True), flush=True)
    return 0 if success_exit(report, fixture=args.fixture) else 1


if __name__ == '__main__':
    raise SystemExit(main())
