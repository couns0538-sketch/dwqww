#!/usr/bin/env python3
"""Export the selected clean engine plus one explicitly pinned test-harness repair."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

BASE = '1ab50b2dd64d9b2f752f7f1285f6968cad2fd792'
CLEAN_ENGINE = '6e9622fd5be18e0155fc3ed5fcf6c4586705cca6'
TEST_COMMIT = 'f4a1ed6be3921a024e0d876cac2433153a96c66c'
TEST_SHA256 = '6dec8511d6107511cae182dc6169122b48b41e00c5033738f8b04ab027441dce'
REPO = Path('/workspace/dwqww')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inc', required=True, type=Path)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--manifest', required=True, type=Path)
    args = parser.parse_args()
    net = args.inc.resolve()
    source = args.source.resolve()
    manifest = args.manifest.resolve()
    if source.exists() or manifest.exists():
        raise ValueError('Fresh paths required; preserve every previous attempt')
    net_bytes = net.read_bytes()
    if sha(net_bytes) != args.sha256:
        raise ValueError('Explicit frozen network checksum differs')
    sys.path.insert(0, str(REPO / 'tools/nnue'))
    from include_parser import load_include
    info = load_include(net, expected_hidden=128)
    if info['sha256'] != args.sha256 or not info['residual']:
        raise ValueError('Expected the frozen checksum and residual=1 include')
    clean_delta = subprocess.check_output(['git', '-C', str(REPO), 'diff-tree', '--no-commit-id',
                                           '--name-only', '-r', BASE, CLEAN_ENGINE]).decode().splitlines()
    clean_net = subprocess.check_output(['git', '-C', str(REPO), 'show', CLEAN_ENGINE + ':src/nnue_weights.inc'])
    repaired_test = subprocess.check_output(['git', '-C', str(REPO), 'show', TEST_COMMIT + ':tests/tests.cpp'])
    if clean_delta != ['src/nnue_weights.inc'] or clean_net != net_bytes:
        raise ValueError('Selected include is not the exact clean net-only engine commit')
    if sha(repaired_test) != TEST_SHA256:
        raise ValueError('Exact authorized controlled null-pruning test repair differs')
    command = ['git', '-C', str(REPO), 'ls-tree', '-r', '-z', BASE, '--',
        'CMakeLists.txt', 'LICENSE', 'include', 'src', 'bench', 'tests', 'tools']
    rows = subprocess.check_output(command).split(b'\0')
    baseline, modes, skipped = {}, {}, []
    for row in rows:
        if not row:
            continue
        prefix, raw_name = row.split(b'\t', 1)
        mode, kind, object_id = prefix.decode('ascii').split()
        name = raw_name.decode('utf-8')
        if name.endswith('.pyc'):
            skipped.append(name)
            continue
        if kind != 'blob' or mode not in ('100644', '100755'):
            raise ValueError('Unexpected source-tree entry')
        data = subprocess.check_output(['git', '-C', str(REPO), 'cat-file', 'blob', object_id])
        baseline[name] = sha(data)
        modes[name] = mode
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        target.chmod(0o755 if mode == '100755' else 0o644)
    actual = {str(p.relative_to(source)): sha(p.read_bytes()) for p in source.rglob('*') if p.is_file()}
    if actual != baseline:
        raise ValueError('Pristine export differs from exact Git blobs')
    (source / 'src/nnue_weights.inc').write_bytes(net_bytes)
    (source / 'tests/tests.cpp').write_bytes(repaired_test)
    after = {str(p.relative_to(source)): sha(p.read_bytes()) for p in source.rglob('*') if p.is_file()}
    changed = sorted(name for name in baseline if after[name] != baseline[name])
    if set(after) != set(baseline) or changed != ['src/nnue_weights.inc', 'tests/tests.cpp']:
        raise ValueError('Expected only the chosen include and exact pinned test-harness repair')
    if net.read_bytes() != net_bytes:
        raise ValueError('Frozen include changed during export')
    record = {'status': 'EXPORTED_CLEAN_ENGINE_WITH_PINNED_TEST_REPAIR_NOT_BUILT', 'baseline': BASE,
        'clean_engine_source_commit': CLEAN_ENGINE, 'test_harness_commit': TEST_COMMIT,
        'test_harness_sha256': TEST_SHA256, 'delta_from_clean_engine_commit': ['tests/tests.cpp'],
        'all_files_match_clean_engine_commit_except_exact_pinned_test': True,
        'source': str(source), 'chosen_include': str(net), 'chosen_include_sha256': args.sha256,
        'hidden': info['hidden'], 'residual': info['residual'], 'source_files': len(after),
        'changed_paths': changed, 'baseline_sha256': baseline, 'source_sha256': after,
        'git_modes': modes, 'omitted_historical_pyc_only': skipped,
        'export_helper_sha256': sha(Path(__file__).read_bytes()),
        'include_parser_sha256': sha((REPO / 'tools/nnue/include_parser.py').read_bytes()),
        'scope': 'Exact clean net-only engine commit plus authorized controlled-NMP test repair only; no production source, Git mutation, build or acceptance'}
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with manifest.open('x') as stream:
        stream.write(json.dumps(record, indent=2) + '\n')
    print(json.dumps({k: record[k] for k in ('status', 'baseline', 'source_files', 'changed_paths', 'chosen_include_sha256')}, indent=2))


if __name__ == '__main__':
    main()
