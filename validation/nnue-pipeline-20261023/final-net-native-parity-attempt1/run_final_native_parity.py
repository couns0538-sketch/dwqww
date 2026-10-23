#!/usr/bin/env python3
"""Frozen final-network native parity only. Saves all actual command receipts."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

REPO = Path('/workspace/dwqww')
OUT = Path('/workspace/forge-nnue-handoff-20261023/final-net-native-parity-attempt1')
BUILD = Path('/workspace/.cloud-setup/nnue-final-native-probe-attempt1')
COMMIT = '6e9622fd5be18e0155fc3ed5fcf6c4586705cca6'
WEIGHTS = Path('/workspace/forge-nnue-handoff-20261023/full-trained-net-freeze-attempt1/nnue_weights.inc')
FREEZE = WEIGHTS.parent / 'FREEZE.json'
ARCHIVE = Path('/workspace/.cloud-setup/nnue-pipeline-20261023-working-build/libforge_core.a')
PROBE_SOURCE = REPO / 'tools/nnue/engine_probe.cpp'
PARITY_TEST = REPO / 'tools/nnue/tests/test_engine_parity.py'
TRAINER = REPO / 'tools/nnue/train_nnue.py'
SAMPLE = REPO / 'tools/nnue/examples/forge_sample.txt'
PYTHON = '/workspace/.cloud-setup/nnue-pipeline-20261023-venv/bin/python'
COMPILER = '/usr/bin/g++-14'
SCOPE = 'Final frozen chosen-network native inference parity only; no CTest, bench, training, search, Windows, speed, loss, Elo or acceptance conclusion.'
EXPECTED = {
    str(WEIGHTS): 'a52efa5f7864b04d0e8fceb3b14af4fc4970e0bb0a0a8706be0959b0bbb98df7',
    str(FREEZE): '3d945dc1f0e20d3469791eeb36b9ad5b23a1e70c87f6615703d0fda3442e211c',
    str(ARCHIVE): 'aed0d79eb7bb2a997ea1ec59605e85dda49e84abacebc549e35b55817cbe2906',
    str(PROBE_SOURCE): 'a4d584955d9cdf1185b6bec6efe884d90babf1a7bbcb79de1b0c40f69b647629',
    str(PARITY_TEST): 'e2107a375c39dfd83ef276b3018f5f5665dfdb7b7835b772ca820d7dd3510d3a',
    str(TRAINER): 'afd8fc9da5a439c307f74670a8fe7950860912763407eaad5f104c7bb96c050c',
    str(REPO / 'tools/nnue/include_parser.py'): '48cc169f506e9975c239001bbe3ef5fd220d68c0e0ecc68b16dc4145d3f0d32b',
    str(SAMPLE): 'ab429836ee5920e92a61bfb09cf29c15318a7b0e3d63643cf176d1d0962ee0bb',
    str(REPO / 'include/forge/nnue.hpp'): 'd87106d1716388375332ea20e97d9a703c74f479ffa5236c75608b356ab5aace',
}
COMMANDS = []
ENV = os.environ.copy()
ENV['PYTHONDONTWRITEBYTECODE'] = '1'

def now():
    return datetime.now(timezone.utc).isoformat()

def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()

def sha(path):
    return sha_bytes(Path(path).read_bytes())

def dump(path, obj):
    with Path(path).open('x') as stream:
        stream.write(json.dumps(obj, indent=2) + '\n')

def write_bytes(path, data):
    with Path(path).open('xb') as stream:
        stream.write(data)

def run(stem, command, timeout=180):
    command = [str(part) for part in command]
    dump(OUT / (stem + '.command.json'), {'command': command, 'cwd': str(REPO), 'environment_overrides': {'PYTHONDONTWRITEBYTECODE': '1'}})
    started, start = now(), time.monotonic()
    stdout, stderr = OUT / (stem + '.stdout'), OUT / (stem + '.stderr')
    timed_out = False
    with stdout.open('xb') as out_stream, stderr.open('xb') as err_stream:
        process = subprocess.Popen(command, cwd=REPO, env=ENV, stdout=out_stream, stderr=err_stream)
        try:
            returncode = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            returncode = process.wait()
    receipt = {'command': command, 'cwd': str(REPO), 'pid': process.pid,
               'started_utc': started, 'finished_utc': now(), 'elapsed_seconds': time.monotonic() - start,
               'returncode': returncode, 'timed_out': timed_out,
               'stdout_sha256': sha(stdout), 'stderr_sha256': sha(stderr),
               'stdout_bytes': stdout.stat().st_size, 'stderr_bytes': stderr.stat().st_size}
    dump(OUT / (stem + '.receipt.json'), receipt)
    COMMANDS.append(receipt)
    print(json.dumps({'phase': stem, 'returncode': returncode, 'timed_out': timed_out}), flush=True)
    if returncode != 0 or timed_out:
        raise RuntimeError(stem + ' failed; actual returncode=' + str(returncode))
    return stdout.read_bytes()

def main():
    dump(OUT / 'DRIVER-START.json', {'utc': now(), 'driver_sha256': sha(__file__), 'scope': SCOPE})
    BUILD.mkdir(parents=True, exist_ok=False)
    original = {name: sha(name) for name in EXPECTED}
    original[str(REPO / 'src/nnue.cpp')] = sha(REPO / 'src/nnue.cpp')
    original[str(REPO / 'src/nnue_weights.inc')] = sha(REPO / 'src/nnue_weights.inc')
    dump(OUT / 'ORIGINAL-INPUTS.json', original)
    for name, expected in EXPECTED.items():
        if original[name] != expected:
            raise ValueError('Frozen input hash differs: ' + name)
    resolved = run('git-resolve-commit', ['git', 'rev-parse', COMMIT + '^{commit}']).decode().strip()
    if resolved != COMMIT:
        raise ValueError('Clean source commit identity differs')
    diff = run('git-net-only-diff', ['git', 'diff-tree', '--no-commit-id', '--name-status', '-r', COMMIT]).decode().strip()
    if diff != 'M\tsrc/nnue_weights.inc':
        raise ValueError('Commit is not the expected net-only change')
    source = run('git-export-nnue-source', ['git', 'show', COMMIT + ':src/nnue.cpp'])
    if sha_bytes(source) != '86aec39feecf029e73510e7e5fadf9e9878c94744f0380c4149edf04da02cdcd':
        raise ValueError('Clean nnue.cpp hash differs')
    git_weights = run('git-export-net-identity', ['git', 'show', COMMIT + ':src/nnue_weights.inc'])
    if sha_bytes(git_weights) != EXPECTED[str(WEIGHTS)]:
        raise ValueError('Git committed network differs from frozen include')
    headers = run('git-list-headers', ['git', 'ls-tree', '-r', '--name-only', COMMIT, '--', 'include']).decode().splitlines()
    header_identity = {}
    for index, relative in enumerate(headers):
        data = run('git-header-' + str(index), ['git', 'show', COMMIT + ':' + relative])
        current_sha = sha(REPO / relative)
        original[str(REPO / relative)] = current_sha
        header_identity[relative] = {'git_sha256': sha_bytes(data), 'current_sha256': current_sha, 'equal': sha_bytes(data) == current_sha}
        if not header_identity[relative]['equal']:
            raise ValueError('Current build header differs from Git commit: ' + relative)
    dump(OUT / 'HEADER-IDENTITY.json', header_identity)
    write_bytes(BUILD / 'nnue.cpp', source)
    write_bytes(BUILD / 'nnue_weights.inc', WEIGHTS.read_bytes())
    if sha(BUILD / 'nnue.cpp') != sha_bytes(source) or sha(BUILD / 'nnue_weights.inc') != EXPECTED[str(WEIGHTS)]:
        raise ValueError('Private source/include copy differs')
    run('compiler-version', [COMPILER, '--version'])
    flags = ['-std=gnu++20', '-O3', '-DNDEBUG', '-march=x86-64-v3', '-mtune=znver5',
             '-fno-fast-math', '-ffp-contract=off', '-fno-lto', '-Wall', '-Wextra',
             '-Wpedantic', '-Wconversion', '-Wshadow', '-DFORGE_NNUE_HIDDEN=128', '-I', str(REPO / 'include')]
    obj, probe, linkmap = BUILD / 'nnue-final.o', BUILD / 'forge_nnue_probe', BUILD / 'probe-link.map'
    run('compile-nnue', [COMPILER, *flags, '-c', BUILD / 'nnue.cpp', '-o', obj])
    run('link-probe', [COMPILER, *flags, PROBE_SOURCE, obj, ARCHIVE, '-pthread', '-Wl,-Map,' + str(linkmap), '-o', probe])
    linkmap_bytes = linkmap.read_bytes()
    write_bytes(OUT / 'probe-link.map', linkmap_bytes)
    if b'nnue.cpp.o' in linkmap_bytes:
        raise ValueError('Old archive nnue.cpp.o appears in link map')
    if ('LOAD ' + str(obj)).encode() not in linkmap_bytes:
        raise ValueError('Explicit chosen-network object missing from link map')
    artifacts = {str(path): {'sha256': sha(path), 'bytes': path.stat().st_size}
                 for path in [BUILD / 'nnue.cpp', BUILD / 'nnue_weights.inc', obj, probe, linkmap]}
    provenance = {'scope': SCOPE, 'source_commit': COMMIT, 'driver_sha256': sha(__file__),
                  'original_inputs_sha256': original, 'expected_frozen_inputs_sha256': EXPECTED,
                  'private_artifacts': artifacts, 'old_archive_nnue_member_absent_from_link_map': True,
                  'explicit_object_before_archive': True, 'flags': flags, 'commands': COMMANDS.copy()}
    dump(OUT / 'BUILD-PROVENANCE.json', provenance)
    run('parity-run', [PYTHON, '-B', PARITY_TEST, '--probe', probe, '--weights', WEIGHTS,
                      '--trainer', TRAINER, '--sample', SAMPLE, '--positions', '2048',
                      '--seed', '20261023', '--out', OUT / 'parity'], timeout=300)
    result = json.loads((OUT / 'parity/RESULT.json').read_text())
    unchanged = {name: sha(name) == value for name, value in original.items()}
    dump(OUT / 'POST-RUN-INPUT-IDENTITY.json', unchanged)
    if not all(unchanged.values()):
        raise ValueError('Original build/test input changed during parity')
    if not (result['status'] == 'PASS' and result['positions'] == 2048 and result['seed'] == 20261023
            and result['hidden_size'] == 128 and result['residual_mode'] is True
            and result['weights_sha256'] == EXPECTED[str(WEIGHTS)] and not result['changed_inputs']):
        raise ValueError('Final native parity result differs from frozen run requirements')
    final = {'status': 'PASS_FINAL_CHOSEN_NET_NATIVE_PARITY_ONLY', 'scope': SCOPE, 'utc': now(),
             'source_commit': COMMIT, 'driver_sha256': sha(__file__), 'weights_sha256': sha(WEIGHTS),
             'freeze_sha256': sha(FREEZE), 'probe_sha256': sha(probe), 'object_sha256': sha(obj),
             'parity_result_sha256': sha(OUT / 'parity/RESULT.json'), 'parity_returncode': COMMANDS[-1]['returncode'],
             'positions': result['positions'], 'exact_integer_matches': result['exact_integer_matches'],
             'within_one_cp': result['within_one_cp'], 'maximum_integer_cp_error': result['maximum_integer_cp_error'],
             'feature_mismatch_count': result['feature_mismatch_count'],
             'hce_only_records_match': result['hce_only_records_match'],
             'filter_flags_match_python_chess': result['filter_flags_match_python_chess'],
             'invalid_input_controls': result['invalid_input_controls'],
             'corpus_origins': result['corpus_origins'],
             'special_first_moves_included_before_walk': result['special_first_moves_included_before_walk'],
             'activation_categories': result['activation_categories'],
             'all_original_inputs_unchanged': all(unchanged.values()),
             'old_archive_nnue_member_absent_from_link_map': True,
             'command_receipt_files': [str(OUT / (name + '.receipt.json')) for name in ['compiler-version','compile-nnue','link-probe','parity-run']]}
    dump(OUT / 'NATIVE-PARITY.json', final)
    text = ('# Final chosen-network native inference parity\n\n'
            'Status: **PASS — native inference parity only.**\n\n'
            f"The final frozen H128 residual include `{sha(WEIGHTS)}` matched the shared Python trainer on "
            f"{result['exact_integer_matches']}/{result['positions']} integer scores exactly; maximum integer error "
            f"{result['maximum_integer_cp_error']} cp, feature mismatches {result['feature_mismatch_count']}. "
            'HCE-only records and legal/filter flags matched; all three invalid-input controls were rejected.\n\n'
            'Compiler, NNUE-object compilation, link and parity processes exited 0. The explicit chosen-network object preceded the immutable archive; its old nnue.cpp.o member is absent from the retained link map. All original source/header/tool/network inputs remained unchanged. Exact commands, streams, actual exits, source/object/executable hashes and the unchanged shared test output are preserved beside this report.\n\n'
            + SCOPE + '\n')
    with (OUT / 'NATIVE-PARITY.md').open('x') as stream:
        stream.write(text)
    print(json.dumps(final, indent=2), flush=True)
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        failure = {'status': 'FAIL_PRESERVED', 'utc': now(), 'error': str(error),
                   'traceback': traceback.format_exc(), 'commands_completed': COMMANDS, 'scope': SCOPE}
        if not (OUT / 'FAILURE.json').exists():
            dump(OUT / 'FAILURE.json', failure)
        traceback.print_exc()
        sys.exit(1)
