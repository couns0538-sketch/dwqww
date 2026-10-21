#!/usr/bin/env python3
"""One actual new-policy regression linked to the retained original22 core."""
import ctypes
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import time

REPO = Path('/workspace/dwqww')
HERE = Path(__file__).resolve().parent
OUT = HERE / 'parent-policy-red-attempt1'
BUILD = Path('/workspace/.cloud-setup/tt-refresh-parent-policy-red')
CORE = Path('/workspace/.cloud-setup/pv-metadata-native-release/libforge_core.a')
SOURCE = REPO / 'tests/tt_coherence_tests.cpp'
HEADER = Path('/workspace/.cloud-setup/pv-metadata-native-source/include/forge/search.hpp')
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(CORE) == '374275cc7f3d973204747e8c0befae30d0a0c8f495a7f36dda96fa275fe720b6'
assert sha(SOURCE) == 'cc2fe3e9fb0059f409876345e8cfb3c008ede401751a4dad76b022f743238fd5'
assert ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0) == 0
spec = importlib.util.spec_from_file_location('facts', REPO / 'validation/tt-generation-investigation-20261021/process_facts.py')
facts_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(facts_module)
OUT.mkdir(exist_ok=False)
BUILD.mkdir(exist_ok=False)
(OUT / 'tt_coherence_tests.cpp').write_bytes(SOURCE.read_bytes())
inputs = {'core': CORE, 'new_policy_test_source': SOURCE, 'parent_header': HEADER, 'driver': Path(__file__).resolve()}
before = {name: sha(path) for name, path in inputs.items()}
result = {'status': 'RUNNING', 'utc': datetime.now(timezone.utc).isoformat(),
          'baseline_source_commit': 'ff2e269c6058be84456e3b98344826d17b0056eb',
          'purpose': 'Expected policy contrast, not a claim of a parent correctness defect',
          'inputs': {name: str(path) for name, path in inputs.items()}, 'input_sha256_before': before, 'steps': []}
def save():
    (OUT / 'RESULT.json').write_text(json.dumps(result, indent=2) + '\n')
save()
def run(label, command, timeout, expected_exit):
    p = None
    code = None
    timed_out = False
    error = None
    start = time.monotonic()
    with (OUT / (label + '.stdout')).open('xb') as stdout, (OUT / (label + '.stderr')).open('xb') as stderr:
        try:
            p = subprocess.Popen(command, cwd=REPO, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, stdout=stdout, stderr=stderr, start_new_session=True)
            try:
                code = p.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                os.killpg(p.pid, signal.SIGKILL)
                code = p.wait(timeout=10)
        except BaseException as exc:
            error = repr(exc)
        finally:
            clean = facts_module.cleanup(p.pid) if p else {'no_live_owned_processes': True, 'not_started': True}
    result['steps'].append({'label': label, 'command': command, 'timeout_seconds': timeout,
                            'expected_exit': expected_exit, 'exit_code': code, 'timed_out': timed_out,
                            'error': error, 'cleanup': clean, 'pid': p.pid if p else None,
                            'elapsed_seconds_operational_only': time.monotonic() - start,
                            'stdout_sha256': sha(OUT / (label + '.stdout')), 'stderr_sha256': sha(OUT / (label + '.stderr'))})
    save()
    assert code == expected_exit and not timed_out and error is None
    assert clean['no_live_owned_processes'] and not clean.get('unexpected_live_members_after_command', False)
try:
    executable = BUILD / 'forge_tt_policy_red'
    run('compile', ['/usr/bin/g++-14', '-std=c++20', '-O3', '-DNDEBUG', '-march=x86-64-v3', '-mtune=znver5', '-fno-fast-math', '-ffp-contract=off', '-fno-lto', '-I/workspace/.cloud-setup/pv-metadata-native-source/include', str(OUT / 'tt_coherence_tests.cpp'), str(CORE), '-pthread', '-o', str(executable)], 120, 0)
    result['executable_sha256'] = sha(executable)
    save()
    run('actual-parent-policy-red', [str(executable)], 30, 1)
    assert (OUT / 'actual-parent-policy-red.stderr').read_bytes() == b'FAIL: old occupied hit did not refresh only generation bits\n'
    assert (OUT / 'actual-parent-policy-red.stdout').read_bytes() == b''
    result['input_sha256_after'] = {name: sha(path) for name, path in inputs.items()}
    assert result['input_sha256_after'] == before
    result['status'] = 'PASS_EXPECTED_OLD_POLICY_CONTRAST'
finally:
    if result['status'] == 'RUNNING':
        result['status'] = 'FAILED_ATTEMPT_RETAINED'
    result['completed_utc'] = datetime.now(timezone.utc).isoformat()
    save()
print(json.dumps({'status': result['status'], 'expected_parent_exit': 1, 'candidate_execution': False}))
