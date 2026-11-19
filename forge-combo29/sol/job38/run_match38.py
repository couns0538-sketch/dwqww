#!/usr/bin/env python3
"""Run one Job 38 fastchess comparison at a pinned hard node limit."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shlex
import signal
import subprocess
import sys
from tempfile import TemporaryDirectory


HERE = Path(__file__).resolve().parent
JOB36 = Path('/workspace/work/sol-job36')
sys.path.insert(0, str(JOB36))

from run_match36 import (
    BOOK, BOOK_SHA, FASTCHESS, FASTCHESS_REVISION, FASTCHESS_SHA, FASTCHESS_VERSION,
    KF, KF_SHA, NET, PC20, PC20_SHA, R15D, R15D_SHA, build_settings, preflight,
    stop_request, wait_for_match,
)
from run_pins36 import NET_CHECKSUM, NET_SHA, SETTING, digest, require, utc_now


MATCHES = {
    'K38a': ('r15d', 20000, 4001, 10, 93),
    'K38b': ('r15d', 20000, 4001, 10, 93),
    'C38': ('r15d', 20000, 4001, 10, 60),
    'G20-r15d': ('r15d', 20000, 4011, 300, 93),
    'G20-kF': ('kF', 20000, 4011, 300, 93),
    'G50-r15d': ('r15d', 50000, 4311, 150, 93),
    'G50-kF': ('kF', 50000, 4311, 150, 93),
    'G250-r15d': ('r15d', 250000, 4461, 24, 93),
    'G250-kF': ('kF', 250000, 4461, 24, 93),
}
ENGINES = {'r15d': (R15D, R15D_SHA), 'kF': (KF, KF_SHA)}
SIDES = ('X1', 'X2')


def fastchess_command(engine, settings, pgn, nodes, opening_start, games, workers):
    options = []
    for setting in settings:
        match = SETTING.fullmatch(setting)
        require(match is not None, f'malformed setting {setting}')
        name, value = match.groups()
        options.append(f'option.{name}={value}')
    command = [str(FASTCHESS)]
    for side in SIDES:
        command.extend(('-engine', f'cmd={engine}', f'name={side}', *options))
    command.extend((
        '-each', 'proto=uci', f'nodes={nodes}', 'restart=on',
        '-openings', f'file={BOOK}', 'format=epd', 'order=sequential', f'start={opening_start}',
        '-rounds', str(games), '-games', '1', '-noswap',
        '-concurrency', str(workers), '-autosaveinterval', '0',
        '-pgnout', f'file={pgn}', 'notation=san', 'append=false', 'nodes=true', 'min=false',
    ))
    return command


def run(args):
    build, nodes, opening_start, games, lmr = MATCHES[args.match]
    engine, engine_sha = ENGINES[build]
    nproc = int(subprocess.check_output(['nproc'], text=True))
    workers = nproc - 1
    require(workers > 0, f'nproc {nproc} leaves no eligible game workers')
    output = args.output.resolve()
    pgn, raw_path, sidecar = (output / f'{args.match}.{suffix}' for suffix in ('pgn', 'out', 'meta'))
    for path in (pgn, raw_path, sidecar):
        require(not path.exists(), f'refusing to overwrite {path}')
    pc20 = PC20.read_bytes()
    pc20_sha = sha256(pc20).hexdigest()
    require(pc20_sha == PC20_SHA, f'PC20 SHA-256 {pc20_sha}, expected {PC20_SHA}')
    settings = build_settings(pc20)
    original = 'setoption name LmrQuietBase value 93'
    require(settings.count(original) == 1, 'expected one PC20 LmrQuietBase 93 setting')
    settings[settings.index(original)] = f'setoption name LmrQuietBase value {lmr}'
    command = fastchess_command(engine, settings, pgn, nodes, opening_start, games, workers)
    if args.print_command:
        print(shlex.join(command))
        return 0

    output.mkdir(parents=True, exist_ok=True)
    meta = {
        'match': args.match, 'build': build, 'nodes': nodes, 'lmr_quiet_base': lmr,
        'opening_start': opening_start, 'opening_end': opening_start + games - 1,
        'games_requested': games, 'command': sys.argv, 'fastchess_command': command,
        'fastchess_revision': FASTCHESS_REVISION, 'restart': True, 'pgn_nodes': True,
        'adjudication': False, 'recover': False, 'timecontrol': None,
        'engine_names': list(SIDES), 'x1_always_white': True, 'opening_order': 'sequential',
        'nproc': nproc, 'concurrency': workers, 'cpu_max': Path('/sys/fs/cgroup/cpu.max').read_text().strip(),
        'settings': settings, 'pc20_sha256': pc20_sha, 'net_checksum': NET_CHECKSUM,
        'deadline_epoch': args.deadline, 'start_utc': utc_now(), 'status': 'failed',
    }
    caught_signal = None

    def receive_signal(signum, _frame):
        nonlocal caught_signal
        if caught_signal is None:
            caught_signal = signal.Signals(signum).name

    def should_stop():
        return stop_request(args.deadline, caught_signal)

    handlers = {sig: signal.signal(sig, receive_signal) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        with sidecar.open('x', encoding='utf-8') as metadata, raw_path.open('x', encoding='utf-8') as raw:
            try:
                pins = {
                    'exe': (engine, engine_sha), 'net': (NET, NET_SHA),
                    'book': (BOOK, BOOK_SHA), 'fastchess': (FASTCHESS, FASTCHESS_SHA),
                }
                for field, (path, expected) in pins.items():
                    meta[field] = str(path)
                    actual = digest(path)
                    meta[f'{field}_sha256'] = actual
                    require(actual == expected, f'{field} SHA-256 {actual}, expected {expected}')
                version = subprocess.check_output(
                    [str(FASTCHESS), '--version'], text=True, stderr=subprocess.STDOUT, timeout=10,
                ).strip()
                meta['fastchess_version'] = version
                require(version == FASTCHESS_VERSION, f'fastchess version {version!r}, expected {FASTCHESS_VERSION!r}')
                raw.write(f'{version}\n')
                for side in SIDES:
                    if should_stop():
                        break
                    meta[f'nnue_active_{side.lower()}'] = preflight(side, engine, settings, raw)
                if reason := should_stop():
                    meta['stop_reason'] = reason
                else:
                    raw.write(f'{utc_now()} fastchess argv\n{shlex.join(command)}\n\nFastchess output\n')
                    raw.flush()
                    with TemporaryDirectory(prefix=f'.{args.match}-fastchess-', dir=output) as cwd:
                        meta['match_start_utc'] = utc_now()
                        child = subprocess.Popen(
                            command, stdout=raw, stderr=subprocess.STDOUT, start_new_session=True, cwd=cwd,
                        )
                        meta['fastchess_pid'] = child.pid
                        meta['fastchess_exit'] = wait_for_match(child, should_stop, meta)
                        meta['match_end_utc'] = utc_now()
                if 'stop_reason' in meta:
                    meta['status'] = 'interrupted'
                else:
                    require(meta['fastchess_exit'] == 0, f"fastchess exited {meta['fastchess_exit']}")
                    require(pgn.is_file() and pgn.stat().st_size, 'fastchess produced no nonempty PGN')
                    meta['status'] = 'complete'
            except (ValueError, OSError, subprocess.SubprocessError) as error:
                meta['error'] = str(error)
            finally:
                raw.flush()
                meta['end_utc'] = utc_now()
                for name, path in (('pgn', pgn), ('out', raw_path)):
                    if path.is_file():
                        meta[name] = str(path)
                        meta[f'{name}_bytes'] = path.stat().st_size
                        meta[f'{name}_sha256'] = digest(path)
                json.dump(meta, metadata, indent=2)
                metadata.write('\n')
    finally:
        for sig, handler in handlers.items():
            signal.signal(sig, handler)

    print(f"{args.match}: {meta['status']} {meta.get('error', meta.get('stop_reason', ''))}".rstrip(), flush=True)
    return {'complete': 0, 'interrupted': 130}.get(meta['status'], 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('match', choices=MATCHES)
    parser.add_argument('--deadline', type=float, required=True, help='UTC cutoff as Unix epoch seconds')
    parser.add_argument('--output', type=Path, default=HERE / 'raw')
    parser.add_argument('--print-command', action='store_true', help='print argv without launching engines')
    args = parser.parse_args()
    try:
        return run(args)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(f'{args.match}: refused {error}', file=sys.stderr, flush=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
