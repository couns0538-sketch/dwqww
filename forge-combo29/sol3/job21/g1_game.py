#!/usr/bin/env python3
"""Capture one Job 21 G1 game, with raw UCI and per-search monotonic timing."""

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from time import monotonic_ns

import chess

import identity


EXE_SHA = 'bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6'
FIXTURE_SHA = '3c1b17332eca46a912f572eae8197324f466a8e2f909653104c427457ffb0521'
HELPER_SHA = '4a51fe258b610b32055cc7e42614640d9dd0abb8988fdb304d1ad31f7fbcef61'
PYTHON_CHESS = '1.11.2'
MOVE_CAP = 200
SOFT_NODES = 2000
HARD_NODES = SOFT_NODES * 4
GO = f'go softnodes {SOFT_NODES}'
HEADER = ('game', 'ply', 'pieces', 'last_depth', 'last_nodes', 'last_time_ms', 'final_nodes', 'wall_ns',
          'cap', 'prev_depth', 'prev_nodes', 'prev2_depth', 'prev2_nodes', 'bestmove', 'root_fen')
TIME_HEADER = ('game', 'ply', 'monotonic_go_write_ns', 'monotonic_bestmove_parsed_ns')
FINAL_NODES = re.compile(rb'info string softnodes nodes ([0-9]+)')
INFO = re.compile(
    rb'info depth ([0-9]+) seldepth [0-9]+ score (?:cp|mate) -?[0-9]+ '
    rb'nodes ([0-9]+) nps [0-9]+ hashfull [0-9]+ time ([0-9]+) pv(?: ([^\r\n]+))?'
)


def sha(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def fixture_game(path, game):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != FIXTURE_SHA or b'\r' in data or not data.endswith(b'\n'):
        raise ValueError('unexpected W1 fixture SHA-256 or line endings')
    fens = data.decode('ascii').splitlines()
    if len(fens) != 1000:
        raise ValueError('expected exactly 1,000 W1 FENs')
    return fens[game - 1]


class TimedEngine(identity.EngineRun):
    def search(self, game, ply, time_log, time_writer):
        go = GO.encode('ascii') + b'\n'
        self.commands.write(go)
        self.commands.flush()
        finished_ns = None

        def bestmove_received(line):
            nonlocal finished_ns
            if line.startswith(b'bestmove '):
                finished_ns = monotonic_ns()
                return True
            return False

        # Save the raw clock readings for independent recomputation of wall_ns.
        started_ns = monotonic_ns()
        try:
            self.process.stdin.write(go)
            self.process.stdin.flush()
            lines = self.receive(bestmove_received, f'bestmove for W1 game {game}, ply {ply}')
            return lines, finished_ns - started_ns
        finally:
            time_writer.writerow((game, ply, started_ns, finished_ns))
            time_log.flush()


def parse_completed_iterations(lines):
    iterations = []
    for raw in lines:
        if not raw.startswith(b'info depth '):
            continue
        match = INFO.fullmatch(raw)
        if match is None:
            raise ValueError(f'malformed depth info {raw!r}')
        depth, nodes, elapsed_ms = map(int, match.groups()[:3])
        pv = match[4].split() if match[4] else []
        if depth != len(iterations) + 1:
            raise ValueError(f'nonconsecutive or duplicate completed depth {depth}')
        if iterations and (nodes < iterations[-1][1] or elapsed_ms < iterations[-1][2]):
            raise ValueError(f'depth {depth} has a decreasing cumulative node count or time')
        iterations.append((depth, nodes, elapsed_ms, pv))
    if not iterations:
        raise ValueError('no completed depth info')
    return iterations


def parse_frame(lines, wall_ns):
    best = identity.BESTMOVE.fullmatch(lines[-1])
    if best is None or best[1] == b'0000':
        raise ValueError('missing valid bestmove at a playable root')
    if any(line in (b'uciok', b'readyok') or line.startswith(identity.NET_ACTIVE) for line in lines[:-1]):
        raise ValueError('unexpected protocol handshake during search')
    final_lines = [line for line in lines[:-1] if line.startswith(b'info string softnodes nodes')]
    final = FINAL_NODES.fullmatch(final_lines[0]) if len(final_lines) == 1 else None
    if final is None or final_lines[0] != lines[-2]:
        raise ValueError('expected exactly one final softnodes marker directly before bestmove')
    final_nodes = int(final[1])
    iterations = parse_completed_iterations(lines[:-2])
    depth, last_nodes, time_ms, pv = iterations[-1]
    if not 0 < last_nodes <= final_nodes or wall_ns <= 0:
        raise ValueError(f'invalid last/final nodes or wall time: {last_nodes}/{final_nodes}, {wall_ns}ns')
    if any(identity.MOVE.fullmatch(token) is None for token in pv):
        raise ValueError('invalid move token in last finished PV')
    cap = int(final_nodes > last_nodes)
    prev_depth, prev_nodes = iterations[-2][:2] if len(iterations) >= 2 else ('', '')
    prev2_depth, prev2_nodes = iterations[-3][:2] if len(iterations) >= 3 else ('', '')
    notices = []
    if cap and (final_nodes < HARD_NODES or last_nodes >= SOFT_NODES):
        notices.append('final above last info with unexpected relation to node limits')
    if final_nodes > HARD_NODES or (not cap and final_nodes == HARD_NODES):
        notices.append('final nodes at or above hard cap with an unexpected exact marker relationship')
    if wall_ns < time_ms * 1_000_000:
        notices.append('last engine info time exceeds measured inclusive wall time')
    if not pv or pv[0] != best[1]:
        notices.append('last finished PV head differs from final bestmove or is absent')
    return {
        'last_depth': depth, 'last_nodes': last_nodes, 'last_time_ms': time_ms, 'final_nodes': final_nodes,
        'wall_ns': wall_ns, 'cap': cap, 'prev_depth': prev_depth, 'prev_nodes': prev_nodes,
        'prev2_depth': prev2_depth, 'prev2_nodes': prev2_nodes, 'bestmove': best[1].decode('ascii'),
    }, notices


def write_anomaly(stream, game, ply, fen, severity, message, lines=None):
    row = {'game': game, 'ply': ply, 'root_fen': fen, 'severity': severity, 'message': message}
    if lines is not None:
        row['search_stdout'] = [line.decode('ascii', errors='backslashreplace') for line in lines]
    stream.write(json.dumps(row, ensure_ascii=True, separators=(',', ':')) + '\n')
    stream.flush()


def play(engine, board, start_fen, game, output, clock_log, anomalies, progress):
    writer = csv.DictWriter(output, fieldnames=HEADER, delimiter='\t', lineterminator='\n')
    timer = csv.writer(clock_log, delimiter='\t', lineterminator='\n')
    writer.writeheader()
    timer.writerow(TIME_HEADER)
    moves = progress['moves']
    engine.send('ucinewgame')
    while len(moves) < MOVE_CAP and not board.is_game_over(claim_draw=True):
        ply = len(moves) + 1
        fen = board.fen()
        lines = None
        try:
            engine.send(' '.join(('position fen', start_fen, 'moves', *moves)))
            if engine.ready() != [b'readyok']:
                raise ValueError('unexpected output at per-search ready barrier')
            lines, wall_ns = engine.search(game, ply, clock_log, timer)
            data, notices = parse_frame(lines, wall_ns)
            move = board.parse_uci(data['bestmove'])
            if not move:
                raise ValueError('null move at a playable root')
        except (OSError, RuntimeError, ValueError) as error:
            write_anomaly(anomalies, game, ply, fen, 'error', str(error), lines)
            raise ValueError(f'W1 game {game}, ply {ply}: {error}') from error
        for notice in notices:
            write_anomaly(anomalies, game, ply, fen, 'notice', notice, lines)
            progress['notices'] += 1
        writer.writerow({'game': game, 'ply': ply, 'pieces': board.occupied.bit_count(), 'root_fen': fen, **data})
        output.flush()
        board.push(move)
        moves.append(data['bestmove'])


def run(args):
    if not 41 <= args.game <= 140:
        raise ValueError('game must be the 1-based W1 position index 41 through 140')
    if chess.__version__ != PYTHON_CHESS:
        raise ValueError(f'expected python-chess module {PYTHON_CHESS}; got {chess.__version__}')
    if not 0 < args.timeout <= 120:
        raise ValueError('timeout must be positive and at most 120 seconds')
    engine, net, fixture = (path.resolve(strict=True) for path in (args.engine, args.net, args.fixture))
    if any(char in str(net) for char in '\r\n'):
        raise ValueError('invalid multiline net path')
    if sha(engine) != EXE_SHA or sha(net) != identity.NET_SHA or sha(Path(identity.__file__)) != HELPER_SHA:
        raise ValueError('r15d, net, or identity helper SHA-256 mismatch')
    start_fen = fixture_game(fixture, args.game)
    board = chess.Board(start_fen)
    if not board.is_valid():
        raise ValueError(f'invalid W1 FEN at row {args.game}')
    output = args.output
    output.mkdir(parents=True, exist_ok=False)
    stdout_path = output / 'engine.stdout.txt'
    stderr_path = output / 'engine.stderr.txt'
    start = utc()
    error = None
    progress = {'moves': [], 'notices': 0}
    try:
        with (stdout_path.open('xb') as stdout, stderr_path.open('x+b') as stderr,
              (output / 'engine.commands.txt').open('xb') as commands,
              (output / 'rows.tsv').open('x', encoding='ascii', newline='') as rows,
              (output / 'timings.tsv').open('x', encoding='ascii', newline='') as timings,
              (output / 'anomalies.jsonl').open('x', encoding='ascii') as anomalies):
            with TimedEngine(engine, stdout, stderr, commands, args.timeout) as process:
                process.set_up(net)
                play(process, board, start_fen, args.game, rows, timings, anomalies, progress)
        identity.check_logs(stdout_path, stderr_path)
    except (OSError, RuntimeError, ValueError) as err:
        error = str(err)
    outcome = board.outcome(claim_draw=True)
    metadata = {
        'workload': 'G1', 'build': 'r15d', 'game': args.game, 'exe_sha256': EXE_SHA,
        'net_path': str(net), 'net_sha256': identity.NET_SHA, 'fixture_sha256': FIXTURE_SHA,
        'identity_helper_sha256': HELPER_SHA, 'runner_sha256': sha(Path(__file__)),
        'python_chess': PYTHON_CHESS, 'pc20': identity.PC20, 'soft_nodes': SOFT_NODES, 'hard_nodes': HARD_NODES,
        'ply_cap': MOVE_CAP, 'claim_draw': True, 'started_utc': start, 'finished_utc': utc(), 'error': error,
        'plies': len(progress['moves']), **progress, 'start_fen': start_fen, 'final_fen': board.fen(),
        'stop': ('ERROR' if error else outcome.termination.name if outcome else 'PLY_CAP'),
        'result': outcome.result() if outcome else '*',
        'clock': 'time.monotonic_ns before go pipe write and upon recognizing complete bestmove line',
        'files_sha256': {path.name: sha(path) for path in sorted(output.iterdir())},
    }
    summary = json.dumps(metadata, indent=2) + '\n'
    with (output / 'summary.json').open('x', encoding='ascii') as stream:
        stream.write(summary)
    print(summary, end='', flush=True)
    return int(error is not None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ('engine', 'net', 'fixture', 'output'):
        parser.add_argument('--' + option, type=Path, required=True)
    parser.add_argument('--game', type=int, required=True)
    parser.add_argument('--timeout', type=float, default=30.0)
    args = parser.parse_args()
    try:
        return run(args)
    except (OSError, ValueError) as err:
        parser.exit(1, f'{err}\n')


if __name__ == '__main__':
    raise SystemExit(main())
