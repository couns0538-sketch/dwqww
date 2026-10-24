#!/usr/bin/env python3
"""Original actual-engine Linux screen: 6 A/A +14 OFF/ON/ON/OFF blocks.

Requires an explicit root performance lease before execution. Quantized ON is
not bit-exact; the frozen numerical parity receipt is its accuracy gate. This
does not replace the native Windows float-oracle/qualification script.
"""
import argparse
import csv
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import statistics
import subprocess
import time


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--exe', type=Path, required=True)
    p.add_argument('--d11-receipt', type=Path, required=True)
    p.add_argument('--parity-receipt', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--cpu', type=int, default=1)
    p.add_argument('--on-d13', type=int, required=True)
    p.add_argument('--on-d16', type=int, required=True)
    p.add_argument('--timeout', type=float, default=300)
    p.add_argument('--whole-timeout', type=float, default=1200)
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    actual_hash = sha(args.exe)
    receipt = json.loads(args.d11_receipt.read_text())
    if receipt.get('status') != 'PASS' or receipt.get('engine_sha256') != actual_hash or \
       not (receipt.get('d11') == 308972 or [11, 308972] in receipt.get('rows', [])):
        raise ValueError('matching all-OFF d11 precondition receipt required')
    parity = json.loads(args.parity_receipt.read_text())
    metrics = parity.get('metrics', {})
    if parity.get('status') != 'PASS' or parity.get('engine_sha256') != actual_hash or \
       metrics.get('result') != 'PASS' or metrics.get('unique_four_field_positions', 0) < 100000 or \
       metrics.get('mean_abs_cp', 100000) > 2 or metrics.get('max_abs_cp', 100000) > 30:
        raise ValueError('matching closed 100k numerical/state parity receipt required')
    if args.on_d13 <= 0 or args.on_d16 <= 0:
        raise ValueError('root-frozen ON node counts must be positive')
    os.sched_setaffinity(0, {args.cpu})
    if os.getpriority(os.PRIO_PROCESS, 0) != 0:
        raise RuntimeError('normal priority (nice0) required')
    start = time.monotonic()
    deadline = start + args.whole_timeout
    manifest = {'started_utc': utc(), 'pid': os.getpid(), 'cpu': args.cpu,
                'affinity': sorted(os.sched_getaffinity(0)), 'nice': os.getpriority(os.PRIO_PROCESS, 0),
                'exe': str(args.exe), 'exe_sha256': actual_hash, 'runner_sha256': sha(__file__),
                'd11_receipt': str(args.d11_receipt), 'd11_receipt_sha256': sha(args.d11_receipt),
                'parity_receipt': str(args.parity_receipt), 'parity_receipt_sha256': sha(args.parity_receipt),
                'scope': 'Actual-engine Linux dry run; no Windows, Ryzen or Elo claim',
                'comparison': 'same executable, only NnueInt16 mode differs; ON search is non-bit-exact',
                'threads': 1, 'hash_mib': 16, 'ownbook': False, 'depth': 16,
                'aa_blocks': 6, 'abba_blocks': 14, 'processes_per_block': 4,
                'aa_order': ['OFF', 'OFF', 'OFF', 'OFF'], 'abba_order': ['OFF', 'ON', 'ON', 'OFF'],
                'off_nodes': {'11': 308972, '13': 745494, '16': 2460422, '20': 11901452, '22': 31111774},
                'on_nodes': {'13': args.on_d13, '16': args.on_d16}, 'whole_timeout': args.whole_timeout,
                'decision': 'FASTER only >=12/14 positive and median beyond max-absolute AA band; SLOWER >=12 negative; otherwise NOISE'}
    (args.out / 'frozen.json').write_text(json.dumps(manifest, indent=2) + '\n')
    raw = args.out / 'raw'
    raw.mkdir()
    samples = []

    def bench(active, depth, tag, expected, collect):
        if time.monotonic() >= deadline or sha(args.exe) != actual_hash:
            raise RuntimeError('whole deadline or immutable identity gate failed')
        commands = ('uci\nsetoption name Threads value 1\nsetoption name Hash value 16\n'
                    'setoption name OwnBook value false\nsetoption name NnueInt16 value ' +
                    ('true' if active else 'false') + '\nisready\nbench ' + str(depth) + '\nquit\n')
        (raw / (tag + '.stdin')).write_text(commands)
        command = ['taskset', '-c', str(args.cpu), str(args.exe)]
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True)
        metadata = {'tag': tag, 'argv': command, 'pid': process.pid, 'utc': utc(), 'int16': active,
                    'depth': depth, 'affinity': sorted(os.sched_getaffinity(process.pid)),
                    'nice': os.getpriority(os.PRIO_PROCESS, process.pid), 'nps_sample': collect}
        timed_out = False
        try:
            stdout, stderr = process.communicate(commands, timeout=min(args.timeout, deadline-time.monotonic()))
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()  # This process is owned by this sample; never touch another process.
            stdout, stderr = process.communicate()
        (raw / (tag + '.stdout')).write_text(stdout)
        (raw / (tag + '.stderr')).write_text(stderr)
        metadata.update({'actual_exit': process.returncode, 'watchdog_timeout': timed_out,
                         'closed_utc': utc(), 'stdout_sha256': sha(raw / (tag + '.stdout')),
                         'stderr_sha256': sha(raw / (tag + '.stderr'))})
        (raw / (tag + '.json')).write_text(json.dumps(metadata, indent=2) + '\n')
        if process.returncode != 0 or timed_out or stderr or metadata['affinity'] != [args.cpu] or metadata['nice'] != 0:
            raise RuntimeError('process/affinity/priority/watchdog/stderr gate failed at ' + tag)
        lines = stdout.splitlines()
        if 'option name NnueInt16 type check default false' not in lines:
            raise RuntimeError('missing OFF-default mode option at ' + tag)
        matches = list(re.finditer(r'^info string bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)$', stdout, re.M))
        if len(matches) != 1:
            raise RuntimeError('one exact bench line required at ' + tag)
        if active:
            ack = stdout.find('info string NnueInt16 active\n')
            advertised = stdout.find('option name NnueInt16 type check default false\n')
            if ack <= advertised or ack >= matches[0].start() or 'info string NnueInt16 unavailable; using float' in stdout:
                raise RuntimeError('actual integer activation gate failed at ' + tag)
        measured_depth, nodes, elapsed, nps = map(int, matches[0].groups())
        if measured_depth != depth or nodes != expected or elapsed <= 0 or nps <= 0:
            raise RuntimeError('frozen node/bench gate failed at ' + tag)
        if time.monotonic() >= deadline or sha(args.exe) != actual_hash:
            raise RuntimeError('post-sample whole deadline or identity gate failed at ' + tag)
        if collect:
            samples.append({'tag': tag, 'mode': 'ON' if active else 'OFF', 'nodes': nodes,
                            'time_ms': elapsed, 'nps': nps, 'actual_exit': process.returncode})
        return nps

    # These are identity/correctness probes; their NPS fields are never samples.
    for depth, nodes in [(11,308972), (13,745494), (16,2460422), (20,11901452), (22,31111774)]:
        bench(False, depth, 'identity-off-d' + str(depth), nodes, False)
    for depth, nodes in [(13,args.on_d13), (16,args.on_d16)]:
        bench(True, depth, 'identity-on-d' + str(depth), nodes, False)
    pairs = []
    with (args.out / 'pairs.csv').open('w', newline='', buffering=1) as stream:
        fields = ['kind', 'block', 'A1_nps', 'B1_nps', 'B2_nps', 'A2_nps', 'gain_pct']
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for kind, count in [('AA',6), ('ABBA',14)]:
            for block in range(1, count+1):
                values = []
                for index, active in enumerate([False, kind == 'ABBA', kind == 'ABBA', False]):
                    expected = args.on_d16 if active else 2460422
                    values.append(bench(active, 16, f'{kind}-{block:02d}-{index}', expected, True))
                gain = 100 * (((values[1]+values[2])/2) / ((values[0]+values[3])/2) - 1)
                row = dict(zip(fields, [kind, block, *values, gain]))
                writer.writerow(row)
                pairs.append(row)
                print(json.dumps(row), flush=True)
    aa = [row['gain_pct'] for row in pairs if row['kind'] == 'AA']
    ab = [row['gain_pct'] for row in pairs if row['kind'] == 'ABBA']
    band = max(map(abs, aa))
    median = statistics.median(ab)
    faster = sum(value > 0 for value in ab)
    slower = sum(value < 0 for value in ab)
    verdict = 'FASTER' if faster >= 12 and median > band else 'SLOWER' if slower >= 12 else 'NOISE'
    result = {'status': 'PASS', 'closed_utc': utc(), 'scope': manifest['scope'], 'exe_sha256': actual_hash,
              'aa_blocks': 6, 'abba_blocks': 14, 'actual_nps_processes': len(samples),
              'aa_band_pct': band, 'per_pair_pct': ab, 'median_pct': median, 'mean_pct': statistics.mean(ab),
              'faster': faster, 'slower': slower, 'verdict_linux_dry_run_only': verdict,
              'numerical_gate': '100K_PASS_NON_BIT_EXACT_ON', 'windows_zen5_speed': 'UNPROVEN', 'elo_claim': None}
    (args.out / 'samples.json').write_text(json.dumps(samples, indent=2) + '\n')
    (args.out / 'RESULT.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        import sys
        failure = {'status': 'FAIL', 'error': str(error), 'utc': utc()}
        if '--out' in sys.argv:
            directory = Path(sys.argv[sys.argv.index('--out')+1])
            if directory.is_dir():
                (directory / 'FAILURE.json').write_text(json.dumps(failure, indent=2) + '\n')
        print(json.dumps(failure), file=sys.stderr, flush=True)
        raise
