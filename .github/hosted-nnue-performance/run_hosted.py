#!/usr/bin/env python3
"""One bounded hosted Linux pilot. No retries, gameplay, or adaptive sampling."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import signal
import statistics
import subprocess
import sys
import time

sys.dont_write_bytecode = True
BLOCK_ORDERS = ['ABBA', 'BAAB'] * 3
ENGINE_STDIN = b'bench 11\n' * 12 + b'quit\n'
READY = 'PREREGISTERED_REVIEWED_READY_FOR_SINGLE_PUSH'
BENCH_LINE = re.compile(r'info string bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)')


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def files_under(path):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('Immutable inputs must not be symlinks: ' + str(path))
    if path.is_file():
        return [path]
    if not path.is_dir():
        raise ValueError('Missing immutable input: ' + str(path))
    entries = sorted(path.rglob('*'))
    if any(entry.is_symlink() for entry in entries):
        raise ValueError('Immutable input tree contains a symlink: ' + str(path))
    files = [entry for entry in entries if entry.is_file()]
    if not files:
        raise ValueError('Empty immutable input tree: ' + str(path))
    return files


def freeze_inputs(roots):
    return {str(path): sha(path) for root in roots for path in files_under(root)}


def verify_build_freeze(frozen_root, manifest_path):
    expected = json.loads(Path(manifest_path).read_text())
    actual = {path.relative_to(frozen_root).as_posix(): sha(path) for path in files_under(frozen_root)}
    if not isinstance(expected, dict) or not expected or expected != actual:
        raise ValueError('Frozen build manifest differs from actual immutable inputs before timing')
    return dict(status='passed', manifest=str(manifest_path), sha256=sha(manifest_path), files=len(actual))


def rehash_inputs(frozen, roots):
    rows, mismatches = {}, []
    for name, expected in frozen.items():
        row = {'expected_sha256': expected}
        try:
            row['actual_sha256'] = sha(name)
            row['matches'] = not Path(name).is_symlink() and row['actual_sha256'] == expected
        except OSError as error:
            row.update(matches=False, error=repr(error))
        rows[name] = row
        if not row['matches']:
            mismatches.append(name)
    observed, tree_errors = set(), []
    for root in roots:
        try:
            observed.update(str(path) for path in files_under(root))
        except (OSError, ValueError) as error:
            tree_errors.append(repr(error))
    added = sorted(observed - set(frozen))
    return dict(status='failed' if mismatches or added or tree_errors else 'passed',
                inputs=rows, mismatches=mismatches, added_inputs=added, tree_errors=tree_errors)


def host_context():
    result = dict(platform=platform.platform(), uname=list(platform.uname()),
                  python=platform.python_version(), affinity=sorted(os.sched_getaffinity(0)))
    for name in ['/proc/cpuinfo', '/proc/loadavg', '/proc/self/cgroup',
                 '/sys/fs/cgroup/cpu.max', '/sys/fs/cgroup/cpu.stat']:
        try:
            result[name] = Path(name).read_text()
        except OSError as error:
            result[name] = {'error': repr(error)}
    return result


def positive(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError('Invalid positive finite ' + label)
    return value


def pin_cpu(cpu):
    os.sched_setaffinity(0, {cpu})
    if os.sched_getaffinity(0) != {cpu}:
        raise RuntimeError('Exact one-CPU affinity was not established')


def kill_group(pid):
    try:
        os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def run_owned(command, stdin, out, cpu, timeout):
    """Use wait4 for this exact child; raw streams are never piped or discarded."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    stdin_path, stdout_path, stderr_path = [out / name for name in ('stdin.txt', 'stdout.txt', 'stderr.txt')]
    stdin_path.write_bytes(stdin)
    row = dict(command=[str(part) for part in command], cwd=str(Path.cwd()),
               stdin=str(stdin_path), stdout=str(stdout_path), stderr=str(stderr_path),
               cpu=cpu, affinity_method='parent and child sched_setaffinity, exact singleton verified',
               timeout_seconds=timeout, timed_out=False, returncode=None,
               started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    save(out / 'command.json', row)
    process, reaped, usage, status = None, False, None, None
    started = time.monotonic()
    try:
        with stdin_path.open('rb') as source, stdout_path.open('wb') as stdout, stderr_path.open('wb') as stderr:
            process = subprocess.Popen(row['command'], stdin=source, stdout=stdout, stderr=stderr,
                                       start_new_session=True, preexec_fn=lambda: pin_cpu(cpu))
            row['pid'] = process.pid
            while True:
                pid, status, usage = os.wait4(process.pid, os.WNOHANG)
                if pid == process.pid:
                    reaped = True
                    break
                if time.monotonic() - started >= timeout:
                    row['timed_out'] = True
                    kill_group(process.pid)
                    _, status, usage = os.wait4(process.pid, 0)
                    reaped = True
                    break
                time.sleep(.01)
    except BaseException as error:
        row['error'] = repr(error)
        raise
    finally:
        if process is not None:
            # The leader can exit before a descendant; always clean the owned group.
            kill_group(process.pid)
            if not reaped:
                _, status, usage = os.wait4(process.pid, 0)
            process.returncode = os.waitstatus_to_exitcode(status)
            row['returncode'] = process.returncode
        row['wall_seconds'] = time.monotonic() - started
        if usage is not None:
            row.update(user_seconds=usage.ru_utime, system_seconds=usage.ru_stime,
                       cpu_seconds=usage.ru_utime + usage.ru_stime,
                       wait_status=status)
        save(out / 'status.json', row)
    return row


def parse_bench(stdout):
    records = []
    for line in stdout.splitlines():
        if line.startswith('info string bench'):
            match = BENCH_LINE.fullmatch(line)
            if not match:
                raise ValueError('Malformed complete bench record: ' + repr(line))
            depth, nodes, _, _ = map(int, match.groups())
            records.append(dict(depth=depth, nodes=nodes))
    if len(records) != 12 or any(row != dict(depth=11, nodes=419798) for row in records):
        raise ValueError('Every process must complete exactly twelve depth-11 419798-node benches')
    return records


def parse_kernel(stdout):
    try:
        row = json.loads(stdout)
    except (ValueError, TypeError) as error:
        raise ValueError('Kernel must emit exactly one complete JSON record') from error
    expected = dict(benchmark='public_nnue_update_microkernel', group='quiet',
                    iterations=2000000, warmup_calls=16384,
                    actual_counts=[0, 0, 2000000, 0, 0],
                    checksum_scope='all_final_output_ring_lanes_and_validity_outside_timing',
                    strict_math_preprocessor_check=True, driver_optimized=True,
                    core_and_driver_lto='must_be_disabled_and_verified_externally')
    if not isinstance(row, dict) or any(row.get(key) != value for key, value in expected.items()):
        raise ValueError('Kernel fixed workload or strict-math metadata mismatch')
    for key in ['iterations', 'warmup_calls', 'corpus_size', 'hidden_size', 'accumulator_bytes',
                'wall_ns', 'cpu_ticks', 'clocks_per_sec', 'fp_control']:
        if type(row.get(key)) is not int or row[key] < (0 if key == 'fp_control' else 1):
            raise ValueError('Missing or invalid integer kernel field: ' + key)
    if row['corpus_size'] > row['iterations']:
        raise ValueError('Kernel corpus exceeds update count')
    counts = row.get('corpus_seen')
    if not isinstance(counts, list) or len(counts) != 5 or any(type(n) is not int or n < 0 for n in counts):
        raise ValueError('Invalid kernel corpus counts')
    for key in ['input_hash_fnv1a64', 'output_hash_fnv1a64']:
        if not re.fullmatch('[0-9a-f]{16}', str(row.get(key, ''))):
            raise ValueError('Missing kernel hash: ' + key)
    for key in ['compiler', 'flags_label']:
        if not isinstance(row.get(key), str) or not row[key]:
            raise ValueError('Missing kernel build field: ' + key)
    if type(row.get('driver_avx2')) is not bool:
        raise ValueError('Missing kernel ISA metadata')
    return row


def calibration(pairs):
    if len(pairs) != 6:
        raise ValueError('Calibration requires exactly six completed pairs')
    result = {}
    for name in ['cpu', 'wall']:
        key = name + '_seconds'
        ratios = [positive(positive(pair['A'][key], key) / positive(pair['B'][key], key), name + ' ratio')
                  for pair in pairs]
        median = statistics.median(ratios)
        result[name] = dict(ratios=ratios, median=median,
                            passed=all(.97 <= ratio <= 1.03 for ratio in ratios) and .99 <= median <= 1.01)
    result['passed'] = all(result[name]['passed'] for name in ['cpu', 'wall'])
    return result


def analyze_blocks(blocks):
    if len(blocks) != 6 or any(''.join(row['variant'] for row in block) != order
                               for block, order in zip(blocks, BLOCK_ORDERS)):
        raise ValueError('Exactly six complete alternating ABBA/BAAB blocks are required')
    result = {}
    for name in ['cpu', 'wall']:
        key = name + '_seconds'
        ratios = [positive(sum(positive(row[key], key) for row in block if row['variant'] == 'A') /
                          sum(positive(row[key], key) for row in block if row['variant'] == 'B'), name + ' ratio')
                  for block in blocks]
        logs = [math.log(ratio) for ratio in ratios]
        mean = statistics.mean(logs)
        half_width = 2.57058 * statistics.stdev(logs) / math.sqrt(6)
        result[name] = dict(block_ratios=ratios, log_ratios=logs, geomean=math.exp(mean),
                            ci95_lower=math.exp(mean - half_width), ci95_upper=math.exp(mean + half_width),
                            t_critical_df5=2.57058)
    result['qualifies_hosted_speed_claim'] = (result['cpu']['geomean'] >= 1.03 and
                                              result['cpu']['ci95_lower'] > 1. and
                                              result['wall']['geomean'] > 1.)
    return result


def validate_protocol(protocol):
    expected = dict(status=READY,
                    primary=dict(bench_depth=11, benches_per_process=12, expected_nodes=419798,
                                 aa_pairs=6, ab_blocks=BLOCK_ORDERS),
                    kernel=dict(iterations=2000000, group='quiet', aa_pairs=6, ab_blocks=BLOCK_ORDERS),
                    calibration=dict(each_ratio_min=.97, each_ratio_max=1.03, median_min=.99, median_max=1.01),
                    analysis=dict(t_critical_df5=2.57058, claim_cpu_geomean_min=1.03,
                                  claim_cpu_lower_ci_exclusive_min=1., claim_wall_geomean_exclusive_min=1.,
                                  blocks=6, confidence=.95), attempts=1, fault_retries=0,
                    bounds=dict(timing_minutes=10, per_process_timeout_seconds=45,
                                no_adaptive_iterations_or_retries=True, no_gameplay=True))
    for key, value in expected.items():
        if isinstance(value, dict):
            if not isinstance(protocol.get(key), dict) or any(protocol[key].get(k) != v for k, v in value.items()):
                raise ValueError('Protocol fixed settings differ: ' + key)
        elif protocol.get(key) != value:
            raise ValueError('Protocol is not reviewed and ready: ' + key)


def run_experiment(args, execute=run_owned):
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    roots = [Path(args.package).resolve(), Path(args.frozen_root).resolve(), Path(__file__).resolve()]
    roots += [Path(getattr(args, name)).resolve() for name in
              ['baseline', 'candidate', 'baseline_kernel', 'candidate_kernel']]
    build_manifest = Path(args.frozen_root).resolve().parent / 'frozen-build-SHA256.json'
    roots.append(build_manifest)
    report = dict(status='running', qualifies_hosted_speed_claim=False,
                  scope='fixed suite on this hosted Linux runner only; no Ryzen, Windows, NPS or Elo inference',
                  primary={}, kernel={}, runs=[], cli=sys.argv, no_retries=True)
    frozen, original_affinity = {}, None
    started = time.monotonic()
    signatures = {}
    try:
        if any(root == out or root in out.parents for root in roots):
            raise ValueError('Result output must be outside every immutable input tree')
        frozen = freeze_inputs(roots)
        save(out / 'initial-inputs.json', dict(sha256=frozen, roots=list(map(str, roots))))
        report['build_freeze_verification'] = verify_build_freeze(Path(args.frozen_root).resolve(), build_manifest)
        protocol = json.loads((Path(args.package) / 'protocol.json').read_text())
        report['protocol'] = protocol
        validate_protocol(protocol)
        original_affinity = os.sched_getaffinity(0)
        cpu = min(original_affinity) if args.cpu is None else args.cpu
        if cpu != min(original_affinity):
            raise ValueError('The registered CPU must be the minimum inherited allowed CPU')
        pin_cpu(cpu)
        report.update(cpu=cpu, inherited_affinity=sorted(original_affinity), host_before=host_context())
        save(out / 'host-before.json', report['host_before'])
        process_limit = min(float(args.timeout), 45.)
        total_limit = min(float(getattr(args, 'total_timeout', 600.)), 600.)
        positive(process_limit, 'per-process timeout')
        positive(total_limit, 'total timeout')

        def trial(kind, phase, index, variant):
            remaining = total_limit - (time.monotonic() - started)
            if remaining <= 0:
                raise TimeoutError('Fixed 600-second timing budget exhausted; no retry')
            label = 'baseline' if variant == 'A' or phase == 'aa' else 'candidate'
            path = getattr(args, label + ('_kernel' if kind == 'kernel' else ''))
            command = [str(Path(path).resolve())]
            stdin = ENGINE_STDIN
            if kind == 'kernel':
                command += ['--group', 'quiet', '--iterations', '2000000']
                stdin = b''
            run_name = '%02d-%s-%s-%02d-%s' % (len(report['runs']) + 1, kind, phase, index, variant)
            planned = dict(name=run_name, kind=kind, phase=phase, index=index, variant=variant,
                           command=command, timeout_seconds=min(process_limit, remaining))
            report['runs'].append(planned)
            save(out / 'report.json', report)
            with (out / 'commands.jsonl').open('a') as log:
                log.write(json.dumps(planned, allow_nan=False) + '\n')
            try:
                raw = execute(command, stdin, out / 'runs' / run_name, cpu, planned['timeout_seconds'])
            except BaseException as error:
                planned['error'] = repr(error)
                save(out / 'report.json', report)
                raise
            planned['process'] = raw
            save(out / 'report.json', report)
            if raw['returncode'] != 0 or raw['timed_out']:
                raise RuntimeError('Process failed or timed out: ' + run_name)
            positive(raw['cpu_seconds'], 'external process CPU seconds')
            positive(raw['wall_seconds'], 'external process wall seconds')
            if Path(raw['stderr']).read_bytes().strip():
                raise ValueError('Unexpected stderr in ' + run_name)
            stdout = Path(raw['stdout']).read_text()
            if kind == 'primary':
                signature = parse_bench(stdout)
                measurement = dict(cpu_seconds=raw['cpu_seconds'], wall_seconds=raw['wall_seconds'])
            else:
                payload = parse_kernel(stdout)
                planned['kernel_record'] = payload
                signature = {key: value for key, value in payload.items()
                             if key not in ['wall_ns', 'cpu_ticks', 'clocks_per_sec']}
                measurement = dict(cpu_seconds=payload['cpu_ticks'] / payload['clocks_per_sec'],
                                   wall_seconds=payload['wall_ns'] / 1e9)
            if kind in signatures and signatures[kind] != signature:
                raise ValueError('Work/signature identity mismatch across frozen inputs: ' + run_name)
            signatures.setdefault(kind, signature)
            planned['measurement'] = measurement
            save(out / 'report.json', report)
            return dict(measurement, variant=variant, run=run_name)

        def calibrate(kind):
            pairs = []
            report[kind]['aa_pairs'] = pairs
            for index in range(6):
                pair = {}
                pairs.append(pair)
                for variant in 'AB':
                    pair[variant] = trial(kind, 'aa', index + 1, variant)
            result = calibration(pairs)
            report[kind]['calibration'] = result
            save(out / 'report.json', report)
            return result['passed']

        def compare(kind):
            blocks = []
            report[kind]['ab_blocks'] = blocks
            for index, order in enumerate(BLOCK_ORDERS, 1):
                block = []
                blocks.append(block)
                for variant in order:
                    block.append(trial(kind, 'ab', index, variant))
            report[kind]['analysis'] = analyze_blocks(blocks)

        if not calibrate('primary'):
            report.update(status='failed_primary_calibration_no_ab')
            report['primary']['ab_status'] = 'skipped_failed_primary_calibration'
            report['kernel']['status'] = 'skipped_failed_primary_calibration'
        else:
            kernel_eligible = calibrate('kernel')
            compare('primary')
            if kernel_eligible:
                compare('kernel')
                # The same numerical diagnostic rule has a deliberately separate name.
                analysis = report['kernel']['analysis']
                analysis['meets_diagnostic_numerical_criterion'] = analysis.pop('qualifies_hosted_speed_claim')
                report['kernel']['status'] = 'completed_diagnostic_only'
            else:
                report['kernel']['status'] = 'failed_kernel_calibration_no_kernel_ab'
            qualifies = report['primary']['analysis']['qualifies_hosted_speed_claim']
            report.update(qualifies_hosted_speed_claim=qualifies,
                          status='completed_hosted_speed_criterion_met' if qualifies else 'completed_no_hosted_speed_claim')
    except (Exception, KeyboardInterrupt) as error:
        report.update(status='failed_or_inconclusive_no_claim', error=repr(error), qualifies_hosted_speed_claim=False)
    finally:
        if frozen:
            report['final_input_rehash'] = rehash_inputs(frozen, roots)
            save(out / 'final-inputs.json', report['final_input_rehash'])
            if report['final_input_rehash']['status'] != 'passed':
                report.update(status='failed_or_inconclusive_no_claim', qualifies_hosted_speed_claim=False,
                              final_input_error='Immutable inputs changed, appeared, disappeared or became unreadable')
        else:
            report['final_input_rehash'] = dict(status='unavailable', reason='Initial freeze did not complete')
        if original_affinity is not None:
            report['host_after'] = host_context()
            save(out / 'host-after.json', report['host_after'])
            try:
                os.sched_setaffinity(0, original_affinity)
            except OSError as error:
                report.update(status='failed_or_inconclusive_no_claim', qualifies_hosted_speed_claim=False,
                              affinity_restore_error=repr(error))
        if not report['status'].startswith('completed_'):
            if 'analysis' in report['primary']:
                report['primary']['analysis']['qualifies_hosted_speed_claim'] = False
            if 'analysis' in report['kernel']:
                report['kernel']['analysis']['meets_diagnostic_numerical_criterion'] = False
        report['elapsed_wall_seconds'] = time.monotonic() - started
        save(out / 'report.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['package', 'out', 'baseline', 'candidate', 'baseline-kernel', 'candidate-kernel', 'frozen-root']:
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--cpu', type=int)
    parser.add_argument('--timeout', type=float, default=45., help='Emergency per-process bound, maximum 45 seconds')
    parser.add_argument('--total-timeout', type=float, default=600., help='Entire finite pilot bound, maximum 600 seconds')
    args = parser.parse_args()
    def interrupted(signum, frame):
        raise InterruptedError('Received signal %d; no retry' % signum)
    signal.signal(signal.SIGTERM, interrupted)
    report = run_experiment(args)
    print(report['status'])
    return 0 if report['status'].startswith('completed_') else 1


if __name__ == '__main__':
    sys.exit(main())
