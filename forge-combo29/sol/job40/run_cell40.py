#!/usr/bin/env python3
"""Play one fixed-limit Job 40 run on the pinned r15d build."""

import argparse
from collections import Counter
import json
from math import isfinite
from pathlib import Path
import signal
import subprocess
import sys
import time

import chess


ROOT = Path(__file__).resolve().parent
for directory in (ROOT.parent / 'job39', ROOT.parent / 'sol-job39'):
    if (directory / 'run_draw39.py').is_file():
        sys.path.insert(0, str(directory))
        break
else:
    raise SystemExit('Job 39 UCI driver is missing')

from run_draw39 import (
    ENGINE_SHA256, MAX_PLIES, NET_FINGERPRINT, NET_SHA256, SEARCH, Crashed, Cut,
    Hung, LoggedEngine, Refused, digest, initialize, job35, settings, utc_now,
)


LIMITS = {'N2': ('hard', 410001), 'N1': ('soft', 400001)}
GAMES = 20
EXIT_STATUS = {'complete': 0, 'cut': 130, 'refused': 2, 'crash': 3, 'hang': 4}


def run(args):
    if chess.__version__ != '1.11.2':
        raise RuntimeError(f'expected python-chess 1.11.2, got {chess.__version__}')
    executable = (args.artifacts / 'r15d' / 'forge').resolve(strict=True)
    net = (args.artifacts / 'net768.nnue').resolve(strict=True)
    engine_sha, net_sha = digest(executable), digest(net)
    if engine_sha != ENGINE_SHA256['r15d'] or net_sha != NET_SHA256:
        raise ValueError(f'Job 34 artifact pin mismatch: executable {engine_sha}, net {net_sha}')
    if '\n' in str(net) or '\r' in str(net):
        raise ValueError('network path must fit a single UCI line')

    mode, first = LIMITS[args.limit]
    last = first + GAMES - 1
    job35.SEARCH = SEARCH[mode]
    options = settings(net, 93)
    option = None
    if args.option:
        name, value = args.option
        options.append((name, str(value)))
        option = {'name': name, 'value': value}

    start_ns = time.monotonic_ns()
    info_kinds = Counter()
    meta = {
        'command': sys.argv, 'build': 'r15d', 'limit': args.limit, 'option': option,
        'mode': mode, 'search': job35.SEARCH, 'exe': str(executable), 'exe_sha256': engine_sha,
        'external_net_file': str(net), 'external_net_sha256': net_sha,
        'external_net_checksum_expected': NET_FINGERPRINT, 'python_chess': chess.__version__,
        'reset_commands': ['ucinewgame', 'isready'], 'reset_frequency': 'once per game',
        'position_command': 'position startpos moves <all preceding UCI moves including random opening>',
        'record_format': 'game identifier, absolute ply (0-based), bestmove, nodes from last literal info line',
        'settings_sent': [], 'settings_ready_count': 0, 'max_plies': MAX_PLIES, 'claim_draw': True,
        'first_game': first, 'last_game': last, 'games_requested': GAMES, 'games_completed': 0,
        'positions_completed': 0, 'last_info_nodes_sum': 0, 'info_line_kinds': info_kinds, 'games': [],
        'deadline_epoch': args.deadline, 'start_utc': utc_now(), 'status': 'incomplete',
    }
    current = {'game': None, 'ply': None}
    requested_signal = None

    def on_signal(signum, _frame):
        nonlocal requested_signal
        requested_signal = signal.Signals(signum).name

    def stopped():
        return requested_signal or ('deadline' if time.time() >= args.deadline else None)

    args.output.mkdir(parents=True, exist_ok=False)
    records_path = args.output / 'records.txt'
    setup_path = args.output / 'uci-setup.txt'
    old_signals = {sig: signal.signal(sig, on_signal) for sig in (signal.SIGINT, signal.SIGTERM)}
    engine = None
    try:
        with records_path.open('x', encoding='ascii', newline='\n') as rows, setup_path.open('x', encoding='utf-8') as log:
            if reason := stopped():
                raise Cut(reason)
            with LoggedEngine(executable, args.timeout, stopped, log) as engine:
                initialize(engine, options, meta)
                for game in range(first, last + 1):
                    if reason := stopped():
                        raise Cut(reason)
                    opening = job35.generated_opening(game)
                    opening_moves = list(opening[1])
                    current = {'game': game, 'ply': None, 'opening_moves': opening_moves}
                    if opening[2] != 'ready':
                        engine.send('ucinewgame')
                        engine.send('isready')
                        engine.until('readyok')
                    game_start = time.monotonic_ns()
                    outcome = job35.play_game(engine, opening, game, stopped, current)
                    if outcome is None:
                        raise Cut(stopped() or 'interrupted')
                    records, nodes, ending, kinds, sample = outcome
                    rows.writelines(records)
                    rows.flush()
                    info_kinds.update(kinds)
                    if sample and 'first_last_info_line' not in meta:
                        meta['first_last_info_line'] = sample
                    meta['games'].append(dict(game=game, opening_plies=len(opening_moves), opening_moves=opening_moves,
                                              plies=len(records), termination=ending, end_utc=utc_now(),
                                              elapsed_ns=time.monotonic_ns() - game_start))
                    meta['games_completed'] += 1
                    meta['positions_completed'] += len(records)
                    meta['last_info_nodes_sum'] += nodes
            meta['status'] = 'complete'
    except Cut as error:
        meta.update(status='cut', stop_reason=str(error))
    except Refused as error:
        meta.update(status='refused', error=str(error))
    except (Hung, subprocess.TimeoutExpired) as error:
        meta.update(status='hang', error=str(error))
    except Crashed as error:
        meta.update(status='crash', error=str(error))
    except (RuntimeError, ValueError, OSError, subprocess.SubprocessError) as error:
        meta['error'] = str(error)
    finally:
        if meta['status'] != 'complete':
            meta.update(stopped_at=current, last_command=None if engine is None else engine.last_command,
                        last_reply=[] if engine is None else engine.last_reply)
        meta.update(end_utc=utc_now(), elapsed_ns=time.monotonic_ns() - start_ns,
                    engine_exit=None if engine is None else engine.process.returncode,
                    records_sha256=digest(records_path), uci_setup_sha256=digest(setup_path))
        (args.output / 'run.json').write_text(json.dumps(meta, indent=2) + '\n', encoding='utf-8')
        for sig, previous in old_signals.items():
            signal.signal(sig, previous)
    print(f'{args.output.name}: {meta["status"]}, {meta["games_completed"]}/{GAMES} games, '
          f'{meta["positions_completed"]} records', flush=True)
    return EXIT_STATUS.get(meta['status'], 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('limit', choices=LIMITS)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--deadline', required=True, type=float, help='UTC epoch seconds')
    parser.add_argument('--option', nargs=2, metavar=('NAME', 'VALUE'), help='one extra UCI spin setting')
    parser.add_argument('--artifacts', type=Path, default=ROOT.parent / 'sol-job34')
    parser.add_argument('--timeout', type=float, default=15, help='UCI response timeout in seconds')
    args = parser.parse_args()
    if not isfinite(args.deadline) or args.deadline <= 0 or not isfinite(args.timeout) or args.timeout <= 0:
        parser.error('deadline and timeout must be positive finite numbers')
    if args.option:
        name, value = args.option
        if not name.isascii() or not name.isidentifier():
            parser.error('option name must be an ASCII identifier')
        try:
            args.option = (name, int(value))
        except ValueError:
            parser.error('option value must be an integer')
    return run(args)


if __name__ == '__main__':
    raise SystemExit(main())
