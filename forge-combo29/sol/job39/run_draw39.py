#!/usr/bin/env python3
"""Run one pinned Forge settings draw using the Job 35 game driver."""

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

import chess

from generate_draws39 import NAMES, draw_values


ROOT = Path(__file__).resolve().parent
for directory in (ROOT.parent / 'job35', ROOT.parent / 'sol-job35'):
    if (directory / 'whole_games35.py').is_file():
        sys.path.insert(0, str(directory))
        break
else:
    raise SystemExit('Job 35 whole-game driver is missing')

import whole_games35 as job35
from whole_games34 import Engine, MAX_PLIES, NET_FINGERPRINT, Refused, digest, settings, utc_now


ENGINE_SHA256 = {
    'r15d': '9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671',
    'kF': 'c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb',
}
NET_SHA256 = 'c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7'
SEARCH = {'hard': 'go nodes 20000', 'soft': 'go softnodes 2000'}
ERROR_LINE = re.compile(r'\bERROR\b')


class Cut(RuntimeError):
    """The batch deadline or a stop signal interrupted this run."""


class Hung(RuntimeError):
    """The engine exceeded its response timeout."""


class Crashed(RuntimeError):
    """The engine closed its UCI pipe before responding."""


class LoggedEngine(Engine):
    """Record the setup exchange and retain the current reply for failures."""

    def __init__(self, executable, timeout, stopped, setup_log):
        super().__init__(executable, timeout)
        self.stopped = stopped
        self.setup_log = setup_log
        self.last_command = None
        self.last_reply = []

    def send(self, command):
        reason = self.stopped()
        if reason and command != 'quit':
            raise Cut(reason)
        self.last_command = command
        if self.setup_log is not None:
            self.setup_log.write(f'> {command}\n')
        try:
            super().send(command)
        except BrokenPipeError as error:
            raise Crashed(f'engine closed stdin while sending {command!r}') from error

    def until(self, token):
        self.last_reply = []
        deadline = time.monotonic() + self.timeout
        while True:
            if reason := self.stopped():
                raise Cut(reason)
            newline = self.unread.find(b'\n')
            if newline == -1:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise Hung(f'timeout waiting for {token}')
                if not self.selector.select(min(remaining, 0.25)):
                    continue
                chunk = os.read(self.process.stdout.fileno(), 65536)
                if not chunk:
                    if self.unread:
                        self.last_reply.append(self.unread.decode('utf-8', errors='replace'))
                        if self.setup_log is not None:
                            self.setup_log.write(f'< {self.last_reply[-1]}\n')
                    raise Crashed(f'engine closed stdout waiting for {token}')
                self.unread.extend(chunk)
                continue
            line = self.unread[:newline].decode('utf-8', errors='replace').rstrip('\r')
            del self.unread[:newline + 1]
            self.last_reply.append(line)
            if self.setup_log is not None:
                self.setup_log.write(f'< {line}\n')
            lower = line.lower()
            if 'unknown option' in lower or 'invalid value' in lower or ERROR_LINE.search(line):
                raise Refused(line)
            if lower.startswith(('info string invalid fen:', 'info string illegal move ')):
                raise RuntimeError(line)
            if line == token or line.startswith(token + ' '):
                return self.last_reply


def selected_draw(path, number):
    lines = path.read_text(encoding='ascii').splitlines()
    if len(lines) != 100:
        raise ValueError(f'expected 100 draw rows in {path}, got {len(lines)}')
    fields = lines[number - 1].split('\t')
    values = tuple(map(int, fields[1:]))
    if fields[0] != str(number) or values != draw_values(number):
        raise ValueError(f'draw {number} differs from the pinned Python generator')
    return list(zip(NAMES, map(str, values), strict=True))


def initialize(engine, options, meta):
    engine.send('uci')
    uci = engine.until('uciok')
    meta['id_name'] = next((line for line in uci if line.startswith('id name ')), None)
    if meta['id_name'] is None:
        raise RuntimeError('missing engine identification')
    announced = {
        line.removeprefix('option name ').split(' type ', 1)[0]
        for line in uci if line.startswith('option name ')
    }
    setup_replies = []
    for name, value in options:
        if name not in announced:
            raise Refused(f'engine did not announce option {name}')
        command = f'setoption name {name} value {value}'
        engine.send(command)
        meta['settings_sent'].append(command)
        engine.send('isready')
        meta['settings_ready_count'] += 1
        setup_replies.extend(engine.until('readyok'))
    for prefix, field in (('NNUE v3 loaded:', 'load_line'), ('NNUE v3 active:', 'active_line')):
        matching = [line for line in setup_replies if line.startswith(f'info string {prefix}')]
        if len(matching) != 1 or not re.search(rf'\bchecksum {NET_FINGERPRINT}\b', matching[0]):
            raise RuntimeError(f'expected one {prefix} line with checksum {NET_FINGERPRINT}, got {matching}')
        meta[field] = matching[0]
    engine.setup_log = None
    print(meta['load_line'], flush=True)
    print(meta['active_line'], flush=True)


def run(args):
    if chess.__version__ != '1.11.2':
        raise RuntimeError(f'expected python-chess 1.11.2, got {chess.__version__}')
    engine_path = (args.artifacts / args.build / 'forge').resolve(strict=True)
    net = (args.artifacts / 'net768.nnue').resolve(strict=True)
    engine_sha, net_sha = digest(engine_path), digest(net)
    if engine_sha != ENGINE_SHA256[args.build] or net_sha != NET_SHA256:
        raise ValueError(f'Job 34 pin mismatch: executable {engine_sha}, net {net_sha}')
    if '\n' in str(net) or '\r' in str(net):
        raise ValueError('network path must fit a single UCI command')
    draw_options = [] if args.draw == 'pc20' else selected_draw(args.draws, int(args.draw))
    if args.lmr60:
        draw_options = [(name, '60' if name == 'LmrQuietBase' else value) for name, value in draw_options]
    options = [*settings(net, 93), *draw_options]
    job35.SEARCH = SEARCH[args.mode]
    info_kinds = Counter()
    start_ns = time.monotonic_ns()
    meta = {
        'command': sys.argv, 'build': args.build, 'draw': args.draw if args.draw == 'pc20' else int(args.draw),
        'draws_sha256': digest(args.draws) if draw_options else None, 'lmr60': args.lmr60,
        'draw_settings': dict(draw_options), 'mode': args.mode, 'search': job35.SEARCH,
        'exe': str(engine_path), 'exe_sha256': engine_sha,
        'external_net_file': str(net), 'external_net_sha256': net_sha,
        'external_net_checksum_expected': NET_FINGERPRINT, 'python_chess': chess.__version__,
        'reset_commands': ['ucinewgame', 'isready'], 'reset_frequency': 'once per game',
        'position_command': 'position startpos moves <all preceding UCI moves including random opening>',
        'record_format': 'game identifier, absolute ply (0-based), bestmove, nodes from last literal info line',
        'settings_sent': [], 'settings_ready_count': 0, 'max_plies': MAX_PLIES, 'claim_draw': True,
        'first_game': args.first, 'last_game': args.last, 'games_requested': args.last - args.first + 1,
        'games_completed': 0, 'positions_completed': 0, 'last_info_nodes_sum': 0,
        'info_line_kinds': info_kinds, 'games': [], 'deadline_epoch': args.deadline,
        'start_utc': utc_now(), 'status': 'incomplete',
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
    meta_path = args.output / 'run.json'
    old_signals = {sig: signal.signal(sig, on_signal) for sig in (signal.SIGINT, signal.SIGTERM)}
    engine = None
    try:
        with records_path.open('x', encoding='ascii', newline='\n') as rows, setup_path.open('x', encoding='utf-8') as log:
            if reason := stopped():
                raise Cut(reason)
            with LoggedEngine(engine_path, args.timeout, stopped, log) as engine:
                initialize(engine, options, meta)
                for game in range(args.first, args.last + 1):
                    if reason := stopped():
                        raise Cut(reason)
                    current = {'game': game, 'ply': None}
                    opening = job35.generated_opening(game)
                    opening_moves = list(opening[1])
                    current['opening_moves'] = opening_moves
                    if opening[2] != 'ready':
                        engine.send('ucinewgame')
                        engine.send('isready')
                        engine.until('readyok')
                    game_start = time.monotonic_ns()
                    outcome = job35.play_game(engine, opening, game, stopped, current)
                    if outcome is None:
                        raise Cut(stopped() or 'interrupted')
                    records, sum_nodes, ending, kinds, sample = outcome
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
                    meta['last_info_nodes_sum'] += sum_nodes
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
        meta_path.write_text(json.dumps(meta, indent=2) + '\n', encoding='utf-8')
        for sig, previous in old_signals.items():
            signal.signal(sig, previous)
    print(f'{args.output.name}: {meta["status"]}, {meta["games_completed"]}/{meta["games_requested"]} games, '
          f'{meta["positions_completed"]} records', flush=True)
    return {'complete': 0, 'cut': 130, 'refused': 2, 'crash': 3, 'hang': 4}.get(meta['status'], 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', required=True, choices=ENGINE_SHA256)
    parser.add_argument('--draw', required=True, help='draw number 1–100, or pc20')
    parser.add_argument('--first', required=True, type=int)
    parser.add_argument('--last', required=True, type=int)
    parser.add_argument('--mode', required=True, choices=SEARCH)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--deadline', required=True, type=float, help='UTC epoch seconds')
    parser.add_argument('--lmr60', action='store_true', help='override the selected draw LmrQuietBase for C39')
    parser.add_argument('--timeout', type=float, default=15, help='UCI response timeout in seconds')
    parser.add_argument('--draws', type=Path, default=ROOT / 'draws.tsv')
    parser.add_argument('--artifacts', type=Path, default=ROOT.parent / 'sol-job34')
    args = parser.parse_args()
    if args.draw != 'pc20' and (not args.draw.isdecimal() or not 1 <= int(args.draw) <= 100):
        parser.error('--draw must be 1–100 or pc20')
    if args.draw == 'pc20' and args.lmr60:
        parser.error('--lmr60 applies only to a draw')
    if not 1 <= args.first <= args.last or args.timeout <= 0:
        parser.error('game range and timeout must be positive')
    return run(args)


if __name__ == '__main__':
    raise SystemExit(main())
