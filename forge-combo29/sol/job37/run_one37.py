#!/usr/bin/env python3
"""Time one Job 37 run with one warm Forge process per worker."""

import argparse
from contextlib import redirect_stdout
import json
import multiprocessing as mp
from multiprocessing.connection import wait
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


WORK = Path('/workspace/work')
ROOT = Path(__file__).resolve().parent.parent
for driver in (ROOT / 'job35', WORK / 'sol-job35'):
    if (driver / 'whole_games35.py').is_file():
        sys.path.insert(0, str(driver))
        break

import whole_games35 as job35


PINNED_ENGINES = {
    'r15d': '9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671',
    'kF': 'c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb',
}
PINNED_NET = 'c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7'
GAMES_PER_WORKER = 25


def worker(w, workers, args, exe, options, ready_to_start, stop, cpu_read, outgoing):
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    job35.SEARCH = f'go softnodes {args.nodes}'
    basename = args.output / f'worker{w:02d}'
    receipt = {
        'worker': w, 'driver_pid': os.getpid(), 'pid': None, 'active_line': None,
        'games_completed': 0, 'records': 0, 'last_info_nodes_sum': 0, 'error': None,
    }

    def stopped():
        return stop.is_set() or time.time() >= args.deadline

    with basename.with_suffix('.out').open('x', encoding='utf-8') as log:
        try:
            with job35.Engine(exe, timeout=15) as engine:
                receipt['pid'] = engine.process.pid
                configuration = {'settings_sent': []}
                with redirect_stdout(log):
                    job35.setup(engine, options, configuration)
                receipt['active_line'] = configuration['active_line']
                if ' hidden 768 ' not in receipt['active_line']:
                    raise RuntimeError('wrong active network shape')
                log.write(json.dumps(configuration, sort_keys=True) + '\n')
                log.flush()
                outgoing.send(('ready', receipt.copy()))
                ready_to_start.wait()
                current = {}
                with basename.with_suffix('.rows').open('x', encoding='ascii', newline='\n') as rows:
                    for i in range(GAMES_PER_WORKER):
                        if stopped():
                            break
                        game = args.base + i * workers + w
                        current = {'game': game, 'ply': None}
                        opening = job35.generated_opening(game)
                        if opening[2] != 'ready':
                            engine.send('ucinewgame')
                            engine.send('isready')
                            engine.until('readyok')
                        result = job35.play_game(engine, opening, game, stopped, current)
                        if result is None:
                            break
                        records, node_sum, termination, _kinds, sample = result
                        rows.writelines(records)
                        rows.flush()
                        receipt['games_completed'] += 1
                        receipt['records'] += len(records)
                        receipt['last_info_nodes_sum'] += node_sum
                        log.write(json.dumps({
                            'game': game, 'records': len(records), 'nodes': node_sum,
                            'termination': termination, 'first_search_last_info': sample,
                        }, sort_keys=True) + '\n')
                if receipt['games_completed'] < GAMES_PER_WORKER and not stopped():
                    raise RuntimeError(f'worker stopped early at {current}')
                outgoing.send(('done', receipt))
                cpu_read.wait()
        except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
            receipt['error'] = f'{type(error).__name__}: {error}'
            outgoing.send(('error', receipt))
        finally:
            log.write(json.dumps(receipt, sort_keys=True) + '\n')
            outgoing.close()


def engine_ticks(w, pid):
    stat = Path(f'/proc/{pid}/stat').read_text()
    # comm is parenthesized and can include spaces or closing parentheses.
    fields = stat[stat.rfind(')') + 2:].split()
    return {'worker': w, 'pid': pid, 'user': int(fields[11]), 'system': int(fields[12])}


def collect(connections, processes, expected, deadline, interrupted):
    receipts = {}
    pending = set(connections)
    while pending:
        if reason := interrupted():
            return receipts, reason
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return receipts, 'deadline'
        for conn in wait(pending, timeout=min(remaining, 0.05)):
            w = connections[conn]
            label, receipt = conn.recv()
            receipts[w] = receipt
            pending.remove(conn)
            if label != expected:
                return receipts, f'worker {w} returned {label}: {receipt["error"]}'
        for conn in pending:
            w = connections[conn]
            if processes[w].exitcode is not None:
                return receipts, f'worker {w} exited {processes[w].exitcode} before {expected}'
    return receipts, None


def final_worker_receipts(args, workers, partial):
    receipts = []
    for w in range(workers):
        log = args.output / f'worker{w:02d}.out'
        if log.is_file():
            lines = log.read_text(encoding='utf-8').splitlines()
            if lines and lines[-1].startswith('{"active_line"'):
                last = json.loads(lines[-1])
                if last.get('worker') == w:
                    receipts.append(last)
                    continue
        if w in partial:
            receipts.append(partial[w])
    return receipts


def merge_records(output, workers):
    staged = sorted(output.glob('worker*.rows'))
    rows = [line for path in staged for line in path.read_text(encoding='ascii').splitlines(keepends=True)]

    def game_ply(line):
        game, ply, _move, _nodes = line.split()
        return int(game), int(ply)

    rows.sort(key=game_ply)
    if len(staged) > workers or len({game_ply(row) for row in rows}) != len(rows):
        raise RuntimeError('worker records overlap')
    records = output / 'records.tsv'
    records.write_text(''.join(rows), encoding='ascii', newline='\n')
    for path in staged:
        path.unlink()
    return len(rows), job35.digest(records)


def run(args):
    if job35.chess.__version__ != '1.11.2':
        raise RuntimeError(f'expected python-chess 1.11.2, got {job35.chess.__version__}')
    workers = int(subprocess.check_output(['nproc'], text=True))
    if workers < 1:
        raise RuntimeError(f'nproc reported {workers}')
    exe = args.artifacts / args.build / 'forge'
    net = args.artifacts / 'net768.nnue'
    if job35.digest(exe) != PINNED_ENGINES[args.build] or job35.digest(net) != PINNED_NET:
        raise RuntimeError('Job 34 executable or net SHA-256 mismatch')
    options = job35.settings(net, 93)
    args.output.mkdir(parents=True, exist_ok=True)
    if any(args.output.iterdir()):
        raise FileExistsError(f'output directory is not empty: {args.output}')
    ctx = mp.get_context('fork')
    ready_to_start, stop, cpu_read = ctx.Event(), ctx.Event(), ctx.Event()
    receivers, processes = {}, []
    ready, done, ticks = {}, {}, []
    request = None
    started_utc = finished_utc = monotonic_start = monotonic_stop = None
    deadline = time.monotonic() + args.deadline - time.time()

    def on_signal(signum, _frame):
        nonlocal request
        request = signal.Signals(signum).name

    old_signals = {sig: signal.signal(sig, on_signal) for sig in (signal.SIGINT, signal.SIGTERM)}
    reason = None
    try:
        for w in range(workers):
            receiver, outgoing = ctx.Pipe(duplex=False)
            process = ctx.Process(target=worker, args=(
                w, workers, args, exe, options, ready_to_start, stop, cpu_read, outgoing,
            ))
            process.start()
            outgoing.close()
            receivers[receiver] = w
            processes.append(process)
        ready, reason = collect(receivers, processes, 'ready', deadline, lambda: request)
        if reason is None:
            started_utc = job35.utc_now()
            monotonic_start = time.monotonic()
            ready_to_start.set()
            done, reason = collect(receivers, processes, 'done', deadline, lambda: request)
            monotonic_stop = time.monotonic()
            finished_utc = job35.utc_now()
            if reason is None:
                ticks = [engine_ticks(w, ready[w]['pid']) for w in range(workers)]
    except (EOFError, OSError, RuntimeError, ValueError) as error:
        reason = f'{type(error).__name__}: {error}'
    finally:
        stop.set()
        ready_to_start.set()
        cpu_read.set()
        for process in processes:
            process.join(timeout=2)
            if process.is_alive():
                process.terminate()
                process.join(timeout=1)
            if process.is_alive():
                process.kill()
                process.join()
        for conn in receivers:
            conn.close()
        for sig, old in old_signals.items():
            signal.signal(sig, old)

    worker_receipts = final_worker_receipts(args, workers, ready | done)
    records, record_sha = merge_records(args.output, workers)
    total_games = sum(row['games_completed'] for row in worker_receipts)
    clock_ticks = os.sysconf('SC_CLK_TCK')
    if reason is None and (
        any(process.exitcode for process in processes)
        or len(worker_receipts) != workers
        or len(ticks) != workers
        or total_games != workers * GAMES_PER_WORKER
        or any(row['error'] for row in worker_receipts)
        or records != sum(row['records'] for row in worker_receipts)
    ):
        reason = 'incomplete worker results'
    status = 'complete' if reason is None else (
        'interrupted' if reason in ('deadline', 'SIGINT', 'SIGTERM') else 'failed'
    )
    result = {
        'status': status, 'reason': reason, 'build': args.build, 'base': args.base, 'nodes': args.nodes,
        'workers': workers, 'games_per_worker': GAMES_PER_WORKER,
        'wall_seconds': None if monotonic_stop is None else monotonic_stop - monotonic_start,
        'engine_cpu_seconds': None if not ticks else sum(row['user'] + row['system'] for row in ticks) / clock_ticks,
        'records': records, 'record_sha256': record_sha, 'games_completed': total_games,
        'games_requested': workers * GAMES_PER_WORKER, 'started_utc': started_utc, 'finished_utc': finished_utc,
        'monotonic_start': monotonic_start, 'monotonic_stop': monotonic_stop, 'deadline_epoch': args.deadline,
        'engine_ticks': ticks, 'ticks_per_second': clock_ticks, 'worker_receipts': worker_receipts,
        'engine_sha256': PINNED_ENGINES[args.build], 'net_sha256': PINNED_NET, 'settings': options,
        'python': sys.version.split()[0], 'python_chess': job35.chess.__version__,
        'reset_frequency': 'ucinewgame and isready once per game, including terminal random openings',
        'record_format': 'space-delimited ASCII: game, absolute zero-based ply, bestmove, last-info nodes',
    }
    (args.output / 'run.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return {'complete': 0, 'interrupted': 130, 'failed': 1}[status]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', choices=PINNED_ENGINES, required=True)
    parser.add_argument('--base', type=int, required=True)
    parser.add_argument('--nodes', choices=(2000, 3000), type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--deadline', type=float, required=True)
    parser.add_argument('--artifacts', type=Path, default=WORK / 'sol-job34')
    args = parser.parse_args()
    if args.base <= 0:
        parser.error('--base must be positive')
    try:
        return run(args)
    except (OSError, RuntimeError, ValueError) as error:
        print(f'run refused: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
