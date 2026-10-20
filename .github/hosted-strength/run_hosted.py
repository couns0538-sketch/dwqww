#!/usr/bin/env python3
"""Bounded hosted pilot wrapper; delegates matches to the unchanged repository CLI."""
import argparse
import hashlib
import importlib.util
import json
import os
import platform
from pathlib import Path
import re
import resource
import signal
import statistics
import subprocess
import sys
import time

sys.dont_write_bytecode = True


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def host_context():
    def read(path):
        try:
            return Path(path).read_text()
        except OSError as error:
            return {'read_error': str(error)}
    cpuinfo = read('/proc/cpuinfo')
    cpu = {}
    if isinstance(cpuinfo, str):
        for line in cpuinfo.splitlines():
            if ':' in line:
                key, value = line.split(':', 1)
                if key.strip() in ('model name', 'flags', 'vendor_id'):
                    cpu.setdefault(key.strip(), value.strip())
    result = {'platform': platform.platform(), 'uname': list(platform.uname()),
              'python': platform.python_version(), 'cpu': cpu,
              'affinity': sorted(os.sched_getaffinity(0)),
              'proc_self_cgroup': read('/proc/self/cgroup'), 'cgroups': {}}
    roots = [Path('/sys/fs/cgroup')]
    if isinstance(result['proc_self_cgroup'], str):
        for line in result['proc_self_cgroup'].splitlines():
            if line.startswith('0::'):
                roots.append(Path('/sys/fs/cgroup') / line[3:].lstrip('/'))
    for base in set(roots):
        for name in ('cpu.max', 'cpu.stat'):
            result['cgroups'][str(base / name)] = read(base / name)
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--fastchess', type=Path, required=True)
    p.add_argument('--package', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    for name in ('repo', 'baseline', 'candidate', 'fastchess', 'package'):
        setattr(a, name, getattr(a, name).resolve(strict=True))
    a.out.mkdir(parents=True, exist_ok=False)
    cfg = json.loads((a.package / 'protocol.json').read_text())
    for key in ('baseline_sha', 'candidate_sha'):
        if not re.fullmatch('[0-9a-f]{40}', cfg[key]):
            raise ValueError('Freeze full commit SHA before launch: ' + key)
    cpu = min(os.sched_getaffinity(0))
    original_affinity = sorted(os.sched_getaffinity(0))
    os.sched_setaffinity(0, {cpu})
    tools = a.repo / 'tools/match'
    stats_module = load('hosted_pgn_stats', tools / 'pgn_stats.py')
    validator = load('hosted_windows_validator', tools / 'windows_validate.py')
    inputs = [a.baseline, a.candidate, a.fastchess, a.package / 'protocol.json',
              a.package / 'run_hosted.py', a.package / 'openings/aa.epd',
              a.package / 'openings/sprt.epd', tools / 'run_match.py',
              tools / 'pgn_stats.py', tools / 'windows_validate.py']
    frozen = {str(path): sha(path) for path in inputs}
    report = {'status': 'running', 'protocol': cfg, 'frozen_inputs': frozen,
              'original_affinity': original_affinity, 'selected_cpu': cpu,
              'scope': 'Native hosted Linux only; no native Windows/Ryzen claim.',
              'started_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    report['host_context_before'] = host_context()
    save(a.out / 'host-context-before.json', report['host_context_before'])
    save(a.out / 'summary.json', report)
    active = None

    def interrupted(signum, frame):
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        raise KeyboardInterrupt('Termination signal ' + str(signum))

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)

    def stop_group(process):
        # A leader exit does not prove descendants have stopped.
        try:
            os.killpg(process.pid, signal.SIGINT)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=5)

    def checked_inputs():
        for name, digest in frozen.items():
            if sha(name) != digest:
                raise ValueError('Frozen input changed: ' + name)

    def bench(index, deadline):
        log = a.out / ('bench-%02d.stdout' % index)
        err = a.out / ('bench-%02d.stderr' % index)
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        start = time.perf_counter()
        with log.open('w') as stdout, err.open('w') as stderr:
            completed = subprocess.run([str(a.baseline)], input='bench 11\nquit\n',
                text=True, stdout=stdout, stderr=stderr,
                timeout=max(0.001, deadline - time.perf_counter()), check=False)
        end = time.perf_counter()
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        text = log.read_text()
        matches = re.findall(r'bench depth 11 nodes (\d+) time (\d+) nps (\d+)', text)
        if completed.returncode or err.stat().st_size or len(matches) != 1 or int(matches[0][0]) != 419798:
            raise ValueError('Bench signature/exit failure: ' + str(index))
        row = {'index': index, 'warmup': index < 2, 'command': [str(a.baseline)],
               'stdin': 'bench 11\nquit\n', 'wall_seconds': end - start,
               'user_seconds': after.ru_utime - before.ru_utime,
               'system_seconds': after.ru_stime - before.ru_stime,
               'engine_nodes': int(matches[0][0]), 'engine_ms': int(matches[0][1]),
               'engine_nps': int(matches[0][2])}
        row['cpu_seconds'] = row['user_seconds'] + row['system_seconds']
        save(a.out / ('bench-%02d.json' % index), row)
        return row

    def fault_reason(out):
        for name in ('console.txt', 'fastchess.log'):
            path = out / name
            if path.exists():
                text = re.sub(r'\x1b\[[0-9;]*m', '', path.read_text(errors='replace'))
                if re.search(r'^\s*(?:warning|error|fatal)\b|\[(?:WARN(?:ING)?|ERR(?:OR)?|FATAL)\s*\]', text, re.I | re.M):
                    return 'Fastchess warning/error in ' + name
        path = out / 'games.pgn'
        if path.exists():
            for termination in re.findall(r'^\[Termination "([^"\n]*)"\]', path.read_text(errors='replace'), re.M):
                if termination != 'normal':
                    return 'Non-normal PGN termination: ' + termination
        return None

    def match(phase, seconds):
        nonlocal active
        out = a.out / phase
        command = [sys.executable, '-B', str(tools / 'run_match.py'),
                   '--fastchess', str(a.fastchess), '--baseline', str(a.baseline),
                   '--candidate', str(a.baseline if phase == 'aa' else a.candidate),
                   '--openings', str(a.package / ('openings/' + phase + '.epd')),
                   '--out', str(out), '--mode', 'smoke' if phase == 'aa' else 'sprt',
                   '--pairs', '4' if phase == 'aa' else '500', '--seed', str(cfg['seed']),
                   '--tc', 'inf' if phase == 'aa' else '2+0.02', '--cpu', str(cpu),
                   '--hash-mb', '32', '--overhead-ms', '10', '--disable-book']
        if phase == 'aa':
            command += ['--aa', '--nodes', '10000']
        save(a.out / (phase + '-command.json'), command)
        match_deadline = time.monotonic() + seconds
        with (a.out / (phase + '-wrapper.stdout')).open('w') as stdout:
            active = subprocess.Popen(command, stdout=stdout, stderr=subprocess.STDOUT,
                                      start_new_session=True)
            normal_completion = False
            try:
                deadline = match_deadline
                while active.poll() is None:
                    fault = fault_reason(out)
                    if fault:
                        raise RuntimeError(phase + '_fail_fast: ' + fault)
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise subprocess.TimeoutExpired(command, seconds)
                    try:
                        active.wait(timeout=min(0.5, remaining))
                    except subprocess.TimeoutExpired:
                        pass
                code = active.returncode
                normal_completion = code == 0
                fault = fault_reason(out)
                if fault:
                    normal_completion = False
                    raise RuntimeError(phase + '_fail_fast: ' + fault)
            except subprocess.TimeoutExpired:
                raise RuntimeError(phase + '_wall_deadline_inconclusive; all raw files preserved')
            finally:
                if not normal_completion:
                    stop_group(active)
                active = None
        if code:
            raise RuntimeError(phase + '_runner_failed; raw files preserved')
        console = re.sub(r'\x1b\[[0-9;]*m', '', (out / 'console.txt').read_text())
        if re.search(r'^\s*(?:warning|error|fatal)\b', console, re.I | re.M):
            raise ValueError('Fastchess console warning/error')
        log = (out / 'fastchess.log').read_text()
        if re.search(r'\[(?:WARN|ERR|FATAL)\s*\]', log):
            raise ValueError('Fastchess log warning/error')
        text = (out / 'games.pgn').read_text()
        stats = stats_module.summarize(text, require_identical_pairs=phase == 'aa')
        pairs = stats['pairs']
        expected = (out / 'selected.epd').read_text().splitlines()[:pairs]
        grouped = {}
        for tags, _ in stats_module.games(text):
            grouped.setdefault(tags['Round'], ' '.join(tags['FEN'].split()[:4]))
        if set(grouped) != {str(i) for i in range(1, pairs + 1)} or any(
                grouped[str(i)] != fen for i, fen in enumerate(expected, 1)):
            raise ValueError('Games do not follow exact frozen opening prefix')
        penta = re.findall(r'Ptnml\(0-2\):\s*\[([^\]]+)\]', console)
        if not penta or [int(n.strip()) for n in penta[-1].split(',')] != stats['pentanomial_0_half_1_1half_2']:
            raise ValueError('Native/independent pentanomial mismatch')
        manifest = json.loads((out / 'manifest.json').read_text())
        if manifest['selected_sha256'] != sha(out / 'selected.epd'):
            raise ValueError('Selected openings changed')
        if phase == 'aa':
            if pairs != 4 or validator.native_acceptance(console):
                raise ValueError('AA incomplete or unexpected SPRT decision')
            decision, likelihood = 'aa_operational_readiness_only', None
        else:
            decision, likelihood = validator.audit_likelihood(console,
                stats['pentanomial_0_half_1_1half_2'], pairs, 500)
        checked_inputs()
        result = {'statistics': stats, 'decision': decision, 'likelihood_audit': likelihood,
                  'screen_48': 'Same SPRT prefix; no reset, separate gate or discarded games.'}
        save(out / 'independent-audit.json', result)
        return result

    try:
        checked_inputs()
        deadline = time.perf_counter() + 30
        rows = [bench(i, deadline) for i in range(8)]
        if time.perf_counter() > deadline:
            raise RuntimeError('AA bench wall deadline exceeded')
        gates = {}
        for field in ('wall_seconds', 'cpu_seconds'):
            ratios = [rows[i + 1][field] / rows[i][field] for i in (2, 4, 6)]
            gates[field] = {'ratios': ratios, 'median': statistics.median(ratios),
                'pass': 0.95 <= statistics.median(ratios) <= 1.05 and all(0.85 <= x <= 1.15 for x in ratios)}
        report['bench_aa'] = gates
        save(a.out / 'summary.json', report)
        if not all(gate['pass'] for gate in gates.values()):
            raise RuntimeError('Whole-engine AA calibration failed; no games permitted')
        for name in ('baseline', 'candidate'):
            completed = subprocess.run([str(getattr(a, name))], input='uci\nquit\n',
                text=True, capture_output=True, timeout=10, check=True)
            (a.out / (name + '-uci.stdout')).write_text(completed.stdout)
            if not re.search(r'option name Ponder type check default false', completed.stdout):
                raise ValueError('Ponder=false runtime default not confirmed')
        report['aa'] = match('aa', 90)
        report['status'] = 'aa_passed_starting_sprt'
        save(a.out / 'summary.json', report)
        report['sprt'] = match('sprt', 16 * 60)
        report['status'] = 'completed_independently_audited'
    except BaseException as error:
        report['status'] = 'failed_or_inconclusive_no_acceptance'
        report['error'] = repr(error)
        raise
    finally:
        if active is not None:
            stop_group(active)
        report['host_context_after'] = host_context()
        save(a.out / 'host-context-after.json', report['host_context_after'])
        report['finished_utc'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        report['raw_files_preserved_without_trimming'] = True
        save(a.out / 'summary.json', report)


if __name__ == '__main__':
    main()
