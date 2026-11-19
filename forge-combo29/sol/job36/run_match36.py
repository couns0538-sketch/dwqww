#!/usr/bin/env python3
"""Verify Job 34 artifacts and run Job 36's pinned fastchess clock matches."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import shlex
import signal
import subprocess
import sys
from tempfile import TemporaryDirectory
import time

from run_pins36 import NET_CHECKSUM, NET_SHA, REFUSAL, SETTING, check_net, check_options, digest, require, utc_now


HERE = Path(__file__).resolve().parent
WORK = HERE.parent
KF = WORK / 'sol-job34/kF/forge'
R15D = WORK / 'sol-job34/r15d/forge'
NET = WORK / 'sol-job34/net768.nnue'
FASTCHESS = WORK / 'sol-job12/fastchess-source/fastchess'
BOOK = WORK / 'sol-job12/UHO_Lichess_4852_v1.epd'
PC20 = WORK / 'sol-job2/pc20-options.txt'
KF_SHA = 'c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb'
R15D_SHA = '9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671'
FASTCHESS_SHA = 'fb945c0930ff17786ccc1c07267930e1c0a6098f9bb16dcd13be20a11baec72e'
BOOK_SHA = '7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a'
PC20_SHA = 'e355dbddb98abb000283ca7b37126e4cf71e152ce6df0bec8f1ea11fb715c7af'
FASTCHESS_REVISION = 'd7b47e8dec6b564aaf4cbb2922ab37e6c6761e75'
FASTCHESS_VERSION = 'fastchess alpha 1.8.3 20261107-d7b47e8'
TIME_CONTROL = '6+0.06'
MATCHES = {'K26': (10, 7360), 'Q1': (300, 7361), 'Q2': (200, 7362)}


def build_settings(pc20):
    lines = pc20.decode().splitlines()
    require(len(lines) == 20 and len(set(lines)) == 20, 'expected 20 distinct PC20 options')
    require('setoption name OwnBook value false' in lines, 'PC20 needs OwnBook disabled')
    return [
        'setoption name Threads value 1',
        'setoption name Hash value 16',
        *lines,
        f'setoption name NNUEArchFile value {NET}',
        'setoption name NNUEArch value true',
    ]


def fastchess_command(engines, settings, pgn, pairs, seed, workers):
    command = [str(FASTCHESS)]
    for side, (engine, _) in engines.items():
        command.extend(('-engine', f'cmd={engine}', f'name={side}'))
        for setting in settings:
            match = SETTING.fullmatch(setting)
            require(match is not None, f'malformed setting {setting}')
            name, value = match.groups()
            command.append(f'option.{name}={value}')
    command.extend((
        '-each', 'proto=uci', f'tc={TIME_CONTROL}', 'timemargin=0',
        '-openings', f'file={BOOK}', 'format=epd', 'order=random',
        '-srand', str(seed), '-rounds', str(pairs), '-games', '2', '-repeat',
        '-concurrency', str(workers), '-autosaveinterval', '0',
        '-pgnout', f'file={pgn}', 'notation=san', 'append=false', 'timeleft=true', 'min=false',
    ))
    return command


def preflight(side, engine, settings, raw):
    commands = '\n'.join(('uci', *settings, 'isready', 'ucinewgame', 'isready', 'quit', ''))
    raw.write(f'{utc_now()} {side} launch preflight {engine}\nUCI stdin\n{commands}')
    raw.flush()
    process = subprocess.run(
        [str(engine)], input=commands, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, timeout=20, check=False,
    )
    raw.write(f'UCI output\n{process.stdout}Exit {process.returncode}\n\n')
    raw.flush()
    output = process.stdout.splitlines()
    require(process.returncode == 0, f'{side} preflight exited {process.returncode}')
    require(not REFUSAL.search(process.stdout), f'{side} preflight reported a refusal or error')
    require(output.count('uciok') == 1 and output.count('readyok') == 2, f'{side} UCI handshake failed')
    check_options(output, settings)
    check_net(output, True)
    active_line = next(line for line in output if line.startswith('info string NNUE v3 active:'))
    require(f' {NET} ' in active_line, f'{side} wrong active net filename')
    return active_line


def stop_request(deadline, caught_signal):
    if caught_signal:
        return caught_signal
    if deadline is not None and time.time() >= deadline:
        return 'deadline'
    return None


def wait_for_match(child, should_stop, meta):
    while child.poll() is None:
        reason = should_stop()
        if reason:
            meta['stop_reason'] = reason
            meta['stop_signal'] = 'SIGINT'
            meta['stop_request_utc'] = utc_now()
            child.send_signal(signal.SIGINT)
            try:
                return child.wait(timeout=20)
            except subprocess.TimeoutExpired:
                meta['stop_escalation'] = 'SIGTERM'
                child.terminate()
                try:
                    return child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    meta['stop_escalation'] = 'SIGKILL'
                    child.kill()
                    return child.wait()
        time.sleep(0.25)
    return child.returncode


def run(args, pairs, seed):
    nproc = int(subprocess.check_output(['nproc'], text=True))
    cpu_max = Path('/sys/fs/cgroup/cpu.max').read_text().strip()
    quota, period = cpu_max.split()
    workers = min(4, nproc - 1)
    if quota != 'max':
        workers = min(workers, max(1, int(quota) // int(period)))
    require(workers > 0, f'nproc {nproc} leaves no eligible game workers')
    engines = {'A': (KF, KF_SHA), 'B': (KF, KF_SHA) if args.match == 'K26' else (R15D, R15D_SHA)}
    output = args.output.resolve()
    pgn, raw_path, sidecar = (output / f'{args.match}.{suffix}' for suffix in ('pgn', 'out', 'meta'))
    for path in (pgn, raw_path, sidecar):
        require(not path.exists(), f'refusing to overwrite {path}')
    pc20 = PC20.read_bytes()
    pc20_sha = sha256(pc20).hexdigest()
    require(pc20_sha == PC20_SHA, f'PC20 SHA-256 {pc20_sha}, expected {PC20_SHA}')
    settings = build_settings(pc20)
    command = fastchess_command(engines, settings, pgn, pairs, seed, workers)
    if args.print_command:
        print(shlex.join(command))
        return 0

    output.mkdir(parents=True, exist_ok=True)
    meta = {
        'match': args.match, 'command': sys.argv, 'fastchess_command': command,
        'fastchess_revision': FASTCHESS_REVISION, 'timecontrol': TIME_CONTROL,
        'time_margin_ms': 0, 'adjudication': False, 'recover': False,
        'nproc': nproc, 'cpu_max': cpu_max, 'concurrency': workers,
        'seed': seed, 'pairs_requested': pairs, 'games_requested': pairs * 2,
        'engine_a': engines['A'][0].parent.name, 'engine_b': engines['B'][0].parent.name,
        'settings_a': settings, 'settings_b': settings, 'pc20_sha256': pc20_sha,
        'net_checksum': NET_CHECKSUM, 'deadline_epoch': args.deadline,
        'start_utc': utc_now(), 'status': 'refused',
    }
    caught_signal = None

    def receive_signal(signum, _frame):
        nonlocal caught_signal
        if caught_signal is None:
            caught_signal = signal.Signals(signum).name

    saved_handlers = {sig: signal.signal(sig, receive_signal) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        with sidecar.open('x', encoding='utf-8') as metadata, raw_path.open('x', encoding='utf-8') as raw:
            try:
                artifact_pins = {
                    'exe_a': engines['A'], 'exe_b': engines['B'],
                    'net': (NET, NET_SHA), 'book': (BOOK, BOOK_SHA), 'fastchess': (FASTCHESS, FASTCHESS_SHA),
                }
                for field, (path, expected) in artifact_pins.items():
                    meta[field] = str(path)
                    actual = digest(path)
                    meta[f'{field}_sha256'] = actual
                    require(actual == expected, f'{field} SHA-256 {actual}, expected {expected}')
                version = subprocess.check_output([str(FASTCHESS), '--version'], text=True,
                                                  stderr=subprocess.STDOUT, timeout=10).strip()
                meta['fastchess_version'] = version
                require(version == FASTCHESS_VERSION, f'fastchess version {version!r}, expected {FASTCHESS_VERSION!r}')
                for side, (engine, _) in engines.items():
                    if stop_request(args.deadline, caught_signal):
                        break
                    meta[f'nnue_active_{side.lower()}'] = preflight(side, engine, settings, raw)
                reason = stop_request(args.deadline, caught_signal)
                if reason:
                    meta.update(status='interrupted', stop_reason=reason)
                else:
                    meta['status'] = 'incomplete'
                    raw.write(f'{utc_now()} fastchess argv\n{shlex.join(command)}\n\nFastchess output\n')
                    raw.flush()
                    with TemporaryDirectory(prefix=f'.{args.match}-fastchess-', dir=output) as cwd:
                        meta['match_start_utc'] = utc_now()
                        child = subprocess.Popen(command, stdout=raw, stderr=subprocess.STDOUT,
                                                 start_new_session=True, cwd=cwd)
                        meta['fastchess_pid'] = child.pid
                        meta['fastchess_exit'] = wait_for_match(
                            child, lambda: stop_request(args.deadline, caught_signal), meta,
                        )
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
        for sig, handler in saved_handlers.items():
            signal.signal(sig, handler)

    print(f"{args.match}: {meta['status']} {meta.get('error', meta.get('stop_reason', ''))}".rstrip(), flush=True)
    return {'complete': 0, 'interrupted': 130}.get(meta['status'], 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('match', choices=MATCHES)
    parser.add_argument('--pairs', type=int, help='Q2 only, from 1 to 200')
    parser.add_argument('--deadline', type=float, help='UTC cutoff as Unix epoch seconds')
    parser.add_argument('--output', type=Path, default=HERE / 'raw')
    parser.add_argument('--print-command', action='store_true', help='print argv without launching engines or a match')
    args = parser.parse_args()
    pairs, seed = MATCHES[args.match]
    if args.pairs is not None:
        if args.match != 'Q2' or not 1 <= args.pairs <= pairs:
            parser.error('--pairs must be 1–200 and is available only for Q2')
        pairs = args.pairs
    try:
        return run(args, pairs, seed)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(f'{args.match}: refused {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
