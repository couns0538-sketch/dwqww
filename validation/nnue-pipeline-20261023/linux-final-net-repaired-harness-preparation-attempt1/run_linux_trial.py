#!/usr/bin/env python3
"""Selected clean-engine qualification with one explicitly pinned repaired test harness."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET

BASE = '1ab50b2dd64d9b2f752f7f1285f6968cad2fd792'
CLEAN_ENGINE = '6e9622fd5be18e0155fc3ed5fcf6c4586705cca6'
TEST_COMMIT = 'f4a1ed6be3921a024e0d876cac2433153a96c66c'
TEST_SHA256 = '6dec8511d6107511cae182dc6169122b48b41e00c5033738f8b04ab027441dce'
TESTS = {
    'forge_tests', 'forge_correction_history_tests', 'forge_runtime_psqt_tests',
    'forge_pawn_span_tests', 'forge_nearest_pawn_tests', 'forge_pv_metadata_tests',
    'forge_tt_tests', 'forge_rule50_tests', 'forge_legal_witness_tests',
    'match_tool_tests', 'windows_validation_tests', 'uci_regression',
    'ponder_regression', 'ownbook_regression',
}
STRICT_FLAGS = '-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -fno-lto'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def save_new(path, value):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, prefix=path.name + '.',
                                         suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(value, stream, indent=2)
            stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
        os.link(temporary, path)  # Atomic, no overwrite.
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def file_record(path):
    path = Path(path)
    return {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size,
            'mode': stat.S_IMODE(path.stat().st_mode)}


def tree_record(directory):
    result = {}
    for path in sorted(directory.rglob('*')):
        if path.is_symlink():
            raise ValueError('Unexpected symlink: ' + str(path))
        if path.is_file():
            result[path.relative_to(directory).as_posix()] = file_record(path)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inc', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--pins', type=Path, default=Path(__file__).with_name('PINS.json'))
    args = parser.parse_args()
    if not re.fullmatch('[0-9a-f]{64}', args.sha256):
        raise ValueError('Explicit lowercase SHA256 required')
    inc, out = args.inc.resolve(strict=True), args.out.resolve()
    if out.exists():
        raise ValueError('Fresh output path required; preserve earlier attempts')
    pins = json.loads(args.pins.read_text())
    if sha(Path(__file__)) != pins['runner_sha256']:
        raise ValueError('Prepared runner identity changed')
    tools = pins['tools']

    def verify_pins():
        if sha(Path(__file__)) != pins['runner_sha256']:
            raise ValueError('Prepared runner identity changed during execution')
        for entry in [*tools.values(), pins['export_helper'], pins['include_parser']]:
            if sha(Path(entry['path'])) != entry['sha256']:
                raise ValueError('Prepared tool/helper identity changed: ' + entry['path'])
        if sha(inc) != args.sha256:
            raise ValueError('Explicit chosen include changed')

    verify_pins()
    out.mkdir(parents=True)
    evidence = out / 'evidence'; evidence.mkdir()
    source = out / 'source'
    freeze = evidence / 'source-freeze.json'
    frozen = None
    frozen_manifest_sha = None
    env = dict(os.environ)
    for key in ('CC', 'CXX', 'CFLAGS', 'CXXFLAGS', 'CPPFLAGS', 'LDFLAGS', 'CPATH',
                'CPLUS_INCLUDE_PATH', 'LIBRARY_PATH', 'LD_LIBRARY_PATH', 'LD_PRELOAD',
                'ASAN_OPTIONS', 'UBSAN_OPTIONS', 'TSAN_OPTIONS', 'LSAN_OPTIONS',
                'CTEST_PARALLEL_LEVEL', 'CMAKE_BUILD_PARALLEL_LEVEL'):
        env.pop(key, None)
    overrides = {'PATH': '/usr/bin:/bin', 'PYTHONDONTWRITEBYTECODE': '1',
                 'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1',
                 'LC_ALL': 'C', 'ASAN_OPTIONS': 'detect_leaks=1:halt_on_error=1:abort_on_error=1',
                 'UBSAN_OPTIONS': 'halt_on_error=1:print_stacktrace=1'}
    env.update(overrides)

    def verify_source():
        verify_pins()
        if frozen is None:
            return
        if sha(freeze) != frozen_manifest_sha:
            raise ValueError('Frozen source manifest changed')
        records = tree_record(source)
        actual = {name: entry['sha256'] for name, entry in records.items()}
        if actual != frozen['source_sha256']:
            raise ValueError('Exact exported source bytes/file set changed')
        if any(records[name]['mode'] != (0o755 if mode == '100755' else 0o644)
               for name, mode in frozen['git_modes'].items()):
            raise ValueError('Exact exported source permission modes changed')

    def run(label, argv, input_bytes=b'', timeout=1800):
        verify_source()
        stdin_path = evidence / (label + '.stdin')
        with stdin_path.open('xb') as stream:
            stream.write(input_bytes)
        save_new(evidence / (label + '.command.json'),
                 {'argv': [str(x) for x in argv], 'cwd': str(out),
                  'stdin': file_record(stdin_path), 'environment_overrides': overrides})
        started = time.monotonic()
        process = None
        error = None
        killed = False
        try:
            with (evidence / (label + '.stdout')).open('xb') as stdout, (evidence / (label + '.stderr')).open('xb') as stderr:
                process = subprocess.Popen([str(x) for x in argv], cwd=out, env=env,
                                           stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                                           start_new_session=True)
                try:
                    process.communicate(input_bytes, timeout=timeout)
                except BaseException as failure:
                    error = type(failure).__name__ + ': ' + str(failure)
                    killed = True
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.communicate()
        except BaseException as failure:
            error = type(failure).__name__ + ': ' + str(failure)
        result = {'returncode': process.returncode if process is not None else None,
                  'utc': datetime.now(timezone.utc).isoformat(),
                  'elapsed_seconds_operational_only': time.monotonic() - started,
                  'owned_process_reaped': process is not None and process.returncode is not None,
                  'owned_group_killed_on_exception': killed, 'exception': error}
        save_new(evidence / (label + '.result.json'), result)
        if error or result['returncode'] != 0:
            raise RuntimeError(label + ' failed; all original streams/results retained')
        verify_source()
        return (evidence / (label + '.stdout')).read_text(errors='strict')

    try:
        save_new(evidence / 'INVOCATION.json',
                 {'baseline': BASE, 'chosen_include': file_record(inc), 'pins': file_record(args.pins),
                  'runner': file_record(Path(__file__)), 'clean_engine_source_commit': CLEAN_ENGINE,
                  'test_harness_commit': TEST_COMMIT, 'test_harness_sha256': TEST_SHA256,
                  'scope': 'Linux trial with exact controlled-test repair; no production-source edits, Elo/NPS/acceptance'})
        for role in ('compiler', 'cmake', 'ctest', 'make', 'helper_python', 'test_python'):
            run('version-' + role, [tools[role]['path'], '--version'], timeout=30)
        run('export-source', [tools['helper_python']['path'], '-B', pins['export_helper']['path'],
                              '--inc', str(inc), '--sha256', args.sha256,
                              '--source', str(source), '--manifest', str(freeze)])
        frozen = json.loads(freeze.read_text())
        frozen_manifest_sha = sha(freeze)
        if (frozen['baseline'] != BASE or frozen['hidden'] != 128 or frozen['residual'] is not True
                or frozen['changed_paths'] != ['src/nnue_weights.inc', 'tests/tests.cpp']
                or frozen['chosen_include_sha256'] != args.sha256
                or frozen['clean_engine_source_commit'] != CLEAN_ENGINE
                or frozen['test_harness_commit'] != TEST_COMMIT
                or frozen['test_harness_sha256'] != TEST_SHA256
                or frozen['delta_from_clean_engine_commit'] != ['tests/tests.cpp']):
            raise ValueError('Exact clean-engine H128/residual plus pinned-test-repair contract differs')
        verify_source()
        profiles = {}
        for profile in ('release', 'asan-ubsan'):
            build = out / ('build-' + profile)
            if build.exists():
                raise ValueError('Fresh build required: ' + str(build))
            sanitized = profile == 'asan-ubsan'
            flags = STRICT_FLAGS + (' -fno-pie' if sanitized else '')
            configure = [tools['cmake']['path'], '-S', str(source), '-B', str(build),
                         '-G', 'Unix Makefiles', '-DCMAKE_MAKE_PROGRAM=' + tools['make']['path'],
                         '-DCMAKE_BUILD_TYPE=' + ('RelWithDebInfo' if sanitized else 'Release'),
                         '-DCMAKE_CXX_COMPILER=' + tools['compiler']['path'],
                         '-DCMAKE_CXX_STANDARD=20', '-DCMAKE_CXX_STANDARD_REQUIRED=ON',
                         '-DCMAKE_CXX_FLAGS=' + flags,
                         '-DCMAKE_EXE_LINKER_FLAGS=' + ('-no-pie' if sanitized else ''),
                         '-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF', '-DFORGE_NATIVE=OFF',
                         '-DFORGE_ENABLE_SANITIZERS=' + ('ON' if sanitized else 'OFF'),
                         '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON',
                         '-DPython3_EXECUTABLE=' + tools['test_python']['path']]
            run(profile + '-configure', configure)
            run(profile + '-build', [tools['cmake']['path'], '--build', str(build), '--parallel', '1'])
            commands = json.loads((build / 'compile_commands.json').read_text())
            for unit in commands:
                command = unit.get('command', ' '.join(unit.get('arguments', [])))
                if any(flag not in command for flag in ('-fno-fast-math', '-ffp-contract=off', '-fno-lto')):
                    raise ValueError('Missing strict float/no-LTO flags')
                if not re.search(r'-std=(?:gnu\+\+20|c\+\+20)(?:\s|$)', command):
                    raise ValueError('Actual C++20 compiler flag missing')
                if any(re.search(r'(?<!\S)' + re.escape(flag) + r'(?!\S)', command)
                       for flag in ('-ffast-math', '-Ofast', '-ffp-contract=fast', '-flto')):
                    raise ValueError('Forbidden float/LTO compile flag')
                if sanitized and '-fsanitize=address,undefined' not in command:
                    raise ValueError('ASan/UBSan instrumentation missing')
            link_command = (build / 'CMakeFiles/forge.dir/link.txt').read_text()
            if sanitized and any(flag not in link_command for flag in ('-fsanitize=address,undefined', '-no-pie')):
                raise ValueError('ASan/UBSan non-PIE link flags missing')
            discovery = json.loads(run(profile + '-ctest-discovery',
                                        [tools['ctest']['path'], '--test-dir', str(build), '--show-only=json-v1']))
            names = [test['name'] for test in discovery['tests']]
            if len(names) != 14 or set(names) != TESTS:
                raise ValueError('Exact original 14 CTest names differ')
            junit = build / 'ctest-junit.xml'
            output = run(profile + '-ctest', [tools['ctest']['path'], '--test-dir', str(build),
                                              '--output-on-failure', '--parallel', '1',
                                              '--output-junit', str(junit)], timeout=900)
            cases = ET.parse(junit).getroot().findall('.//testcase')
            if (len(cases) != 14 or {case.attrib['name'] for case in cases} != TESTS
                    or any(case.find(tag) is not None for case in cases for tag in ('failure', 'error', 'skipped'))
                    or '100% tests passed, 0 tests failed out of 14' not in output):
                raise ValueError('Actual full CTest/JUnit result differs')
            profiles[profile] = {'build': str(build), 'ctests_passed': 14,
                                  'engine': file_record(build / 'forge'),
                                  'core': file_record(build / 'libforge_core.a')}
        engine = out / 'build-release/forge'
        before = file_record(engine)
        nodes = []
        for index in (1, 2):
            label = 'release-bench11-' + str(index)
            output = run(label, [str(engine)], input_bytes=b'bench 11\nquit\n', timeout=180)
            signatures = re.findall(r'^info string bench depth 11 nodes ([0-9]+)\b', output, flags=re.MULTILINE)
            if len(signatures) != 1 or int(signatures[0]) <= 0:
                raise ValueError('Expected one genuine positive bench11 signature')
            nodes.append(int(signatures[0]))
            if file_record(engine) != before:
                raise ValueError('Bench binary identity changed')
            if index == 1:
                save_new(evidence / 'FIRST-BENCH11.json',
                         {'nodes': nodes[0], 'engine': before, 'chosen_include_sha256': args.sha256,
                          'source_manifest_sha256': frozen_manifest_sha,
                          'stdout': file_record(evidence / (label + '.stdout')),
                          'meaning': 'First actual new-network signature; no old-network signature required'})
            elif nodes[1] != nodes[0]:
                raise ValueError('New-network bench11 repeat differs; first signature remains frozen')
        verify_source()
        for profile in profiles:
            build = Path(profiles[profile]['build'])
            save_new(evidence / (profile + '-build-files.json'), tree_record(build))
        result = {'status': 'PASS_LINUX_PINNED_TEST_REPAIR_RELEASE14_ASAN_UBSAN14_BENCH_REPEATABILITY',
                  'baseline': BASE, 'source_manifest_sha256': frozen_manifest_sha,
                  'chosen_include_sha256': args.sha256, 'hidden': 128, 'residual': True,
                  'changed_paths': frozen['changed_paths'], 'profiles': profiles,
                  'clean_engine_source_commit': CLEAN_ENGINE, 'test_harness_commit': TEST_COMMIT,
                  'test_harness_sha256': TEST_SHA256, 'production_source_edits_beyond_selected_net': False,
                  'new_net_bench11_first': nodes[0], 'new_net_bench11_repeat': nodes[1],
                  'speed_conclusion': None, 'elo_conclusion': None, 'promoted': False,
                  'scope': 'Actual Linux selected-engine correctness with exact controlled-NMP test repair and first genuine new-net bench; no Windows, speed, Elo or strength acceptance'}
        save_new(evidence / 'RESULT.json', result)
        print(json.dumps(result, indent=2), flush=True)
        return 0
    except BaseException as error:
        save_new(evidence / 'RESULT.json',
                 {'status': 'FAILED', 'utc': datetime.now(timezone.utc).isoformat(),
                  'reason': type(error).__name__ + ': ' + str(error),
                  'chosen_include_sha256': args.sha256, 'source_changed_to_force_pass': False,
                  'next_action': 'Preserve all original evidence and investigate; no automatic retry or promotion'})
        raise


if __name__ == '__main__':
    raise SystemExit(main())
