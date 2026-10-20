#!/usr/bin/env python3
"""Prepare/run one frozen-working-source Release validation; never run on import.

Requires the parent-approved exact 75-file hash manifest. No bench or match is
performed. Full exported source and build remain outside the checkout.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode = True
REPO = Path('/workspace/dwqww')
HERE = REPO / 'validation/pawn-span-fill-20261020'
KEYLIST = REPO / 'validation/lazy-runtime-psqt-native-20261020/frozen-source-61f5980-files.json'
SOURCE = Path('/workspace/.cloud-setup/pawn-span-fill-prototype-source')
BUILD = Path('/workspace/.cloud-setup/pawn-span-fill-prototype-release')
CMAKE = '/workspace/.cloud-setup/venv/bin/cmake'
CTEST = '/workspace/.cloud-setup/venv/bin/ctest'
CXX = '/usr/bin/g++-14'
FLAGS = '-O3 -DNDEBUG -march=x86-64-v3 -mtune=generic -fno-fast-math -ffp-contract=off -fno-lto'
EXPECTED_TESTS = sorted(('forge_tests', 'forge_correction_history_tests',
    'forge_runtime_psqt_tests', 'forge_pawn_span_tests', 'forge_tt_tests',
    'forge_rule50_tests', 'forge_legal_witness_tests', 'match_tool_tests',
    'windows_validation_tests', 'uci_regression', 'ponder_regression', 'ownbook_regression'))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


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


def _owned_group_empty(process):
    try:
        os.killpg(process.pid, 0)
    except ProcessLookupError:
        return True
    return False


def source_snapshot(root, names):
    return {name: sha(root / name) for name in names}


def build_snapshot():
    return {path.relative_to(BUILD).as_posix(): sha(path)
        for path in sorted(BUILD.rglob('*')) if path.is_file()}


def run_stage(label, command, timeout, out, names, expected, env, summary):
    """Write observations before verdict; teardown cannot be skipped by I/O errors."""
    stage = out / label
    stage.mkdir(exist_ok=False)
    record = {'label': label, 'command': [str(x) for x in command], 'cwd': str(SOURCE),
        'timeout_seconds': timeout, 'status': 'pending', 'exit_code': None,
        'timed_out': False, 'cleanup_attempted': False, 'errors': [],
        'source_sha256_before': source_snapshot(SOURCE, names),
        'working_source_sha256_before': source_snapshot(REPO, names),
        'build_sha256_before': build_snapshot(),
        'started_utc': datetime.now(timezone.utc).isoformat()}
    if record['source_sha256_before'] != expected or record['working_source_sha256_before'] != expected:
        record.update(status='FAILED', error='Source differs before process launch')
        save(stage / 'process.json', record)
        raise RuntimeError(record['error'])
    save(stage / 'process.json', record)
    process = None
    started = time.monotonic()

    def error(where, exc):
        record['errors'].append({'where': where, 'error': repr(exc)})
        record.setdefault('error', repr(exc))

    def capture(key, operation):
        try:
            record[key] = operation()
        except BaseException as exc:
            error(key, exc)

    with (stage / 'stdout.bin').open('xb') as stdout, (stage / 'stderr.bin').open('xb') as stderr:
        try:
            process = subprocess.Popen(record['command'], cwd=SOURCE, env=env,
                stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, start_new_session=True)
            record['pid'] = process.pid
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired as exc:
                record['timed_out'] = True
                record['wait_error'] = repr(exc)
                error('wait', exc)
            except BaseException as exc:
                record['wait_error'] = repr(exc)
                error('wait', exc)
        except BaseException as exc:
            error('launch', exc)
        finally:
            record['returncode_before_verdict'] = process.returncode if process else None
            record['elapsed_before_cleanup_operational_only'] = time.monotonic() - started
            try:
                capture('owned_group_empty_before_verdict', lambda: _owned_group_empty(process) if process else None)
                capture('stdout_flush_before_verdict', lambda: stdout.flush())
                capture('stderr_flush_before_verdict', lambda: stderr.flush())
                capture('stdout_sha256_before_verdict', lambda: sha(stage / 'stdout.bin'))
                capture('stderr_sha256_before_verdict', lambda: sha(stage / 'stderr.bin'))
                capture('before_verdict_record_written', lambda: save(stage / 'before-verdict.json', record))
            finally:
                if process and (record['errors'] or process.returncode != 0
                        or record.get('owned_group_empty_before_verdict') is not True):
                    record['cleanup_attempted'] = True
                    try:
                        stop_group(process)
                    except BaseException as exc:
                        record['cleanup_error'] = repr(exc)
                        error('cleanup', exc)
                record['exit_code'] = process.returncode if process else None
                capture('owned_group_empty_after_cleanup', lambda: _owned_group_empty(process) if process else None)
                record['elapsed_after_cleanup_operational_only'] = time.monotonic() - started
                capture('stdout_flush_after_cleanup', lambda: stdout.flush())
                capture('stderr_flush_after_cleanup', lambda: stderr.flush())
                capture('stdout_sha256', lambda: sha(stage / 'stdout.bin'))
                capture('stderr_sha256', lambda: sha(stage / 'stderr.bin'))
                capture('source_sha256_after', lambda: source_snapshot(SOURCE, names))
                capture('working_source_sha256_after', lambda: source_snapshot(REPO, names))
                capture('build_sha256_after', build_snapshot)
                if record.get('source_sha256_after') != expected or record.get('working_source_sha256_after') != expected:
                    error('source_immutability', RuntimeError('Source changed during stage'))
                passed = (not record['errors'] and record['exit_code'] == 0
                    and record.get('owned_group_empty_before_verdict') is True
                    and record.get('owned_group_empty_after_cleanup') is True)
                record['status'] = 'PASS' if passed else 'FAILED'
                record['completed_utc'] = datetime.now(timezone.utc).isoformat()
                save(stage / 'process.json', record)
                summary['stages'].append(record)
                save(out / 'summary.json', summary)
    if record['status'] != 'PASS':
        raise RuntimeError(label + ' failed; original observations retained')
    return stage


def verify_build_configuration():
    cache = (BUILD / 'CMakeCache.txt').read_text()
    for line in ('CMAKE_BUILD_TYPE:STRING=Release', 'CMAKE_CXX_FLAGS:STRING=',
            'CMAKE_CXX_FLAGS_RELEASE:STRING=' + FLAGS,
            'CMAKE_INTERPROCEDURAL_OPTIMIZATION:UNINITIALIZED=OFF',
            'FORGE_NATIVE:BOOL=OFF', 'CMAKE_EXPORT_COMPILE_COMMANDS:UNINITIALIZED=ON'):
        key, value = line.split('=', 1)
        name = key.split(':', 1)[0]
        if not re.search(r'^' + re.escape(name) + r':[^=]+=' + re.escape(value) + r'$', cache, re.M):
            raise RuntimeError('Unexpected configured cache entry: ' + line)
    commands = json.loads((BUILD / 'compile_commands.json').read_text())
    if not commands:
        raise RuntimeError('No actual compile commands')
    for entry in commands:
        args = entry.get('arguments') or shlex.split(entry['command'])
        if Path(args[0]).resolve() != Path(CXX).resolve():
            raise RuntimeError('Actual compile command does not use pinned GCC14')
        for flag in FLAGS.split():
            if flag not in args:
                raise RuntimeError('Actual compile command misses ' + flag)
        if any(arg.startswith('-flto') or arg == '-ffast-math' or arg == '-Ofast'
                or (arg.startswith('-march=') and arg != '-march=x86-64-v3')
                or (arg.startswith('-mtune=') and arg != '-mtune=generic') for arg in args):
            raise RuntimeError('Forbidden actual compile option')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-source-manifest', type=Path, required=True,
        help='Exact approved75-path workingtree hashes; preparation alone cannot launch')
    parser.add_argument('--output', type=Path, default=HERE / 'release-attempt1')
    args = parser.parse_args()
    names = sorted(set(json.loads(KEYLIST.read_text())) | {'tests/pawn_span_tests.cpp'})
    expected = json.loads(args.expected_source_manifest.read_text())
    if len(names) != 75 or sorted(expected) != names or any(not re.fullmatch('[0-9a-f]{64}', value) for value in expected.values()):
        raise RuntimeError('Require exact75-path SHA256 manifest')
    if SOURCE.exists() or BUILD.exists() or args.output.exists():
        raise RuntimeError('Fresh source/build/output paths required; never overwrite/retry')
    before = source_snapshot(REPO, names)
    if before != expected:
        raise RuntimeError('Workingtree differs from approved manifest; nothing launched')
    args.output.mkdir(parents=True, exist_ok=False)
    frozen_inputs = {str(Path(__file__).resolve()): sha(Path(__file__)), str(KEYLIST): sha(KEYLIST),
        str(args.expected_source_manifest.resolve()): sha(args.expected_source_manifest)}
    summary = {'status': 'RUNNING', 'scope': 'Release correctness only; no bench/match/performance/Elo',
        'source_kind': 'approved workingtree export, not an asserted Git commit',
        'source_root': str(SOURCE), 'build_root': str(BUILD), 'source_file_count': len(names),
        'working_source_sha256_before_export': before, 'frozen_inputs_sha256_before': frozen_inputs,
        'expected_ctest_names': EXPECTED_TESTS, 'stages': [],
        'started_utc': datetime.now(timezone.utc).isoformat()}
    save(args.output / 'summary.json', summary)
    try:
        SOURCE.mkdir(parents=True, exist_ok=False)
        for name in names:
            target = SOURCE / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / name, target)
        summary['exported_source_sha256_before_build'] = source_snapshot(SOURCE, names)
        summary['working_source_sha256_after_export'] = source_snapshot(REPO, names)
        save(args.output / 'source-export.json', summary)
        if summary['exported_source_sha256_before_build'] != expected or summary['working_source_sha256_after_export'] != expected:
            raise RuntimeError('Source changed while exporting; no compiler launched')
        env = os.environ.copy()
        for key in ('ASAN_OPTIONS', 'UBSAN_OPTIONS', 'TSAN_OPTIONS', 'LSAN_OPTIONS', 'CXXFLAGS', 'CPPFLAGS', 'CFLAGS', 'LDFLAGS'):
            env.pop(key, None)
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        summary['build_environment_overrides'] = {'PYTHONDONTWRITEBYTECODE': '1',
            'removed': ['ASAN_OPTIONS', 'UBSAN_OPTIONS', 'TSAN_OPTIONS', 'LSAN_OPTIONS', 'CXXFLAGS', 'CPPFLAGS', 'CFLAGS', 'LDFLAGS']}
        stage = lambda label, command, timeout: run_stage(label, command, timeout, args.output, names, expected, env, summary)
        compiler = stage('compiler-version', [CXX, '--version'], 10)
        if not re.search(rb'\b14\.\d', (compiler / 'stdout.bin').read_bytes()):
            raise RuntimeError('Actual compiler version is not GCC14')
        stage('configure', [CMAKE, '-S', SOURCE, '-B', BUILD, '-DCMAKE_BUILD_TYPE=Release',
            '-DCMAKE_CXX_COMPILER=' + CXX, '-DCMAKE_CXX_FLAGS=', '-DCMAKE_CXX_FLAGS_RELEASE=' + FLAGS,
            '-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF', '-DFORGE_NATIVE=OFF',
            '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON'], 120)
        verify_build_configuration()
        stage('build', [CMAKE, '--build', BUILD, '-j2'], 360)
        verify_build_configuration()
        listing = stage('ctest-list', [CTEST, '--test-dir', BUILD, '--show-only=json-v1'], 30)
        actual_tests = sorted(item['name'] for item in json.loads((listing / 'stdout.bin').read_text())['tests'])
        if actual_tests != EXPECTED_TESTS:
            raise RuntimeError('Configured tests differ from exact12 required names')
        tests = stage('ctest', [CTEST, '--test-dir', BUILD, '--output-on-failure', '--no-tests=error', '-j', '1'], 240)
        raw = (tests / 'stdout.bin').read_text()
        actual_run = sorted(re.findall(r'\d+/\d+\s+Test\s+#\d+:\s+(\S+)', raw))
        if actual_run != EXPECTED_TESTS or not re.search(r'100% tests passed, 0 tests failed out of 12\b', raw):
            raise RuntimeError('Actual CTest output does not prove full12/12 pass')
        direct = stage('pawn-span-direct', [BUILD / 'forge_pawn_span_tests'], 60)
        if (direct / 'stdout.bin').read_bytes() != b'pawn_span_tests: 37320 checks, 0 failures\n' or (direct / 'stderr.bin').read_bytes():
            raise RuntimeError('Direct permanent pawn-span regression output differs from37320/0 contract')
        for name in ('CMakeCache.txt', 'compile_commands.json', 'Testing/Temporary/LastTest.log', 'Testing/Temporary/CTestCostData.txt'):
            path = BUILD / name
            if path.is_file():
                target = args.output / 'retained-build-records' / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
        summary['status'] = 'PASS'
    except BaseException as exc:
        summary.update(status='FAILED', error=repr(exc))
        raise
    finally:
        try:
            summary['working_source_sha256_final'] = source_snapshot(REPO, names)
            summary['exported_source_sha256_final'] = source_snapshot(SOURCE, names)
            summary['build_sha256_final'] = build_snapshot()
            summary['frozen_inputs_sha256_final'] = {path: sha(path) for path in frozen_inputs}
            if (summary['working_source_sha256_final'] != expected or summary['exported_source_sha256_final'] != expected
                    or summary['frozen_inputs_sha256_final'] != frozen_inputs):
                summary.update(status='FAILED', final_immutability_error='Source or frozen driver/manifest changed')
        except BaseException as exc:
            summary.update(status='FAILED', final_observation_error=repr(exc))
        summary['completed_utc'] = datetime.now(timezone.utc).isoformat()
        save(args.output / 'summary.json', summary)
    if summary['status'] != 'PASS':
        raise RuntimeError('Final immutable-input gate failed')
    print(json.dumps({'status': 'PASS', 'source_file_count': 75, 'ctest_count': 12,
        'source_root': str(SOURCE), 'build_root': str(BUILD)}))


if __name__ == '__main__':
    main()
