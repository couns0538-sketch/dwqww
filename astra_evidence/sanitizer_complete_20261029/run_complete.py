#!/usr/bin/env python3
"""Run every registered CTest with sanitizers; separately apply Forge's existing exception policy.

IDEA_SOURCE: Forge opus_round1/ci/run_ci.sh and owner-requested complete sanitizer qualification.
This adds a completeness check; it does not change test expectations or the existing policy.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def completed_tests(log, registered):
    rows = re.findall(r'^\s*(\d+)/(\d+) Test\s+#(\d+):\s+(\S+)\s+(.+)$', log, re.M)
    n = len(registered)
    if len(rows) != n or not n:
        raise ValueError(f'incomplete run: {len(rows)} results for {n} registered tests')
    if {int(row[2]) for row in rows} != set(range(1, n + 1)):
        raise ValueError('duplicate or missing test ids')
    for ordinal, row in enumerate(rows, 1):
        sequence, total, number, name, status = row
        if int(sequence) != ordinal or int(total) != n or registered[int(number)-1] != name:
            raise ValueError('test registry/result mismatch')
        if 'Passed' not in status and '***Failed' not in status:
            raise ValueError(f'test did not finish normally: {name}: {status}')
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', required=True, type=Path)
    ap.add_argument('--build', required=True, type=Path)
    ap.add_argument('--ctest', required=True, type=Path)
    ap.add_argument('--output', required=True, type=Path)
    args = ap.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    reports = out/'sanitizer_reports'
    reports.mkdir()
    record = {'status': 'RUNNING', 'start_utc': datetime.now(timezone.utc).isoformat(),
              'runner_sha256': digest(Path(__file__)), 'pid': os.getpid()}

    def save():
        temporary = out/'receipt.json.tmp'
        temporary.write_text(json.dumps(record, indent=2)+'\n')
        temporary.replace(out/'receipt.json')

    save()
    try:
        policy = out/'repo_known_failure_policy.py'
        policy.write_bytes(subprocess.check_output([
            'git', '-C', str(args.repo), 'show', 'HEAD:opus_round1/ci/check_known_failures.py']))
        record['policy_git_blob'] = subprocess.check_output([
            'git', '-C', str(args.repo), 'rev-parse', 'HEAD:opus_round1/ci/check_known_failures.py'], text=True).strip()
        record['policy_sha256'] = digest(policy)
        record['checkout_head_at_start'] = subprocess.check_output([
            'git', '-C', str(args.repo), 'rev-parse', 'HEAD'], text=True).strip()
        engine = args.build/'forge'
        record['engine_sha256_before'] = digest(engine)
        registry_raw = subprocess.check_output([str(args.ctest), '--test-dir', str(args.build), '--show-only=json-v1'])
        (out/'registered_tests.json').write_bytes(registry_raw)
        names = [test['name'] for test in json.loads(registry_raw)['tests']]
        record['registered_test_count'] = len(names)
        env = dict(os.environ,
                   ASAN_OPTIONS=f'log_path={reports}/asan:detect_leaks=1:abort_on_error=1',
                   UBSAN_OPTIONS=f'log_path={reports}/ubsan:print_stacktrace=1:halt_on_error=1',
                   PYTHONDONTWRITEBYTECODE='1')
        cmd = [str(args.ctest), '--test-dir', str(args.build), '--output-on-failure', '--timeout', '600', '-j1']
        record.update(command=cmd, ASAN_OPTIONS=env['ASAN_OPTIONS'], UBSAN_OPTIONS=env['UBSAN_OPTIONS'])
        save()
        with (out/'ctest.log').open('wb') as log:
            run = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, env=env)
        record['ctest_exit_code'] = run.returncode
        text = (out/'ctest.log').read_text(errors='replace')
        rows = completed_tests(text, names)
        record['completed_tests'] = len(rows)
        record['ctest_passed'] = sum('Passed' in row[4] for row in rows)
        record['ctest_failed'] = [row[3] for row in rows if '***Failed' in row[4]]
        record['engine_sha256_after'] = digest(engine)
        if record['engine_sha256_before'] != record['engine_sha256_after']:
            raise ValueError('engine changed during qualification')
        if run.returncode not in (0, 8):
            raise ValueError(f'unexpected CTest exit {run.returncode}')
        gate_cmd = [sys.executable, str(policy), str(out/'ctest.log'), str(reports)]
        with (out/'policy_gate.log').open('wb') as log:
            gate = subprocess.run(gate_cmd, stdout=log, stderr=subprocess.STDOUT)
        record['policy_gate_command'] = gate_cmd
        record['policy_gate_exit_code'] = gate.returncode
        if gate.returncode:
            raise ValueError('repository sanitizer acceptance policy failed')
        record['status'] = 'QUALIFICATION_PASS_WITH_EXPLICIT_KNOWN_FAILURES'
    except Exception as error:
        record.update(status='FAIL', error=str(error))
    record['end_utc'] = datetime.now(timezone.utc).isoformat()
    save()
    print(json.dumps(record, indent=2), flush=True)
    return 0 if record['status'] == 'QUALIFICATION_PASS_WITH_EXPLICIT_KNOWN_FAILURES' else 1


if __name__ == '__main__':
    sys.exit(main())
