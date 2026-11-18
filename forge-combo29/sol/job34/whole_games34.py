#!/usr/bin/env python3
"""Play deterministic Forge games through one UCI process, with both colors."""

import argparse
from collections import Counter
import hashlib
from itertools import islice
import json
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

import chess

PARENT = Path(__file__).resolve().parent.parent
for directory in (PARENT / 'job2', PARENT / 'sol-job2'):
    if (directory / 'run_matrix.py').is_file():
        sys.path.insert(0, str(directory))
        break
else:
    raise SystemExit('Job 2 UCI driver is missing')

from run_matrix import Engine, PC20, Refused, utc_now


BOOK_SHA256 = '7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a'
NET_FINGERPRINT = '30ab43b4ba5db5f3'
MAX_PLIES = 300
NODES_FIELD = re.compile(r'(?:^|\s)nodes ([0-9]+)(?=\s|$)')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read_openings(path, first, last):
    with path.open(encoding='utf-8') as stream:
        openings = [line.rstrip('\r\n') for line in islice(stream, first - 1, last)]
    if len(openings) != last - first + 1:
        raise ValueError(f'book does not contain all physical lines {first} through {last}')
    for index, fen in enumerate(openings, first):
        if len(fen.split()) != 6 or not chess.Board(fen).is_valid():
            raise ValueError(f'invalid six-field FEN on book line {index}: {fen}')
    return openings


def settings(net, quiet_base):
    pc20 = [(name, str(quiet_base) if name == 'LmrQuietBase' else value) for name, value in PC20]
    return [('Threads', '1'), ('Hash', '16'), *pc20, ('NNUEArchFile', str(net)), ('NNUEArch', 'true')]


def setup(engine, options, meta):
    engine.send('uci')
    meta['uci'] = engine.until('uciok')
    meta['id_name'] = next((line for line in meta['uci'] if line.startswith('id name ')), None)
    if meta['id_name'] is None:
        raise RuntimeError('missing engine identification')
    announced = {
        line.removeprefix('option name ').split(' type ', 1)[0]
        for line in meta['uci'] if line.startswith('option name ')
    }
    for name, value in options:
        if name not in announced:
            raise Refused(f'engine did not announce option {name}')
        command = f'setoption name {name} value {value}'
        engine.send(command)
        meta['settings_sent'].append(command)
    engine.send('isready')
    meta['setup_reply'] = engine.until('readyok')
    for prefix, field in (('NNUE v3 loaded:', 'load_line'), ('NNUE v3 active:', 'active_line')):
        lines = [line for line in meta['setup_reply'] if line.startswith(f'info string {prefix}')]
        if len(lines) != 1 or not re.search(rf'\bchecksum {NET_FINGERPRINT}\b', lines[0]):
            raise RuntimeError(f'expected one {prefix} line with checksum {NET_FINGERPRINT}, got {lines}')
        meta[field] = lines[0]
    print(meta['load_line'], flush=True)
    print(meta['active_line'], flush=True)


def play_game(engine, opening, book_line, search, stopped, current, missing_info=None):
    board = chess.Board(opening)
    engine.send('ucinewgame')
    engine.send('isready')
    engine.until('readyok')
    moves, records, info_kinds = [], [], Counter()
    last_info_sample = None
    sum_nodes = 0
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
        position = f'position fen {opening}'
        if moves:
            position += ' moves ' + ' '.join(moves)
        engine.send(position)
        engine.send(search)
        output = engine.until('bestmove')
        if missing_info is None:
            last_info = next((line for line in reversed(output) if line.startswith('info ')), '')
        else:
            last_info = next((line for line in reversed(output) if line.split(maxsplit=1)[:1] == ['info']), '')
        node_fields = NODES_FIELD.findall(last_info)
        words = output[-1].split()
        info_absent = missing_info is not None and not last_info
        if (len(node_fields) != 1 and not info_absent) or len(words) < 2:
            raise RuntimeError(f'missing last-info nodes or bestmove: {output[-4:]}')
        move_text = words[1]
        move = chess.Move.from_uci(move_text)
        if move not in board.legal_moves:
            raise RuntimeError(f'illegal bestmove {move_text} from {position}')
        board.push(move)
        moves.append(move_text)
        if info_absent:
            nodes = 'NA'
            missing_info.append(dict(book_line=book_line, ply=ply, position=position, received=output))
        else:
            nodes = int(node_fields[0])
            sum_nodes += nodes
            kind = 'softnodes' if last_info.startswith('info string softnodes nodes ') else last_info.split(maxsplit=2)[1]
            info_kinds[kind] += 1
            last_info_sample = last_info_sample or last_info
        records.append(f'{book_line} {ply} {move_text} {nodes}\n')
    return records, sum_nodes, ending, info_kinds, last_info_sample


def run(args):
    executable, book, net = (path.resolve(strict=True) for path in (args.engine, args.book, args.net))
    executable_sha, book_sha, net_sha = map(digest, (executable, book, net))
    if args.expected_engine_sha and executable_sha != args.expected_engine_sha:
        raise ValueError(f'engine SHA-256 mismatch: {executable_sha}')
    if book_sha != BOOK_SHA256:
        raise ValueError(f'pinned UHO book SHA-256 mismatch: {book_sha}')
    if '\n' in str(net) or '\r' in str(net):
        raise ValueError('network path must fit a single UCI line')
    work = read_openings(book, args.first, args.last)
    options = settings(net, args.lmr_quiet_base)
    search = f'go {args.mode} 2000'
    sidecar = args.output.with_name(args.output.name + '.meta')
    if args.output.exists() or sidecar.exists():
        raise FileExistsError(f'refusing to overwrite output or sidecar for {args.output}')
    args.output.parent.mkdir(parents=True, exist_ok=True)

    start_ns = time.monotonic_ns()
    info_kinds = Counter()
    meta = {
        'command': sys.argv, 'exe': str(executable), 'exe_sha256': executable_sha,
        'book': str(book), 'book_sha256': book_sha, 'external_net_file': str(net),
        'external_net_sha256': net_sha, 'external_net_checksum_expected': NET_FINGERPRINT,
        'python_chess': chess.__version__, 'search': search, 'settings_sent': [],
        'reset_commands': ['ucinewgame', 'isready'], 'reset_frequency': 'once per game',
        'position_command': 'position fen <book line> [moves <all preceding UCI moves>]',
        'record_format': 'physical book line (1-based), ply (0-based), bestmove, nodes from last literal info line',
        'max_plies': MAX_PLIES, 'claim_draw': True, 'first_line': args.first, 'last_line': args.last,
        'games_requested': len(work), 'games_completed': 0, 'positions_completed': 0,
        'last_info_nodes_sum': 0, 'info_line_kinds': info_kinds, 'games': [],
        'deadline_epoch': args.deadline, 'start_utc': utc_now(), 'status': 'incomplete',
    }
    if args.record_missing_info:
        meta['record_format'] += ' (NA when no info line was received)'
        meta['missing_info_count'] = 0
        meta['missing_info'] = []
    current = {'book_line': None, 'ply': None}
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
                    for book_line, fen in enumerate(work, args.first):
                        if stopped():
                            break
                        current = {'book_line': book_line, 'ply': None}
                        game_start = time.monotonic_ns()
                        missing_info = [] if args.record_missing_info else None
                        result = play_game(engine, fen, book_line, search, stopped, current, missing_info)
                        if result is None:
                            break
                        records, sum_nodes, ending, kinds, sample = result
                        rows.writelines(records)
                        rows.flush()
                        info_kinds.update(kinds)
                        if sample and 'first_last_info_line' not in meta:
                            meta['first_last_info_line'] = sample
                        meta['games'].append(dict(book_line=book_line, plies=len(records), termination=ending,
                                                   end_utc=utc_now(), elapsed_ns=time.monotonic_ns() - game_start))
                        meta['games_completed'] += 1
                        meta['positions_completed'] += len(records)
                        meta['last_info_nodes_sum'] += sum_nodes
                        if missing_info:
                            meta['missing_info_count'] += len(missing_info)
                            meta['missing_info'].extend(missing_info)
                        if meta['games_completed'] % 25 == 0:
                            print(f"{args.output.name}: completed {meta['games_completed']}/{len(work)} games through book line {book_line}", flush=True)
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
    if args.record_missing_info:
        print(f"{args.output.name}: {meta['missing_info_count']} records with no info line", flush=True)
    return {'complete': 0, 'cut': 130}.get(meta['status'], 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('engine', 'book', 'net', 'output'):
        parser.add_argument(name, type=Path)
    parser.add_argument('mode', choices=('softnodes', 'nodes'))
    parser.add_argument('first', type=int, help='first physical book line, inclusive and one-based')
    parser.add_argument('last', type=int, help='last physical book line, inclusive and one-based')
    parser.add_argument('--lmr-quiet-base', type=int, choices=(60, 93), default=93)
    parser.add_argument('--expected-engine-sha')
    parser.add_argument('--deadline', type=float, help='absolute UTC epoch for the shared run cutoff')
    parser.add_argument('--timeout', type=float, default=15, help='seconds allowed per UCI response')
    parser.add_argument('--record-missing-info', action='store_true', help='record NA only when bestmove arrives without any info line')
    args = parser.parse_args()
    if not 1 <= args.first <= args.last or args.timeout <= 0:
        parser.error('line range and timeout must be positive')
    return run(args)


if __name__ == '__main__':
    raise SystemExit(main())
