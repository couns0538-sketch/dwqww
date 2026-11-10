#!/usr/bin/env python3
"""Hash-verified isolated legal-witness ABBA profile; exploratory cloud only."""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import platform
import re
import statistics
import subprocess
import time


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--evidence', type=pathlib.Path, required=True,
                        help='Verified validation manifest with baseline/candidate paths and SHA-256 hashes')
    parser.add_argument('--output', type=pathlib.Path, required=True)
    parser.add_argument('--cycles', type=int, default=3, choices=range(3, 6))
    parser.add_argument('--cpu', type=int)
    args = parser.parse_args()
    evidence = json.loads(args.evidence.read_text())
    binaries = evidence['binaries']
    for name, entry in binaries.items():
        if sha(entry['path']) != entry['sha256']:
            raise RuntimeError(f'{name} binary does not match saved equivalence evidence')
    allowed = sorted(os.sched_getaffinity(0))
    cpu = min(allowed) if args.cpu is None else args.cpu
    if cpu not in allowed:
        raise RuntimeError('Requested CPU not in allowed affinity')
    os.sched_setaffinity(0, {cpu})
    if os.sched_getaffinity(0) != {cpu}:
        raise RuntimeError('Could not pin profiling driver')
    args.output.mkdir(parents=True, exist_ok=True)
    cpu_models = sorted({line.split(':', 1)[1].strip()
                         for line in pathlib.Path('/proc/cpuinfo').read_text().splitlines()
                         if line.startswith('model name')})
    report = {'schema': 1, 'status': 'UNPROVEN; exploratory cloud data only',
              'started_utc': utc(), 'evidence_sha256': sha(args.evidence), 'validation_manifest': evidence,
              'binaries': binaries, 'depth': 16, 'cycles_per_mode': args.cycles,
              'order': ['baseline', 'candidate', 'candidate', 'baseline'],
              'threads': 1, 'bench_hash_mb': 16, 'cpu': cpu,
              'original_allowed_cpus': allowed, 'effective_affinity': sorted(os.sched_getaffinity(0)),
              'machine': {'platform': platform.platform(), 'cpu_models': cpu_models,
                          'logical_cpus_visible': os.cpu_count(), 'initial_loadavg': os.getloadavg()},
              'limitations': ['Shared cloud host; CPU is pinned, not reserved or isolated.',
                             'Host contention, frequency, power and thermal state are uncontrolled.',
                             'Wall time includes process creation, initialization and exit.',
                             f'{args.cycles} ABBA cycles per mode; small fixed eight-position bench.',
                             'No inference of native performance, Elo, or statistical acceptance.'],
              'runs': []}
    receipt = args.output / 'legal_witness_profile_results.json'
    def save():
        receipt.write_text(json.dumps(report, indent=2) + '\n')
    def run(name, nnue, cycle, slot, warmup=False):
        ident = f"{'warmup' if warmup else 'sample'}-nnue{int(nnue)}-cycle{cycle}-slot{slot}-{name}"
        commands = (f'setoption name Threads value 1\nsetoption name OwnBook value false\n'
                    f'setoption name UseNNUE value {str(nnue).lower()}\nbench 16\nquit\n')
        load_before = os.getloadavg()
        start_utc = utc()
        start = time.perf_counter_ns()
        proc = subprocess.run([binaries[name]['path']], input=commands, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
        elapsed = (time.perf_counter_ns() - start) / 1e9
        (args.output / (ident + '.stdout.txt')).write_text(proc.stdout)
        (args.output / (ident + '.stderr.txt')).write_text(proc.stderr)
        parsed = re.findall(r'info string bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)', proc.stdout)
        entry = {'id': ident, 'binary': name, 'nnue': nnue, 'cycle': cycle, 'slot': slot,
                 'warmup': warmup, 'started_utc': start_utc, 'wall_seconds': elapsed,
                 'load_before': load_before, 'load_after': os.getloadavg(),
                 'returncode': proc.returncode, 'stdin': commands,
                 'stdout_file': ident + '.stdout.txt', 'stderr_file': ident + '.stderr.txt'}
        report['runs'].append(entry)
        if proc.returncode != 0 or len(parsed) != 1:
            save()
            raise RuntimeError('Process failure or malformed bench receipt: ' + ident)
        depth, nodes, ms, nps = map(int, parsed[0])
        entry.update({'depth': depth, 'nodes': nodes, 'engine_ms': ms, 'engine_nps': nps})
        if depth != 16 or nodes != (3024920 if nnue else 2448617):
            save()
            raise RuntimeError('Node signature mismatch: ' + ident)
        save()
        print(f'{ident}: nodes={nodes} wall={elapsed:.6f}s', flush=True)
    for nnue in [True, False]:
        for i, name in enumerate(['baseline', 'candidate']):
            run(name, nnue, -1, i, True)
        for cycle in range(args.cycles):
            for slot, name in enumerate(report['order']):
                run(name, nnue, cycle, slot)
    report['summaries'] = []
    for nnue in [True, False]:
        rows = [r for r in report['runs'] if r['nnue'] == nnue and not r['warmup']]
        summary = {'nnue': nnue, 'node_signature_equal': len({r['nodes'] for r in rows}) == 1,
                   'wall_seconds': {}, 'abba_candidate_over_baseline_ratios': []}
        for name in ['baseline', 'candidate']:
            values = [r['wall_seconds'] for r in rows if r['binary'] == name]
            summary['wall_seconds'][name] = {'samples': len(values), 'median': statistics.median(values),
                                              'minimum': min(values), 'maximum': max(values)}
        for cycle in range(args.cycles):
            group = [r for r in rows if r['cycle'] == cycle]
            a = statistics.mean(r['wall_seconds'] for r in group if r['binary'] == 'baseline')
            b = statistics.mean(r['wall_seconds'] for r in group if r['binary'] == 'candidate')
            summary['abba_candidate_over_baseline_ratios'].append(b / a)
        report['summaries'].append(summary)
    report['hashes_unchanged'] = all(sha(v['path']) == v['sha256'] for v in binaries.values())
    report['finished_utc'] = utc()
    report['passed_integrity_checks'] = report['hashes_unchanged'] and all(s['node_signature_equal'] for s in report['summaries'])
    save()
    print(json.dumps(report['summaries'], indent=2))
    if not report['passed_integrity_checks']:
        raise RuntimeError('Final binary integrity or node check failed')


if __name__ == '__main__':
    main()
