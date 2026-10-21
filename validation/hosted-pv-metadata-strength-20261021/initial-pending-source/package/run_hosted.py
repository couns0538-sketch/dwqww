#!/usr/bin/env python3
"""Isolated preregistered hosted correction-history strength wrapper; one bounded native 0/+10 Elo test."""
import argparse
import hashlib
import importlib.util
import json
import math
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
CANDIDATE_SHA = 'PENDING_FROZEN_SOURCE22_SHA'
CANDIDATE_BENCHMARK_NODES = 292545  # Prototype GREEN only; actual frozen22 capture remains mandatory/pending.


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


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


def rehash_inputs(frozen):
    """Retain every final hash/read failure, including failed/interrupted paths."""
    rows, mismatches = {}, []
    for name, expected in frozen.items():
        row = {'expected_sha256': expected}
        try:
            row['actual_sha256'] = sha(name)
            row['matches'] = row['actual_sha256'] == expected
        except OSError as error:
            row['error'], row['matches'] = repr(error), False
        rows[name] = row
        if not row['matches']:
            mismatches.append(name)
    return {'status': 'failed' if mismatches else 'passed', 'inputs': rows,
            'mismatches': mismatches}


def ensure_final_inputs(report, frozen):
    result = rehash_inputs(frozen)
    report['final_input_rehash'] = result
    if result['status'] != 'passed':
        report['status'] = 'failed_or_inconclusive_no_acceptance'
        report['final_input_error'] = 'Frozen inputs changed or unavailable: ' + repr(result['mismatches'])
        report.setdefault('error', report['final_input_error'])


def stop_group(process):
    # A leader exit does not establish that its descendants have exited.
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


class FaultScanner:
    """Incremental live fault checks; final independent audits still read raw files."""
    def __init__(self, out):
        self.out = Path(out)
        self.files = {}
        self.bytes_read = 0

    def __call__(self):
        for name in ('console.txt', 'fastchess.log', 'games.pgn'):
            path = self.out / name
            previous = self.files.get(name)
            try:
                with path.open('rb') as source:
                    info = os.fstat(source.fileno())
                    identity = (info.st_dev, info.st_ino)
                    if previous is not None:
                        if identity != previous['identity']:
                            return 'Observed output replacement: ' + name
                        if info.st_size < previous['offset']:
                            return 'Observed output truncation: ' + name
                    offset = previous['offset'] if previous else 0
                    source.seek(offset)
                    added = source.read()
                    after = os.fstat(source.fileno())
                    current = path.stat()
                    if (current.st_dev, current.st_ino) != identity:
                        return 'Observed output replacement: ' + name
                    if after.st_size < offset + len(added):
                        return 'Observed output truncation: ' + name
            except FileNotFoundError:
                if previous is not None:
                    return 'Observed output deletion: ' + name
                continue
            self.bytes_read += len(added)
            raw = (previous['tail'] if previous else b'') + added
            self.files[name] = {'identity': identity, 'offset': offset + len(added),
                                'tail': raw.rsplit(b'\n', 1)[-1]}
            if not added:
                continue
            text = re.sub(r'\x1b\[[0-9;]*m', '', raw.decode(errors='replace'))
            if name == 'games.pgn':
                for termination in re.findall(r'^\[Termination "([^"\n]*)"\]', text, re.M):
                    if termination != 'normal':
                        return 'Non-normal PGN termination: ' + termination
            elif re.search(r'^\s*(?:warning|error|fatal)\b|\[(?:WARN(?:ING)?|ERR(?:OR)?|FATAL)\s*\]',
                           text, re.I | re.M):
                return 'Fastchess warning/error in ' + name
        return None


def run_owned(command, stdout_path, fault_check, seconds):
    """Natural runner completion is normal; wall timeout is an invalid emergency."""
    deadline = None if seconds is None else time.monotonic() + seconds
    with stdout_path.open('w') as stdout:
        process = subprocess.Popen(command, stdout=stdout, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        normal = False
        try:
            while process.poll() is None:
                fault = fault_check()
                if fault:
                    raise RuntimeError('match_fail_fast: ' + fault)
                if deadline is not None and time.monotonic() >= deadline:
                    raise RuntimeError('emergency_wall_deadline_inconclusive; all raw files preserved')
                try:
                    process.wait(timeout=min(0.5, max(0.001, deadline - time.monotonic()))
                                 if deadline is not None else 0.5)
                except subprocess.TimeoutExpired:
                    pass
            fault = fault_check()
            if fault:
                raise RuntimeError('match_fail_fast: ' + fault)
            if process.returncode == 0:
                try:
                    os.killpg(process.pid, 0)
                except ProcessLookupError:
                    pass
                else:
                    raise RuntimeError('Owned descendant survived successful runner exit; no acceptance')
            normal = process.returncode == 0
            return process.returncode
        finally:
            if not normal:
                stop_group(process)


def audit_likelihood(console, penta, pairs, cap, validator):
    if type(pairs) is not int or type(cap) is not int or not 0 < pairs <= cap:
        raise ValueError('Invalid positive pair count/cap')
    if sum(penta) != pairs:
        raise ValueError('Pentanonial total disagrees with pair count')
    decision = validator.native_acceptance(console)
    native_llr = validator.final_llr(console)
    independent_llr = validator.logistic_llr(penta, 0, 10)
    lower, upper = -math.log(19), math.log(19)
    if abs(native_llr - independent_llr) > validator.PRINTED_LLR_TOLERANCE:
        raise ValueError('Independent likelihood disagrees with native two-decimal likelihood')
    if decision == 'H1_accepted':
        if independent_llr < upper - validator.BOUNDARY_NUMERIC_TOLERANCE:
            raise ValueError('Native H1 acceptance lacks independent upper-bound crossing')
    elif decision == 'H0_accepted':
        if independent_llr > lower + validator.BOUNDARY_NUMERIC_TOLERANCE:
            raise ValueError('Native H0 acceptance lacks independent lower-bound crossing')
    elif pairs != cap:
        raise ValueError('SPRT stopped before cap without a native boundary')
    elif not lower < independent_llr < upper:
        raise ValueError('Cap lacks native acceptance despite independent boundary crossing')
    else:
        decision = 'inconclusive_at_pair_cap'
    return decision, {'method': 'Independent constrained multinomial MLE; 100-step bisection',
        'elo0': 0, 'elo1': 10, 'zero_bin_regularization': validator.ZERO_BIN_REGULARIZATION,
        'native_printed_llr': native_llr, 'independent_llr': independent_llr,
        'printed_llr_tolerance': validator.PRINTED_LLR_TOLERANCE,
        'lower_bound': lower, 'upper_bound': upper,
        'boundary_numeric_tolerance': validator.BOUNDARY_NUMERIC_TOLERANCE}


def verify_candidate_bench_signature(stdout, stderr, returncode, expected_nodes):
    matches = re.findall(r'\Ainfo string bench depth 11 nodes ([0-9]+) time ([0-9]+) nps ([0-9]+)(?:\r?\n)?\Z', stdout)
    if (type(expected_nodes) is not int or expected_nodes <= 0 or returncode != 0 or
            stderr or len(matches) != 1 or int(matches[0][0]) != expected_nodes or
            re.search(r'^\s*(?:warning|error|fatal)\b|\[(?:WARN(?:ING)?|ERR(?:OR)?|FATAL)\s*\]', stdout, re.I | re.M)):
        raise ValueError('Candidate bench signature/exit/warning failure')
    return {'engine_nodes': int(matches[0][0]), 'engine_ms': int(matches[0][1]),
            'engine_nps': int(matches[0][2]), 'scope': 'Signature readiness only; no speed comparison'}


def _owned_group_empty(process):
    try:
        os.killpg(process.pid, 0)
    except ProcessLookupError:
        return True
    return False


def candidate_bench_readiness(engine, out, expected_nodes):
    return _owned_readiness_probe(engine, out, expected_nodes, 10)


def verify_uci_transport(stdout, stderr, returncode):
    rows = stdout.splitlines()
    required = ('option name Ponder type check default false',
                'option name Book File type string default <empty>')
    if (returncode != 0 or stderr or rows.count('uciok') != 1 or not rows or rows[-1] != 'uciok' or
            any(rows.count(line) != 1 for line in required) or
            re.search(r'^\s*(?:info string )?(?:warning|error|fatal)\b|\[(?:WARN(?:ING)?|ERR(?:OR)?|FATAL)\s*\]', stdout, re.I | re.M)):
        raise ValueError('UCI transport/handshake/advertisement failure')
    return {'scope': 'Completed UCI handshake and exact required advertisements only'}


def _owned_readiness_probe(engine, out, expected_nodes, guard_seconds,
                           stdin='bench 11\nquit\n', prefix='candidate-bench11', verify_signature=True):
    stdout_path, stderr_path = out / (prefix + '.stdout'), out / (prefix + '.stderr')
    command = {'command': [str(engine)], 'stdin': stdin, 'expected_nodes': expected_nodes,
               'guard_seconds': guard_seconds, 'scope': ('Signature readiness only; no timing ratio' if verify_signature else 'UCI handshake readiness only')}
    save(out / (prefix + '-command.json'), command)
    facts = {**command, 'verdict': 'pending', 'cleanup_attempted': False,
             'returncode_before_verdict': None, 'owned_group_empty_before_verdict': None,
             'stdout_sha256_before_verdict': None, 'stderr_sha256_before_verdict': None}
    process = None
    started = time.monotonic()
    with stdout_path.open('x') as stdout, stderr_path.open('x') as stderr:
        try:
            process = subprocess.Popen(command['command'], stdin=subprocess.PIPE, stdout=stdout,
                                       stderr=stderr, text=True, start_new_session=True)
            facts['pid'] = process.pid
            try:
                process.communicate(input=command['stdin'], timeout=max(.001, guard_seconds - (time.monotonic() - started)))
            finally:
                stdout.flush()
                stderr.flush()
                facts.update(returncode_before_verdict=process.returncode,
                             owned_group_empty_before_verdict=_owned_group_empty(process),
                             stdout_sha256_before_verdict=sha(stdout_path),
                             stderr_sha256_before_verdict=sha(stderr_path))
                # Persist observations before any parser or process-group assertion can fail.
                save(out / (prefix + '-process.json'), facts)
            if verify_signature:
                result = verify_candidate_bench_signature(stdout_path.read_text(), stderr_path.read_text(),
                                                         process.returncode, expected_nodes)
            else:
                result = verify_uci_transport(stdout_path.read_text(), stderr_path.read_text(), process.returncode)
            if not facts['owned_group_empty_before_verdict']:
                raise ValueError('Owned candidate bench descendant survived leader exit')
            result.update(command=command['command'], stdin=command['stdin'], guard_seconds=guard_seconds,
                          elapsed_seconds=time.monotonic() - started,
                          owned_process_group_empty=True, stdout_sha256=sha(stdout_path),
                          stderr_sha256=sha(stderr_path))
            save(out / (prefix + '.json'), result)
            facts['verdict'] = 'passed'
            return result
        except BaseException as error:
            facts.update(verdict='failed', error=repr(error))
            if process is not None:
                facts['cleanup_attempted'] = True
                try:
                    stop_group(process)
                except BaseException as cleanup_error:
                    facts['cleanup_error'] = repr(cleanup_error)
            raise
        finally:
            stdout.flush()
            stderr.flush()
            facts.update(returncode_after_cleanup=process.returncode if process is not None else None,
                         owned_group_empty_after_cleanup=_owned_group_empty(process) if process is not None else None,
                         stdout_sha256_after_cleanup=sha(stdout_path), stderr_sha256_after_cleanup=sha(stderr_path),
                         stdout_sha256=sha(stdout_path), stderr_sha256=sha(stderr_path),
                         elapsed_seconds=time.monotonic() - started)
            save(out / (prefix + '-process.json'), facts)


def require_launch_protocol(cfg):
    if cfg.get('status') != 'PREREGISTERED_REVIEWED_READY_FOR_SINGLE_PUSH':
        raise ValueError('Protocol review has not authorized this frozen package')
    if (cfg.get('baseline_sha') != '2e151d019bc58dff2ab4e76e99ef99516af8d222' or
            cfg.get('candidate_sha') != CANDIDATE_SHA or
            not isinstance(CANDIDATE_SHA, str) or not re.fullmatch('[0-9a-f]{40}', CANDIDATE_SHA) or
            cfg.get('candidate_sha') == cfg.get('baseline_sha') or
            cfg.get('fastchess_sha') != '60d7a7a26c6b0582a15c112fb29a1829bef2adb3' or
            cfg.get('baseline_version') != '6.4.21' or cfg.get('candidate_version') != '6.4.22' or
            cfg.get('baseline_benchmark_nodes') != 321912 or
            type(CANDIDATE_BENCHMARK_NODES) is not int or CANDIDATE_BENCHMARK_NODES <= 0 or
            cfg.get('candidate_benchmark_nodes') != CANDIDATE_BENCHMARK_NODES or
            cfg.get('candidate_bench_capture_status') != 'PASSED_ACTUAL_FROZEN22_CANONICAL_CAPTURE' or
            cfg.get('source_file_counts') != {'baseline':76,'candidate':77} or
            any(cfg.get(key) != 'PASSED' for key in ('source_gates_status', 'source_scope_review_status',
                                                      'root_review_status', 'astra_review_status')) or
            not cfg.get('correctness_evidence_sha256') or
            cfg.get('workflow_status') != 'FROZEN' or
            not isinstance(cfg.get('workflow_sha256'), str) or
            not re.fullmatch('[0-9a-f]{64}', cfg['workflow_sha256']) or
            cfg.get('operational_qualification_status') != 'authorized_for_one_fresh_host_readiness_attempt_with_prior_anomalies_unresolved'):
        raise ValueError('Source freeze, benchmark, workflow and independent reviews are incomplete')
    if cfg.get('aa_settings') != {'pairs':4,'tc':'1+0.01','nodes':0,'identical_moves_required':False,'binary':'baseline'}:
        raise ValueError('Timed baseline AA differs from frozen operational gate')
    if cfg.get('seed') != 20261031 or cfg.get('sprt_settings') != {
            'elo0': 0, 'elo1': 10, 'alpha': .05, 'beta': .05,
            'pair_cap': 512, 'game_cap': 1024, 'tc': '1+0.01',
            'concurrency': 1, 'emergency_seconds': 18000}:
        raise ValueError('Protocol differs from this frozen bounded strength design')


def verify_package_inventory(repo, package):
    """Exact relative-POSIX self inventory, checked before affinity or processes."""
    repo, package = Path(repo).resolve(strict=True), Path(package).resolve(strict=True)
    inventory = package / 'PACKAGE-SHA256SUMS'
    expected = {}
    order = []
    for line in inventory.read_text().splitlines():
        digest, relative = line.split('  ', 1)
        path = Path(relative)
        if (not re.fullmatch('[0-9a-f]{64}', digest) or path.is_absolute() or
                '..' in path.parts or path.as_posix() != relative or relative in expected):
            raise ValueError('Malformed package inventory')
        expected[relative] = digest
        order.append(relative)
    actual = [p.relative_to(repo).as_posix() for p in package.rglob('*') if p.is_file() and p != inventory]
    workflow = repo / '.github/workflows/forge-hosted-pv-metadata-strength.yml'
    if workflow.is_file():
        actual.append(workflow.relative_to(repo).as_posix())
    actual.sort()
    if order != actual or any('__pycache__' in Path(p).parts or p.endswith('.pyc') for p in actual):
        raise ValueError('Package inventory file set/order mismatch')
    for relative in actual:
        if sha(repo / relative) != expected[relative]:
            raise ValueError('Package self hash mismatch: ' + relative)
    return expected


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
    require_launch_protocol(cfg)
    verify_package_inventory(a.repo, a.package)
    workflow = a.repo / '.github/workflows/forge-hosted-pv-metadata-strength.yml'
    if not workflow.is_file() or sha(workflow) != cfg['workflow_sha256']:
        raise ValueError('Future workflow is absent or differs from reviewed freeze')
    proof_paths = []
    for path, digest in cfg['correctness_evidence_sha256'].items():
        proof = Path(path)
        if (proof.is_absolute() or '..' in proof.parts or proof.as_posix() != path or
                not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest) or
                not (a.repo / proof).is_file() or (a.repo / proof).is_symlink() or
                not (a.repo / proof).resolve().is_relative_to(a.repo) or sha(a.repo / proof) != digest):
            raise ValueError('Current root proof hash mismatch: ' + path)
        proof_paths.append(a.repo / proof)
    preflight = {'status': 'checking', 'expected_baseline': cfg['baseline_sha'],
                 'expected_candidate': cfg['candidate_sha'], 'correctness_proofs': [str(p) for p in proof_paths]}
    save(a.out / 'preflight-evidence.json', preflight)
    try:
        evidence = load('correction_required_build_evidence', a.package / 'build_evidence.py')
        build_paths = evidence.verify_build_evidence(a.out.parent, cfg, a.baseline, a.candidate, a.fastchess)
    except BaseException as error:
        preflight.update(status='failed', error=repr(error))
        save(a.out / 'preflight-evidence.json', preflight)
        raise
    preflight.update(status='passed', consumed_build_paths=[str(p) for p in build_paths])
    save(a.out / 'preflight-evidence.json', preflight)
    for key in ('baseline_sha', 'candidate_sha'):
        if not re.fullmatch('[0-9a-f]{40}', cfg[key]):
            raise ValueError('Freeze full commit SHA before launch: ' + key)
    cpu = min(os.sched_getaffinity(0))
    original_affinity = sorted(os.sched_getaffinity(0))
    os.sched_setaffinity(0, {cpu})
    tools = a.package / 'match'
    stats_module = load('hosted_pgn_stats', tools / 'pgn_stats.py')
    validator = load('hosted_windows_validator', a.repo / 'tools/match/windows_validate.py')
    inputs = [a.baseline, a.candidate, a.fastchess,
              a.repo / 'tools/match/windows_validate.py',
              a.baseline.parent / 'libforge_core.a', a.candidate.parent / 'libforge_core.a',
              a.repo / '.github/workflows/forge-hosted-pv-metadata-strength.yml']
    inputs += sorted(path for path in a.package.rglob('*') if path.is_file())
    # Every initially verified proof and mandatory build byte participates in final rehash.
    inputs += proof_paths + build_paths
    frozen = {str(path): sha(path) for path in inputs}
    report = {'status': 'running', 'protocol': cfg, 'frozen_inputs': frozen,
              'original_affinity': original_affinity, 'selected_cpu': cpu,
              'scope': 'Native hosted Linux only; no native Windows/Ryzen claim.',
              'started_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    report['host_context_before'] = host_context()
    save(a.out / 'host-context-before.json', report['host_context_before'])
    save(a.out / 'summary.json', report)

    def interrupted(signum, frame):
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        raise KeyboardInterrupt('Termination signal ' + str(signum))

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)

    def checked_inputs():
        for name, digest in frozen.items():
            if sha(name) != digest:
                raise ValueError('Frozen input changed: ' + name)

    def bench(index, deadline):
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        start = time.perf_counter()
        signature = _owned_readiness_probe(a.baseline, a.out, cfg['baseline_benchmark_nodes'],
            max(.001, deadline - start), prefix='bench-%02d' % index)
        end = time.perf_counter()
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        row = {'index': index, 'warmup': index < 2, 'command': [str(a.baseline)],
               'stdin': 'bench 11\nquit\n', 'wall_seconds': end - start,
               'user_seconds': after.ru_utime - before.ru_utime,
               'system_seconds': after.ru_stime - before.ru_stime,
               'engine_nodes': signature['engine_nodes'], 'engine_ms': signature['engine_ms'],
               'engine_nps': signature['engine_nps']}
        row['cpu_seconds'] = row['user_seconds'] + row['system_seconds']
        save(a.out / ('bench-%02d.json' % index), row)
        return row

    def match(phase, seconds):
        out = a.out / phase
        command = [sys.executable, '-B', str(tools / 'run_match.py'),
                   '--fastchess', str(a.fastchess), '--baseline', str(a.baseline),
                   '--candidate', str(a.baseline if phase == 'aa' else a.candidate),
                   '--openings', str(a.package / ('openings/' + phase + '.epd')),
                   '--out', str(out), '--mode', 'smoke' if phase == 'aa' else 'sprt',
                   '--pairs', '4' if phase == 'aa' else '512', '--seed', str(cfg['seed']),
                   '--tc', '1+0.01', '--cpu', str(cpu),
                   '--hash-mb', '32', '--overhead-ms', '10', '--disable-book']
        save(a.out / (phase + '-command.json'), command)
        scanner = FaultScanner(out)
        code = run_owned(command, a.out / (phase + '-wrapper.stdout'), scanner, seconds)
        if code:
            raise RuntimeError(phase + '_runner_failed; raw files preserved')
        console = re.sub(r'\x1b\[[0-9;]*m', '', (out / 'console.txt').read_text())
        if re.search(r'^\s*(?:warning|error|fatal)\b', console, re.I | re.M):
            raise ValueError('Fastchess console warning/error')
        log = (out / 'fastchess.log').read_text()
        if re.search(r'\[(?:WARN|ERR|FATAL)\s*\]', log):
            raise ValueError('Fastchess log warning/error')
        text = (out / 'games.pgn').read_text()
        stats = stats_module.summarize(text, require_identical_pairs=False)
        pairs = stats['pairs']
        runtime = json.loads((a.package / 'provenance/runtime-order.json').read_text())[phase]
        selected_bytes = (out / 'selected.epd').read_bytes()
        if (sha(out / 'selected.epd') != runtime['selected_epd_sha256'] or
                selected_bytes.decode('ascii').splitlines() != runtime['ordered_fens']):
            raise ValueError('Runtime opening order differs from frozen prospective order')
        expected = runtime['ordered_fens'][:pairs]
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
            decision, likelihood = audit_likelihood(console,
                stats['pentanomial_0_half_1_1half_2'], pairs, 512, validator)
        checked_inputs()
        result = {'statistics': stats, 'decision': decision, 'likelihood_audit': likelihood,
                  'no_screen_reset_resume_or_pooling': True}
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
        report['candidate_bench_signature'] = candidate_bench_readiness(a.candidate, a.out, cfg['candidate_benchmark_nodes'])
        checked_inputs()
        for name in ('baseline', 'candidate'):
            command = [str(getattr(a, name))]
            save(a.out / (name + '-uci-command.json'), {'command': command, 'stdin': 'uci\nquit\n'})
            _owned_readiness_probe(getattr(a, name), a.out, None, 10, stdin='uci\nquit\n',
                                   prefix=name + '-uci', verify_signature=False)
        report['aa'] = match('aa', 90)
        report['status'] = 'aa_passed_starting_sprt'
        save(a.out / 'summary.json', report)
        report['sprt'] = match('sprt', 18000)
        report['status'] = 'completed_independently_audited'
    except BaseException as error:
        report['status'] = 'failed_or_inconclusive_no_acceptance'
        report['error'] = repr(error)
        raise
    finally:
        ensure_final_inputs(report, frozen)
        save(a.out / 'final-input-rehash.json', report['final_input_rehash'])
        report['host_context_after'] = host_context()
        save(a.out / 'host-context-after.json', report['host_context_after'])
        report['finished_utc'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        report['raw_files_preserved_without_trimming'] = True
        save(a.out / 'summary.json', report)
        if report.get('final_input_error'):
            raise RuntimeError(report['final_input_error'])


if __name__ == '__main__':
    main()
