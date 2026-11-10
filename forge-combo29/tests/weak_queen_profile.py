#!/usr/bin/env python3
"""Hash-verified cloud diagnostic: child CPU time and wall time, never acceptance."""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import platform
import re
import resource
import statistics
import subprocess
import time


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--evidence', type=pathlib.Path, required=True)
    p.add_argument('--output', type=pathlib.Path, required=True)
    p.add_argument('--depth', type=int, choices=[16, 18, 20], default=18)
    p.add_argument('--cycles', type=int, choices=range(3, 7), default=4)
    p.add_argument('--cpu', type=int)
    args = p.parse_args()
    evidence = json.loads(args.evidence.read_text())
    assert evidence['passed'] and evidence['comparisons'] == 256 and not evidence['failures']
    binaries = evidence['binaries']
    assert set(binaries) == {'baseline', 'candidate'}
    for entry in binaries.values():
        assert sha(entry['path']) == entry['sha256'], 'Binary differs from validated binary'
    assert not args.output.exists(), 'Refuse to overwrite an earlier diagnostic'
    allowed = sorted(os.sched_getaffinity(0))
    cpu = min(allowed) if args.cpu is None else args.cpu
    assert cpu in allowed
    os.sched_setaffinity(0, {cpu})
    assert os.sched_getaffinity(0) == {cpu}
    report = {
        'schema': 1, 'status': 'RUNNING; cloud diagnostic only', 'started_utc': utc(),
        'source_commit': '9b67829c86c0ddadcb8334fe92147ffa4a895ced',
        'script_sha256': sha(__file__), 'evidence_sha256': sha(args.evidence), 'binaries': binaries,
        'depth': args.depth, 'cycles_per_mode': args.cycles, 'threads': 1, 'bench_hash_mb': 16,
        'cycle_orders': [(['baseline', 'candidate', 'candidate', 'baseline'] if i % 2 == 0 else
                          ['candidate', 'baseline', 'baseline', 'candidate']) for i in range(args.cycles)],
        'measured_runs': args.cycles * 8, 'warmup_runs': 4,
        'cpu': cpu, 'original_allowed_cpus': allowed, 'platform': platform.platform(),
        'cpu_models': sorted({x.split(':', 1)[1].strip() for x in pathlib.Path('/proc/cpuinfo').read_text().splitlines()
                              if x.startswith('model name')}),
        'limitations': ['CPU pinned, not reserved; uncontrolled shared-cloud cache/frequency/thermal contention.',
                        'Wall time includes spawn/init/exit and host descheduling.',
                        'RUSAGE_CHILDREN CPU deltas exclude descheduling, not frequency/cache contention.',
                        'Only the single engine subprocess runs between each before/after resource sample.',
                        'Small fixed bench; native performance and Elo gates remain UNPROVEN.'],
        'runs': [],
    }

    def save():
        args.output.write_text(json.dumps(report, indent=2) + '\n')

    signatures = {}

    def run(name, nnue, cycle, slot):
        commands = ('setoption name Threads value 1\nsetoption name OwnBook value false\n'
                    f'setoption name UseNNUE value {str(nnue).lower()}\nbench {args.depth}\nquit\n')
        row = {'binary': name, 'nnue': nnue, 'cycle': cycle, 'slot': slot, 'warmup': cycle < 0,
               'started_utc': utc(), 'stdin': commands, 'load_before': os.getloadavg()}
        report['runs'].append(row)
        save()
        # No subprocess except this engine is started between these samples.
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        started = time.perf_counter_ns()
        try:
            proc = subprocess.run([binaries[name]['path']], input=commands, text=True,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
        except subprocess.TimeoutExpired as error:
            row.update({'error': str(error), 'stdout': str(error.stdout), 'stderr': str(error.stderr)})
            report['status'] = 'FAILED; engine timeout'
            raise
        finally:
            elapsed = (time.perf_counter_ns() - started) / 1e9
            after = resource.getrusage(resource.RUSAGE_CHILDREN)
            user = after.ru_utime - before.ru_utime
            system = after.ru_stime - before.ru_stime
            row.update({'wall_seconds': elapsed, 'ru_utime_delta': user, 'ru_stime_delta': system,
                        'child_cpu_seconds': user + system})
            save()
        row.update({'stdout': proc.stdout, 'stderr': proc.stderr,
                    'returncode': proc.returncode, 'load_after': os.getloadavg()})
        parsed = re.findall(r'info string bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)', proc.stdout)
        if proc.returncode or len(parsed) != 1:
            report['status'] = 'FAILED; engine exit or malformed bench'
            save()
            raise RuntimeError(row)
        depth, nodes, ms, nps = map(int, parsed[0])
        row.update({'depth': depth, 'nodes': nodes, 'engine_ms': ms, 'engine_nps': nps})
        expected = signatures.setdefault(nnue, nodes)
        if depth != args.depth or nodes != expected:
            report['status'] = 'FAILED; unequal node signature'
            save()
            raise RuntimeError(row)
        if args.depth == 16:
            assert nodes == (3024920 if nnue else 2448617)
        save()
        print(f'{name} nnue={nnue} cycle={cycle} slot={slot}: CPU={user+system:.6f} wall={elapsed:.6f}', flush=True)

    save()
    for nnue in [True, False]:
        for slot, name in enumerate(['baseline', 'candidate']):
            run(name, nnue, -1, slot)
        for cycle, order in enumerate(report['cycle_orders']):
            for slot, name in enumerate(order):
                run(name, nnue, cycle, slot)
    report['summaries'] = []
    for nnue in [True, False]:
        rows = [r for r in report['runs'] if r['nnue'] == nnue and not r['warmup']]
        summary = {'nnue': nnue, 'nodes': signatures[nnue], 'metrics': {}}
        for metric in ['wall_seconds', 'child_cpu_seconds']:
            ratios = []
            for cycle in range(args.cycles):
                group = [r for r in rows if r['cycle'] == cycle]
                means = {name: statistics.mean(r[metric] for r in group if r['binary'] == name)
                         for name in ['baseline', 'candidate']}
                ratios.append(means['candidate'] / means['baseline'])
            summary['metrics'][metric] = {
                'candidate_over_baseline_duration_ratios': ratios, 'median_ratio': statistics.median(ratios),
                'per_binary': {name: {'samples': len(values), 'median': statistics.median(values),
                                     'minimum': min(values), 'maximum': max(values)}
                               for name in ['baseline', 'candidate']
                               for values in [[r[metric] for r in rows if r['binary'] == name]]},
            }
        report['summaries'].append(summary)
    report['hashes_unchanged'] = all(sha(v['path']) == v['sha256'] for v in binaries.values())
    report['finished_utc'] = utc()
    report['status'] = 'COMPLETE; native speed/Elo UNPROVEN' if report['hashes_unchanged'] else 'FAILED; changed binary'
    save()
    assert report['hashes_unchanged']
    print(json.dumps(report['summaries'], indent=2))


if __name__ == '__main__':
    main()
