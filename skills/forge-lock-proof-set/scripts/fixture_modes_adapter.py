"""Synthetic receipts exclusively for test_contract_modes.py; NOT engine evidence."""
import hashlib
import json
import pathlib
import sys

name, result_arg, net_sha = sys.argv[1:]
result = pathlib.Path(result_arg)
root = result.parent
out = root.parent
PINS = {'11': 312866, '13': 862329, '16': 3024920, '20': 12389307, '22': 34048354}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


(root / 'executed.txt').write_text('fixture executed: ' + name, encoding='utf-8')
log = root / 'fixture.log'
log.write_text('Synthetic adapter receipt; no native engine executed.\n', encoding='utf-8')
if name.startswith('build_'):
    exe = root / 'candidate.exe'
    exe.write_bytes(b'identical fixture binary')
    profile = root / 'profile.gcda'
    profile.write_bytes(b'fixture profile')
    flags = ['fixture-compiler', '-flto=1', '-ffp-contract=off', '-fno-fast-math']
    metrics = {'binary': exe.name,
               'compile_commands': [flags + ['-fprofile-generate', '-c', 'fixture.cpp'],
                                    flags + ['-fprofile-use', '-Werror', '-o', str(exe)]],
               'profile_files': [{'path': profile.name, 'sha256': sha(profile)}]}
elif name == 'off_pins':
    metrics = {'binary_a_sha256': sha(out / 'build_a/candidate.exe'),
               'binary_b_sha256': sha(out / 'build_b/candidate.exe'),
               'nodes_a': PINS, 'nodes_b': PINS, 'options': {'Threads': 1, 'Hash': 16}}
elif name == 'on_active':
    metrics = {'binary_sha256': sha(out / 'build_a/candidate.exe'), 'nodes': PINS,
               'active_count': 12000,
               'options': {'Threads': 1, 'Hash': 16, 'NNUEWideOutput': True}}
elif name == 'perft':
    metrics = {'binary_sha256': sha(out / 'build_a/candidate.exe'),
               'startpos5': 4865609, 'kiwipete5': 193690690}
elif name.startswith('smoke_'):
    metrics = {'binary_sha256': sha(out / 'build_a/candidate.exe'),
               'threads': 1 if name == 'smoke_t1' else 4,
               'searches': 1, 'completed': True, 'illegal_moves': 0, 'crashes': 0, 'time_forfeits': 0}
elif name == 'asan_ubsan':
    exe = root / 'instrumented.exe'
    exe.write_bytes(b'fixture diagnostic binary')
    metrics = {'instrumented_binary': exe.name,
               'compile_commands': [['fixture-compiler', '-fsanitize=address,undefined']],
               'sanitizers': ['address', 'undefined'], 'runtime_started': True,
               'executed_tests': 1, 'failures': 0}
else:
    raise ValueError(name)
receipt = {'schema': 1, 'status': 'PASS', 'source_commit': 'a' * 40,
           'network_sha256': net_sha, 'metrics': metrics,
           'logs': [{'path': log.name, 'sha256': sha(log)}]}
result.write_text(json.dumps(receipt), encoding='utf-8')
