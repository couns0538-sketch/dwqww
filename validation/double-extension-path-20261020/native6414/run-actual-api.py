#!/usr/bin/env python3
"""Compile only the independent driver, then run it with a hard process-group deadline."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

p = argparse.ArgumentParser()
p.add_argument('--build', type=Path, required=True)
p.add_argument('--output-dir', type=Path, required=True)
p.add_argument('--binary-dir', type=Path, required=True)
p.add_argument('--label', required=True)
p.add_argument('--sanitizer', choices=('none', 'thread', 'address'), default='none')
p.add_argument('--source-root', type=Path)
p.add_argument('--optimization', choices=('O2', 'O3'), default='O3')
p.add_argument('--non-pie', action='store_true')
args = p.parse_args()
root = Path("/workspace/dwqww")
out = args.output_dir.resolve()
out.mkdir(parents=True, exist_ok=False)
source = Path(__file__).resolve().parent / 'actual-api-concurrency.cpp'
args.binary_dir.mkdir(parents=True, exist_ok=True)
binary = args.binary_dir.resolve() / ('actual-api-concurrency-' + args.label)
if binary.exists(): raise SystemExit('Refusing existing driver binary: ' + str(binary))
core = args.build.resolve() / 'libforge_core.a'
engine_source = args.source_root.resolve() if args.source_root else root
result = dict(label=args.label, sanitizer=args.sanitizer, status='running', stages=[],
              engine_source_root=str(engine_source),
              sanitizer_options={name: os.environ.get(name) for name in
                                 ('ASAN_OPTIONS', 'UBSAN_OPTIONS', 'TSAN_OPTIONS')})

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save():
    (out / (args.label + '-actual-api.json')).write_text(json.dumps(result, indent=2) + '\n')

def execute(command, stage, timeout):
    record = dict(stage=stage, command=command, timeout_seconds=timeout)
    result['stages'].append(record)
    save()
    started = time.monotonic_ns()
    proc = subprocess.Popen(command, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            start_new_session=True)
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        stdout, stderr = proc.communicate(timeout=10)
        record['timed_out'] = True
    (out / (args.label + '-' + stage + '.stdout')).write_bytes(stdout)
    (out / (args.label + '-' + stage + '.stderr')).write_bytes(stderr)
    record['exit_code'] = proc.returncode
    record['elapsed_seconds'] = (time.monotonic_ns() - started) / 1e9
    record['stdout_sha256'] = hashlib.sha256(stdout).hexdigest()
    record['stderr_sha256'] = hashlib.sha256(stderr).hexdigest()
    save()
    return not record.get('timed_out') and proc.returncode == 0, stdout, stderr

result['sha256_before'] = {str(path.relative_to(root)) if path.is_relative_to(root) else str(path): digest(path)
                           for path in (Path(__file__).resolve(), source, engine_source / 'include/forge/search.hpp',
                                        engine_source / 'src/search.cpp', core)}
flags = ['-std=c++20', '-' + args.optimization, '-DNDEBUG', '-march=x86-64-v3', '-mtune=znver5',
         '-fno-fast-math', '-ffp-contract=off', '-fno-lto', '-Wall', '-Wextra', '-Wpedantic',
         '-Wconversion', '-Wshadow']
if args.non_pie:
    flags += ['-fno-pie', '-no-pie']
if args.sanitizer == 'thread':
    flags += ['-fsanitize=thread', '-g', '-fno-omit-frame-pointer']
elif args.sanitizer == 'address':
    flags += ['-fsanitize=address,undefined', '-g', '-fno-omit-frame-pointer']
command = ['g++', *flags, '-I' + str(engine_source / 'include'), str(source), str(core), '-pthread',
           '-Wl,--wrap=pthread_mutex_lock', '-o', str(binary)]
ok, _, _ = execute(command, 'compile', 120)
if ok:
    result['binary_sha256'] = digest(binary)
    ok, stdout, stderr = execute([str(binary)], 'run', 90)
    expected = [b'PASS default-shared1 ', b'PASS exclusive-request-smp4-fallback ',
                b'PASS exclusive1-after-1to4to1 ', b'PASS post-return-default-api-and-zero-node-cleanup',
                b'PASS nested-other-table-owner-restoration', b'PASS actual-search-exception-unwind',
                b'PASS partial-drain-constructor-exception']
    result['completed_groups'] = [x.decode() for x in expected if x in stdout]
    result['tsan_options'] = os.environ.get('TSAN_OPTIONS')
    if b'ThreadSanitizer: data race' in stderr:
        result['diagnostic_classification'] = 'tsan_data_race'
    elif b'ThreadSanitizer: unexpected memory mapping' in stderr:
        result['diagnostic_classification'] = 'tsan_startup_mapping_failure'
    elif b'ThreadSanitizer: CHECK failed' in stderr:
        result['diagnostic_classification'] = 'tsan_runtime_check_failure'
    elif b'ThreadSanitizer' in stderr:
        result['diagnostic_classification'] = 'other_tsan_diagnostic'
    elif b'AddressSanitizer' in stderr or b'runtime error:' in stderr:
        result['diagnostic_classification'] = 'address_or_undefined_sanitizer_report'
    else:
        result['diagnostic_classification'] = 'none' if not stderr else 'other_stderr'
    ok = ok and len(result['completed_groups']) == len(expected) and not stderr
result['status'] = 'passed' if ok else 'failed'
result['source_unchanged_during_driver'] = all(digest(Path(path) if Path(path).is_absolute() else root / path) == value
                                             for path, value in result['sha256_before'].items())
if not result['source_unchanged_during_driver']:
    result['status'] = 'failed_inputs_changed'
save()
print(json.dumps(dict(status=result['status'], report=str(out / (args.label + '-actual-api.json')))))
raise SystemExit(0 if result['status'] == 'passed' else 1)
