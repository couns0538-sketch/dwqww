#!/usr/bin/env python3
"""Bind the reviewed corrected-harness trial to root's immutable selection."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

BASE = Path('/workspace/forge-nnue-handoff-20261023')
META = Path(__file__).parent
PREP = BASE / 'linux-final-net-repaired-harness-preparation-attempt1'
OUT = Path('/workspace/.cloud-setup/nnue-final-linux-a52efa5f7864-repaired-harness-attempt1')
NET = BASE / 'full-trained-net-freeze-attempt1/nnue_weights.inc'
FREEZE = NET.with_name('FREEZE.json')
NET_SHA = 'a52efa5f7864b04d0e8fceb3b14af4fc4970e0bb0a0a8706be0959b0bbb98df7'
ENGINE = '6e9622fd5be18e0155fc3ed5fcf6c4586705cca6'
TEST_COMMIT = 'f4a1ed6be3921a024e0d876cac2433153a96c66c'
TEST_SHA = '6dec8511d6107511cae182dc6169122b48b41e00c5033738f8b04ab027441dce'
GIT = ['/usr/bin/git', '-C', '/workspace/dwqww']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(name, value):
    with (META / name).open('x') as stream:
        json.dump(value, stream, indent=2); stream.write('\n')


def read_git(label, args):
    command = GIT + args
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    with (META / (label + '.stdout')).open('xb') as stream:
        stream.write(result.stdout)
    with (META / (label + '.stderr')).open('xb') as stream:
        stream.write(result.stderr)
    save(label + '.command.json', {'argv': command, 'returncode': result.returncode,
                                  'stdout_sha256': sha(result.stdout), 'stderr_sha256': sha(result.stderr)})
    if result.returncode:
        raise ValueError('Read-only Git identity query failed')
    return result.stdout


def main():
    if OUT.exists():
        raise ValueError('Fresh corrected-harness output required')
    identity = [(NET, NET_SHA),
                (FREEZE, '3d945dc1f0e20d3469791eeb36b9ad5b23a1e70c87f6615703d0fda3442e211c'),
                (PREP / 'run_linux_trial.py', '3990a9b643bfb4c6133cb72cd1c0b4eebf66f302bc8114df96810b8083523b8b'),
                (PREP / 'export_trial.py', 'e908b4b7bb25c7299616bcb998a4af6ef31fc616a1b6c8460baf1a14e01b4897'),
                (PREP / 'PINS.json', 'ce2549801f1710a0ef9989d018c077572a98f5bf2d13fb77cee18d374de2269e'),
                (BASE / 'linux-final-net-repaired-harness-review-attempt1/REVIEW.json',
                 '87fdaa18ce6e8f49a50c72315949328f5ea3d2af71bf921ed9d68b8a289ae56b')]
    for path, expected_sha in identity:
        if sha(path.read_bytes()) != expected_sha:
            raise ValueError('Frozen input/review identity differs: ' + str(path))
    freeze = json.loads(FREEZE.read_text())
    if freeze['chosen']['inc_sha256'] != NET_SHA:
        raise ValueError('Root selection receipt does not select this include')
    rows = read_git('clean-engine-tree', ['ls-tree', '-r', '-z', ENGINE, '--',
                                        'CMakeLists.txt', 'LICENSE', 'include', 'src', 'bench', 'tests', 'tools']).split(b'\0')
    expected = {}; skipped = []
    for row in rows:
        if not row:
            continue
        prefix, raw_name = row.split(b'\t', 1)
        mode, kind, oid = prefix.decode().split(); name = raw_name.decode()
        if name.endswith('.pyc'):
            skipped.append(name); continue
        if kind != 'blob' or mode not in ('100644', '100755'):
            raise ValueError('Unexpected clean source-tree entry')
        data = subprocess.check_output(GIT + ['cat-file', 'blob', oid])
        expected[name] = {'sha256': sha(data), 'git_mode': mode, 'git_blob': oid, 'bytes': len(data),
                          'origin_commit': ENGINE}
    test_row = read_git('authorized-test-blob', ['ls-tree', '-z', TEST_COMMIT, '--', 'tests/tests.cpp']).rstrip(b'\0')
    prefix, raw_name = test_row.split(b'\t', 1)
    mode, kind, oid = prefix.decode().split()
    test = subprocess.check_output(GIT + ['cat-file', 'blob', oid])
    if raw_name != b'tests/tests.cpp' or kind != 'blob' or mode != '100644' or sha(test) != TEST_SHA:
        raise ValueError('Exact authorized test repair differs')
    expected['tests/tests.cpp'] = {'sha256': TEST_SHA, 'git_mode': mode, 'git_blob': oid,
                                   'bytes': len(test), 'origin_commit': TEST_COMMIT}
    if len(expected) != 74 or expected['src/nnue_weights.inc']['sha256'] != NET_SHA:
        raise ValueError('Exact74 selected-engine/test contract differs')
    save('EXPECTED-SOURCE.json', {'clean_engine_source_commit': ENGINE, 'test_harness_commit': TEST_COMMIT,
                                'test_harness_sha256': TEST_SHA, 'source_files_count': 74,
                                'source_files': expected, 'omitted_historical_pyc_only': skipped})
    command = ['/workspace/.cloud-setup/nnue-pipeline-20261023-venv/bin/python', '-B',
               str(PREP / 'run_linux_trial.py'), '--inc', str(NET), '--sha256', NET_SHA,
               '--pins', str(PREP / 'PINS.json'), '--out', str(OUT)]
    save('BOUND-INVOCATION.json',
         {'status': 'BOUND_SELECTED_ENGINE_AND_EXACT_AUTHORIZED_TEST_REPAIR_BEFORE_EXECUTION',
          'utc': datetime.now(timezone.utc).isoformat(), 'argv': command,
          'identities': [{'path': str(path), 'sha256': digest} for path, digest in identity],
          'clean_engine_source_commit': ENGINE, 'test_harness_commit': TEST_COMMIT,
          'expected_source_manifest_sha256': sha((META / 'EXPECTED-SOURCE.json').read_bytes()),
          'wrapper_sha256': sha(Path(__file__).read_bytes()),
          'scope': 'Fresh exact corrected-harness qualification; original failures preserved; no engine/source algorithm changes, NPS or Elo'})
    with (META / 'runner.stdout').open('xb') as stdout, (META / 'runner.stderr').open('xb') as stderr:
        result = subprocess.run(command, stdout=stdout, stderr=stderr,
                                env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, check=False)
    save('runner.result.json', {'returncode': result.returncode, 'utc': datetime.now(timezone.utc).isoformat()})
    print('CORRECTED_LINUX_RUNNER_RC', result.returncode, flush=True)
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
