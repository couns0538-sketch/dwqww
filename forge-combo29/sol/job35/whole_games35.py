#!/usr/bin/env python3
"""Replay Job 35's seeded eight-ply openings in one UCI process per build."""

import argparse
from collections import Counter
import json
from pathlib import Path
import random
import signal
import subprocess
import sys
import time

import chess

PARENT = Path(__file__).resolve().parent.parent
for directory in (PARENT / 'job34', PARENT / 'sol-job34'):
    if (directory / 'whole_games34.py').is_file():
        sys.path.insert(0, str(directory))
        break
else:
    raise SystemExit('Job 34 whole-game driver is missing')

from whole_games34 import Engine, MAX_PLIES, NET_FINGERPRINT, NODES_FIELD, Refused, digest, settings, setup, utc_now


OPENING_PLIES = 8
SEARCH = 'go softnodes 2000'


def generated_opening(game):
    board = chess.Board()
    rng = random.Random(game)
    moves = []
    for _ in range(OPENING_PLIES):
        move = rng.choice(list(board.legal_moves))
        board.push(move)
        moves.append(move.uci())
        if board.is_game_over(claim_draw=True):
            return board, moves, board.outcome(claim_draw=True).termination.name.lower()
    return board, moves, 'ready'


def read_openings(path, first, last):
    data = path.read_bytes()
    rows = data.decode('ascii').splitlines(keepends=True)
    if len(rows) != last - first + 1:
        raise ValueError(f'expected one opening for each game {first} through {last}')
    entries = []
    for game, row in zip(range(first, last + 1), rows, strict=True):
        opening = generated_opening(game)
        _, moves, status = opening
        expected = f"{game}\t{' '.join(moves)}\t{status}\n"
        if row != expected:
            raise ValueError(f'opening fixture game {game} differs from the seeded opening: {row!r} versus {expected!r}')
        entries.append(opening)
    return entries


def play_game(engine, opening, game, stopped, current):
    board, moves, status = opening
    records, info_kinds = [], Counter()
    last_info_sample = None
    sum_nodes = 0
    if status != 'ready':
        return records, sum_nodes, status, info_kinds, last_info_sample

    engine.send('ucinewgame')
    engine.send('isready')
    engine.until('readyok')
    while True:
        if board.is_game_over(claim_draw=True):
            ending = board.outcome(claim_draw=True).termination.name.lower()
            break
        if len(moves) == MAX_PLIES:
            ending = '300_ply_limit'
            break
        if stopped():
            return None
        ply = len(moves)
        current['ply'] = ply
        position = 'position startpos moves ' + ' '.join(moves)
        engine.send(position)
        engine.send(SEARCH)
        output = engine.until('bestmove')
        last_info = next((line for line in reversed(output) if line.startswith('info ')), '')
        node_fields = NODES_FIELD.findall(last_info)
        words = output[-1].split()
        if len(node_fields) != 1 or len(words) < 2:
            raise RuntimeError(f'missing last-info nodes or bestmove: {output[-4:]}')
        move_text, nodes = words[1], int(node_fields[0])
        move = chess.Move.from_uci(move_text)
        if move not in board.legal_moves:
            raise RuntimeError(f'illegal bestmove {move_text} from {position}')
        board.push(move)
        moves.append(move_text)
        records.append(f'{game} {ply} {move_text} {nodes}\n')
        sum_nodes += nodes
        kind = 'softnodes' if last_info.startswith('info string softnodes nodes ') else last_info.split(maxsplit=2)[1]
        info_kinds[kind] += 1
        last_info_sample = last_info_sample or last_info
    return records, sum_nodes, ending, info_kinds, last_info_sample


def run(args):
    if chess.__version__ != '1.11.2':
        raise RuntimeError(f'expected python-chess 1.11.2, got {chess.__version__}')
    executable, openings, net = (path.resolve(strict=True) for path in (args.engine, args.openings, args.net))
    executable_sha, openings_sha, net_sha = map(digest, (executable, openings, net))
    if args.expected_engine_sha and executable_sha != args.expected_engine_sha:
        raise ValueError(f'engine SHA-256 mismatch: {executable_sha}')
    if '\n' in str(net) or '\r' in str(net):
        raise ValueError('network path must fit a single UCI line')
    work = read_openings(openings, args.first, args.last)
    options = settings(net, args.lmr_quiet_base)
    sidecar = args.output.with_name(args.output.name + '.meta')
    if args.output.exists() or sidecar.exists():
        raise FileExistsError(f'refusing to overwrite output or sidecar for {args.output}')
    args.output.parent.mkdir(parents=True, exist_ok=True)

    start_ns = time.monotonic_ns()
    info_kinds = Counter()
    meta = {
        'command': sys.argv, 'exe': str(executable), 'exe_sha256': executable_sha,
        'opening_fixture': str(openings), 'openings_sha256': openings_sha, 'external_net_file': str(net),
        'external_net_sha256': net_sha, 'external_net_checksum_expected': NET_FINGERPRINT,
        'python_chess': chess.__version__, 'search': SEARCH, 'settings_sent': [],
        'reset_commands': ['ucinewgame', 'isready'], 'reset_frequency': 'once per searched game',
        'position_command': 'position startpos moves <all preceding UCI moves including the random opening>',
        'record_format': 'game (1-based), absolute ply (0-based), bestmove, nodes from last literal info line',
        'max_plies': MAX_PLIES, 'claim_draw': True, 'first_game': args.first, 'last_game': args.last,
        'games_requested': len(work), 'games_completed': 0, 'positions_completed': 0,
        'last_info_nodes_sum': 0, 'info_line_kinds': info_kinds, 'games': [],
        'deadline_epoch': args.deadline, 'start_utc': utc_now(), 'status': 'incomplete',
    }
    current = {'game': None, 'ply': None}
    requested_signal = None

    def on_signal(signum, _frame):
        nonlocal requested_signal
        requested_signal = signal.Signals(signum).name

    def stopped():
        return requested_signal or (args.deadline is not None and time.time() >= args.deadline)

    old_signals = {sig: signal.signal(sig, on_signal) for sig in (signal.SIGINT, signal.SIGTERM)}
    with args.output.open('x', encoding='ascii', newline='\n') as rows, sidecar.open('x', encoding='utf-8') as metadata:
        engine = None
        try:
            if not stopped():
                with Engine(executable, args.timeout) as engine:
                    setup(engine, options, meta)
                    for game, opening in enumerate(work, args.first):
                        if stopped():
                            break
                        current = {'game': game, 'ply': None}
                        opening_plies = len(opening[1])
                        game_start = time.monotonic_ns()
                        result = play_game(engine, opening, game, stopped, current)
                        if result is None:
                            break
                        records, sum_nodes, ending, kinds, sample = result
                        rows.writelines(records)
                        rows.flush()
                        info_kinds.update(kinds)
                        if sample and 'first_last_info_line' not in meta:
                            meta['first_last_info_line'] = sample
                        meta['games'].append(dict(game=game, opening_plies=opening_plies, plies=len(records),
                                                   termination=ending, end_utc=utc_now(),
                                                   elapsed_ns=time.monotonic_ns() - game_start))
                        meta['games_completed'] += 1
                        meta['positions_completed'] += len(records)
                        meta['last_info_nodes_sum'] += sum_nodes
                        if meta['games_completed'] % 25 == 0:
                            print(f"{args.output.name}: completed {meta['games_completed']}/{len(work)} games through game {game}", flush=True)
            if meta['games_completed'] == len(work):
                meta['status'] = 'complete'
            elif stopped():
                meta.update(status='cut', stop_reason=requested_signal or 'deadline', stopped_at=current)
        except (Refused, RuntimeError, ValueError, OSError, subprocess.SubprocessError) as error:
            meta.update(status='refused' if isinstance(error, Refused) else 'incomplete', error=str(error),
                        stopped_at=current)
            print(f"{args.output.name}: {meta['status']} at {current}: {error}", file=sys.stderr)
        finally:
            rows.flush()
            meta.update(end_utc=utc_now(), elapsed_ns=time.monotonic_ns() - start_ns,
                        engine_exit=None if engine is None else engine.process.returncode,
                        records_sha256=digest(args.output))
            json.dump(meta, metadata, indent=2)
            metadata.write('\n')
            for sig, previous in old_signals.items():
                signal.signal(sig, previous)
    print(f"{args.output.name}: {meta['status']}, {meta['games_completed']}/{len(work)} complete games, "
          f"{meta['positions_completed']} records, {meta['last_info_nodes_sum']} last-info nodes", flush=True)
    return {'complete': 0, 'cut': 130}.get(meta['status'], 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('engine', 'openings', 'net', 'output'):
        parser.add_argument(name, type=Path)
    parser.add_argument('first', type=int, help='first game seed, inclusive and one-based')
    parser.add_argument('last', type=int, help='last game seed, inclusive and one-based')
    parser.add_argument('--lmr-quiet-base', type=int, choices=(60, 93), default=93)
    parser.add_argument('--expected-engine-sha')
    parser.add_argument('--deadline', type=float, help='absolute UTC epoch for the shared run cutoff')
    parser.add_argument('--timeout', type=float, default=15, help='seconds allowed per UCI response')
    args = parser.parse_args()
    if not 1 <= args.first <= args.last or args.timeout <= 0:
        parser.error('game range and timeout must be positive')
    return run(args)


if __name__ == '__main__':
    raise SystemExit(main())
