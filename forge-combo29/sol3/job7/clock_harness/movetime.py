import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import statistics
import sys
import time
from pathlib import Path

import chess
import identity


PINS = {
    'k10': '55fed57fadf76d5e861da3f9bf3601b43c6bf67e6d152d87edfcf648e26207ae',
    'k11': 'a7a34a148b40c14e5ea960dd2d3182fceef7023a38d12db47c2521a430fc1ea5',
}
HELPER_SHA256 = '1f7703dae17160651c6a9d163a4af0d14cb34848c7523fa70a50e260c86d93ca'
EMBEDDED_WEIGHTS_SOURCE_SHA256 = 'a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638'
FIRST_100_SHA256 = 'd54a188484d32b31d87c28e8e50530e5891e5f32fa85a02e89758d7ff2808f89'
GO = 'go movetime 100'


def sha256(path):
    with path.open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest()


def is_bestmove(line):
    return line.split(None, 1)[:1] == [b'bestmove']


class ClockedEngine(identity.EngineRun):
    def send(self, command):
        data = command.encode('ascii') + b'\n'
        self.commands.write(data)
        self.commands.flush()
        started_ns = time.monotonic_ns()
        self.process.stdin.write(data)
        self.process.stdin.flush()
        return started_ns

    def read_chunk(self, deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not self.selector.select(remaining):
            return None
        data = os.read(self.process.stdout.fileno(), 65536)
        self.chunk_received_ns = time.monotonic_ns()
        if data:
            self.stdout.write(data)
            self.stdout.flush()
        else:
            self.eof = True
        return data

    def timed_search(self, index):
        started_ns = self.send(GO)
        result = self.receive(is_bestmove, f'bestmove on row {index}')
        elapsed_ns = self.chunk_received_ns - started_ns
        if elapsed_ns < 0:
            raise RuntimeError(f'row {index}: unsolicited bestmove was buffered before go')
        return result[-1], elapsed_ns


def run_clock(executable, fens, output, timeout):
    output.mkdir(parents=True, exist_ok=False)
    raw = output / 'engine.stdout.txt'
    stderr = output / 'engine.stderr.txt'
    commands = output / 'engine.commands.txt'
    rows = output / 'searches.jsonl'
    elapsed_ns = []
    illegal = []
    failed_row = None
    error = None
    started = datetime.now(timezone.utc).isoformat()
    with raw.open('xb') as out, stderr.open('x+b') as err, commands.open('xb') as cmd, rows.open('x', encoding='utf-8') as logs:
        try:
            with ClockedEngine(executable, out, err, cmd, timeout) as engine:
                engine.set_up(net=None)
                for index, fen in enumerate(fens, 1):
                    failed_row = index
                    board = chess.Board(fen)
                    engine.send('ucinewgame')
                    engine.ready()
                    engine.send(f'position fen {fen}')
                    line, duration = engine.timed_search(index)
                    match = identity.BESTMOVE.fullmatch(line)
                    move = match[1].decode('ascii') if match is not None else None
                    legal = move not in (None, '0000') and chess.Move.from_uci(move) in board.legal_moves
                    if not legal:
                        illegal.append(index)
                    elapsed_ns.append(duration)
                    logs.write(json.dumps({
                        'row': index,
                        'fen': fen,
                        'bestmove': move,
                        'raw_bestmove_line': line.decode('ascii', errors='backslashreplace'),
                        'legal': legal,
                        'wall_ns': duration,
                        'wall_ms': duration / 1_000_000,
                    }) + '\n')
                    logs.flush()
                    failed_row = None
            identity.check_logs(raw, stderr)
        except (OSError, RuntimeError, ValueError) as exc:
            error = str(exc)
    finished = datetime.now(timezone.utc).isoformat()
    output_lines = raw.read_bytes().splitlines()
    bestmove_lines = sum(is_bestmove(line) for line in output_lines)
    ids = [line.decode('ascii', errors='backslashreplace') for line in output_lines if line.startswith(b'id name ')]
    if error is None and (len(ids) != 1 or bestmove_lines != len(elapsed_ns)):
        error = f'Unexpected raw transcript counts: id name={len(ids)}, bestmove={bestmove_lines}, timed={len(elapsed_ns)}'
    return {
        'started_utc': started,
        'finished_utc': finished,
        'id_name_lines': ids,
        'expected_searches': len(fens),
        'bestmove_lines_stdout': bestmove_lines,
        'timed_bestmoves': len(elapsed_ns),
        'every_reported_bestmove_legal': 0 < bestmove_lines == len(elapsed_ns) and not illegal,
        'illegal_or_malformed_rows': illegal,
        'median_wall_ms': statistics.median(elapsed_ns) / 1_000_000 if elapsed_ns else None,
        'max_wall_ms': max(elapsed_ns) / 1_000_000 if elapsed_ns else None,
        'stderr_bytes': stderr.stat().st_size,
        'failed_row': failed_row,
        'error': error,
        'artifacts_sha256': {path.name: sha256(path) for path in (raw, stderr, commands, rows)},
    }


def main():
    parser = argparse.ArgumentParser(description='Job 7 Step 2, single-thread PC20 movetime record.')
    parser.add_argument('tree', choices=PINS)
    parser.add_argument('executable', type=Path)
    parser.add_argument('fixture', type=Path)
    parser.add_argument('output', type=Path, help='new output directory for one tree')
    parser.add_argument('--timeout', type=float, default=5, help='timeout in seconds per UCI response')
    args = parser.parse_args()
    if not 0 < args.timeout <= 60:
        parser.error('timeout must be between 0 and 60 seconds')
    helper = Path(identity.__file__).resolve()
    if sha256(helper) != HELPER_SHA256:
        raise ValueError('Job 4 identity helper source hash differs')
    executable = args.executable.resolve(strict=True)
    executable_hash = sha256(executable)
    if executable_hash != PINS[args.tree]:
        raise ValueError(f'{args.tree} ordinary Forge executable does not match its pin: {executable_hash}')
    fixture = args.fixture.resolve(strict=True)
    fens = identity.read_fens(fixture)[:100]
    subset_hash = hashlib.sha256(b''.join(fixture.read_bytes().splitlines(keepends=True)[:100])).hexdigest()
    if len(fens) != 100 or subset_hash != FIRST_100_SHA256:
        raise ValueError('The first 100 Job 3 fixture lines do not match their pin')

    result = run_clock(executable, fens, args.output, args.timeout)
    result.update({
        'tree': args.tree,
        'executable': str(executable),
        'executable_sha256': executable_hash,
        'engine_configuration_source': 'Job 4 Release, ordinary executable',
        'engine_options': identity.PC20,
        'net': 'embedded AL1 s198; no external NNUE file',
        'embedded_weights_source_sha256': EMBEDDED_WEIGHTS_SOURCE_SHA256,
        'fixture': str(fixture),
        'fixture_sha256': identity.POSITIONS_SHA,
        'fixture_first_100_lines_sha256': subset_hash,
        'go': GO,
        'timeout_s': args.timeout,
        'clock': 'time.monotonic_ns; immediately before writing go, until OS read completes the bestmove line',
        'clock_implementation': time.get_clock_info('monotonic').implementation,
        'python_chess': chess.__version__,
        'harness_sha256': sha256(Path(__file__)),
        'job4_identity_helper_sha256': HELPER_SHA256,
    })
    rendered = json.dumps(result, indent=2) + '\n'
    (args.output / 'summary.json').write_text(rendered, encoding='utf-8')
    print(rendered, end='')
    return int(result['error'] is not None or result['timed_bestmoves'] != 100 or
               not result['every_reported_bestmove_legal'])


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as exc:
        print(f'movetime run failed: {exc}', file=sys.stderr)
        raise SystemExit(1) from exc
