#!/usr/bin/env python3
"""Audit saved PV-metadata evidence; never run engines, compilers or tests.

Every check is appended and flushed to a new facts JSONL before the final gate.
Independent stages continue after a discrepancy when their inputs remain readable.
"""
from pathlib import Path
import argparse
import base64
import datetime
import hashlib
import io
import json
import re
import shlex
import stat
import subprocess
import tarfile

ROOT = Path('/workspace/dwqww')
HERE = ROOT / 'validation/pv-metadata-native-20261021'
SOURCE = Path('/workspace/.cloud-setup/pv-metadata-native-source')
REV = None  # Set only in main after explicit root clearance for the frozen source.
PARENT_REV = '2e151d019bc58dff2ab4e76e99ef99516af8d222'
BASE = Path('/workspace/.cloud-setup')
CMAKE = '/workspace/.cloud-setup/venv/bin/cmake'
CTEST = '/workspace/.cloud-setup/venv/bin/ctest'
PYTHON = '/workspace/.cloud-setup/venv/bin/python'
CXX = '/usr/bin/g++-14'
BINARY_NAMES = ['forge', 'forge_tests', 'forge_tt_tests', 'forge_rule50_tests',
                'forge_legal_witness_tests', 'forge_correction_history_tests', 'forge_bench', 'libforge_core.a', 'forge_runtime_psqt_tests', 'CMakeFiles/forge_runtime_psqt_tests.dir/tests/runtime_psqt_tests.cpp.o',
                'forge_pawn_span_tests', 'CMakeFiles/forge_pawn_span_tests.dir/tests/pawn_span_tests.cpp.o',
                'CMakeFiles/forge_core.dir/src/nnue.cpp.o',
                'forge_nearest_pawn_tests', 'CMakeFiles/forge_nearest_pawn_tests.dir/tests/nearest_pawn_tests.cpp.o',
                'forge_pv_metadata_tests', 'CMakeFiles/forge_pv_metadata_tests.dir/tests/pv_metadata_tests.cpp.o']
FLAGS = ['-march=x86-64-v3', '-mtune=znver5', '-fno-fast-math', '-ffp-contract=off', '-fno-lto']
TEST_NAMES = ['forge_tests', 'forge_correction_history_tests', 'forge_tt_tests', 'forge_rule50_tests',
              'forge_legal_witness_tests', 'match_tool_tests', 'windows_validation_tests',
              'uci_regression', 'ponder_regression', 'ownbook_regression', 'forge_runtime_psqt_tests', 'forge_pawn_span_tests', 'forge_nearest_pawn_tests', 'forge_pv_metadata_tests']
DIAGNOSTIC = re.compile(r'AddressSanitizer|LeakSanitizer|UndefinedBehaviorSanitizer|ThreadSanitizer|runtime error:', re.I)
checks, facts, groups = [], {}, set()
context = {}
fact_stream = None


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(path):
    return sha(Path(path).read_bytes())


def load(path):
    return json.loads(Path(path).read_text())


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def record(name, passed, **detail):
    row = {'name': name, 'passed': bool(passed), **detail}
    checks.append(row)
    fact_stream.write(json.dumps({'type': 'check', **row}, allow_nan=False) + '\n')
    fact_stream.flush()
    return bool(passed)


def stage(name, function):
    try:
        value = function()
        facts[name] = value
        row = {'type': 'stage_complete', 'name': name, 'facts': value}
    except Exception as error:
        value = {'error_type': type(error).__name__, 'error': str(error)}
        facts[name] = value
        record('readable_stage:' + name, False, **value)
        row = {'type': 'stage_error', 'name': name, **value}
    fact_stream.write(json.dumps(row, allow_nan=False) + '\n')
    fact_stream.flush()


def frozen_source():
    clear = load(HERE / 'ROOT-CLEARANCE.json')
    record('exact_root_clearance', clear['authorized'] is True and clear['source_commit'] == REV and clear['baseline_source_commit'] == PARENT_REV and clear['required_version'] == '6.4.22' and clear['expected_runtime_psqt_checks'] == 347 and clear['expected_pawn_span_checks'] == 37320 and clear['expected_nearest_checks'] == 791680 and clear['expected_nearest_sets'] == 395840 and clear['expected_nearest_constexpr_assertions'] == 6 and clear['expected_pv_metadata_assertions'] == 56 and clear['expected_pv_metadata_test_source_sha256'] == '8000b717a298c4c8bb637752fcc57a0ce485110a12edc4a505f3d0452620bd1e' and clear['exact_search_parity_required'] is False and clear['observational_cold_warm_searches'] == 0 and clear['source_files'] == 77 and clear['expected_ctest_per_profile'] == 14 and clear['expected_bench11_nodes'] == 292545 and clear['strict_fp'] is True and clear['no_lto'] is True and clear['profiles_sequential'] is True and clear['build_jobs'] == 2 and clear['default_tsan_options'] == 'halt_on_error=1:exitcode=66' and clear['suppression_or_deadlock_detector_disabled'] is False and clear['performance_or_strength_inference'] is False)
    data = git('archive', REV, 'CMakeLists.txt', 'LICENSE', 'src', 'include', 'tests', 'bench', 'tools')
    expected = {}
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        for item in archive.getmembers():
            if item.isfile():
                expected[item.name] = sha(archive.extractfile(item).read())
    actual = {p.relative_to(SOURCE).as_posix(): digest(p) for p in SOURCE.rglob('*') if p.is_file()}
    record('exact_frozen_source_git_tar', (HERE / ('frozen-source-' + REV[:7] + '.tar')).read_bytes() == data)
    record('exact77_source_git_export_manifest', len(expected) == 77 and expected == actual == load(HERE / ('frozen-source-' + REV[:7] + '-files.json')))
    context['source'] = expected
    root_gate = load(HERE / 'ROOT-FROZEN-SOURCE-GATES.json')
    record('root_frozen_source_gate_identity', root_gate['source_commit'] == REV and root_gate['baseline_commit'] == PARENT_REV and root_gate['inputs'] == expected)
    for name in root_gate['unchanged_boundaries']:
        record('root_unchanged_boundary:' + name, expected[name] == sha(git('show', PARENT_REV + ':' + name)))
    provenance = load(HERE / 'DRIVER-PROVENANCE.json')
    for name, value in provenance['scripts'].items():
        record('frozen_driver_unchanged:' + name, digest(HERE / name) == value)
    source_text = '\n'.join((SOURCE / name).read_text() for name in expected if name.startswith(('src/', 'include/')) and name.endswith(('.cpp', '.hpp')))
    record('no_source_tsan_suppression_hooks', re.search(r'__tsan_default_suppressions|no_sanitize_thread|no_sanitize\s*\(\s*"thread"', source_text) is None)
    protocol = load(HERE / 'RELEASE-SIGNATURE-PROTOCOL.json')
    schema_path = Path(protocol['pv_metadata_test_schema_path'])
    schema = load(schema_path)
    record('actual_red_test_schema_identity', digest(schema_path) == protocol['pv_metadata_test_schema_sha256'] == '0b146976915b9a40b25873b0be2c168322331cd68bc352608db49bc860d6d252' and expected['tests/pv_metadata_tests.cpp'] == protocol['pv_metadata_test_source_sha256'] == schema['source_sha256'] == '8000b717a298c4c8bb637752fcc57a0ce485110a12edc4a505f3d0452620bd1e')
    red_path = schema_path.parent / 'baseline-attempt1/result.json'
    red = load(red_path)
    record('actual_saved_baseline21_red', digest(red_path) == schema['baseline_result_sha256'] and red['status'] == 'EXPECTED_BASELINE_RED_PERMANENT_REGRESSION' and red['source_commit'] == PARENT_REV and red['assertions'] == schema['observed_baseline_assertions'] == 56 and schema['observed_baseline_failures'] == 2 and schema['observed_baseline_exit_code'] == 1 and red['inputs_before'] == red['inputs_after'] and red['core_unchanged'] is True and red['all_other_assertions_passed'] is True)
    red_steps = red['steps']
    record('baseline_red_expected_process_exits', [row['label'] for row in red_steps] == ['compile-link', 'actual-core-unit'] and [row['exit_code'] for row in red_steps] == [0, 1] and all(row['cleanup']['no_live_owned_processes'] and not row['cleanup']['unexpected_live_members_after_command'] for row in red_steps))
    for row in red_steps:
        for stream in ['stdout', 'stderr']:
            record('baseline_red_saved_stream:' + row['label'] + ':' + stream, digest(red_path.parent / (row['label'] + '.' + stream)) == row[stream + '_sha256'])
    red_stdout = (red_path.parent / 'actual-core-unit.stdout').read_text()
    red_stderr = (red_path.parent / 'actual-core-unit.stderr').read_text()
    record('baseline_red_actual56_two_failures', re.findall(r'^PV metadata: assertions (\d+) failures (\d+)\s*$', red_stdout, re.M) == [('56', '2')] and re.findall(r'^FAIL (.*)$', red_stderr, re.M) == schema['observed_failed_assertions'] == red['expected_failures'])
    record('baseline_red_actual_five_rows', [list(row) for row in re.findall(r'^PV_METADATA_CASE (\w+) nodes=(\d+) aborted=([01]) flag=([01]) pv_moves=(\d+)\s*$', red_stdout, re.M)] == schema['case_rows'] == red['case_rows'])
    return {'source_commit': REV, 'source_files': len(expected), 'source_tar_sha256': sha(data), 'runtime_psqt_checks': 347, 'pawn_span_checks': clear['expected_pawn_span_checks'], 'nearest_pawn_checks': 791680, 'nearest_pawn_sets': 395840, 'nearest_constexpr_assertions': 6, 'correction_history_checks': 54, 'baseline_red_saved_assertions': 56, 'baseline_red_saved_failures': 2, 'parent_red_executed_during_audit': False}


def cleanup_fact(label, value):
    record('cleanup:' + label, value['no_live_owned_processes'] is True and value.get('unexpected_live_members_after_command') is False and not any(row['state'] != 'Z' for row in value['after']), observed=value)
    groups.add(value['group_id'])


def streams(label, directory, command, suffix):
    for stream in ['stdout', 'stderr']:
        path = directory / (command['label'] + '.' + stream + suffix)
        record('stream_hash:' + label + ':' + stream, digest(path) == command[stream + '_sha256'])


def scan_logs(label, paths):
    found = []
    for path in paths:
        record('sanitizer_log_present:' + label + ':' + path.name, path.is_file())
        if path.is_file():
            matches = [line for line in path.read_text(errors='replace').splitlines() if DIAGNOSTIC.search(line)]
            found.extend({'path': str(path), 'line': line} for line in matches)
    record('no_sanitizer_diagnostics:' + label, not found, matches=found)
    return found


def expected_tests(build):
    result = {name: [str(build / name)] for name in TEST_NAMES[:5]}
    result['forge_legal_witness_tests'] += [str(SOURCE / 'tests/legal_witness_fixtures.tsv'), str(SOURCE / 'tools/openings/forge-10000.epd')]
    result['forge_runtime_psqt_tests'] = [str(build / 'forge_runtime_psqt_tests')]
    result['forge_pawn_span_tests'] = [str(build / 'forge_pawn_span_tests')]
    result['forge_nearest_pawn_tests'] = [str(build / 'forge_nearest_pawn_tests')]
    result['forge_pv_metadata_tests'] = [str(build / 'forge_pv_metadata_tests')]
    result.update(match_tool_tests=[PYTHON, str(SOURCE / 'tools/match/test_match_tools.py')],
                  windows_validation_tests=[PYTHON, str(SOURCE / 'tools/match/tests/test_windows_validate.py')],
                  uci_regression=[PYTHON, str(SOURCE / 'tools/uci_regression.py'), str(build / 'forge'), '--log', str(build / 'uci-regression.log')],
                  ponder_regression=[PYTHON, str(SOURCE / 'tools/ponder_regression.py'), str(build / 'forge')],
                  ownbook_regression=[PYTHON, str(SOURCE / 'tools/ownbook_regression.py'), str(build / 'forge'), str(build / 'ownbook-regression.json')])
    return result


def audit_profile(profile):
    directory = HERE / ('frozen-' + profile + '-attempt1')
    build = BASE / ('pv-metadata-native-' + profile)
    summary = load(directory / 'summary.json')
    record('profile_pass:' + profile, summary['status'] == 'PASS' and summary['source_commit'] == REV, observed_status=summary['status'])
    record('profile_tar_identity:' + profile, summary['source_archive_sha256'] == digest(HERE / ('frozen-source-' + REV[:7] + '.tar')))
    overrides = {'PYTHONDONTWRITEBYTECODE': '1'}
    if profile == 'asan':
        overrides.update(ASAN_OPTIONS='detect_leaks=1:halt_on_error=1:abort_on_error=1', UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    elif profile == 'tsan':
        overrides.update(TSAN_OPTIONS='halt_on_error=1:exitcode=66')
    record('exact_fatal_sanitizer_options:' + profile, summary['environment_overrides'] == overrides)
    steps = summary['steps']
    record('exact_four_profile_steps:' + profile, [step['label'] for step in steps] == ['configure', 'build', 'ctest-discovery', 'ctest'])
    for step in steps:
        name = profile + ':' + step['label']
        record('original_command_record:' + name, step == load(directory / (step['label'] + '-command.json')))
        record('command_gate:' + name, step['exit_code'] == 0 and step['error'] is None and step['timed_out'] is False and step['timeout_seconds'] == 1200)
        cleanup_fact(name, step['cleanup'])
        streams(name, directory, step, '')
        record('source_before_after:' + name, step['source_sha256_before_step'] == step['source_sha256_after_step'] == context.get('source'))
        if step['label'] in ['ctest-discovery', 'ctest']:
            record('all17_artifacts_before_after_step:' + name, step['artifact_sha256_before_step'] == step['artifact_sha256_after_step'] == summary['binary_sha256_before'])
    commands = {step['label']: step['command'] for step in steps}
    config = commands['configure']
    record('exact_source_compiler_config:' + profile, config[:5] == [CMAKE, '-S', str(SOURCE), '-B', str(build)] and '-DCMAKE_CXX_COMPILER=' + CXX in config and '-DPython3_EXECUTABLE=' + PYTHON in config and '-DFORGE_NATIVE=OFF' in config)
    record('correct_profile_configuration:' + profile, '-DCMAKE_BUILD_TYPE=' + ('Release' if profile == 'release' else 'RelWithDebInfo') in config and '-DFORGE_ENABLE_SANITIZERS=' + ('ON' if profile == 'asan' else 'OFF') in config)
    record('exact_serial_build_ctest_commands:' + profile,
           commands['build'] == [CMAKE, '--build', str(build), '--parallel', '2'] and
           commands['ctest-discovery'] == [CTEST, '--test-dir', str(build), '--show-only=json-v1'] and
           commands['ctest'] == [CTEST, '--test-dir', str(build), '--output-on-failure', '-j', '1', '--timeout', '300'])
    record('gnu14_configuration_log:' + profile, 'CXX compiler identification is GNU 14.2.0' in (directory / 'configure.stdout').read_text())
    discovered = load(directory / 'ctest-discovery.stdout')['tests']
    record('exact14_discovered_names:' + profile, len(discovered) == 14 and {row['name'] for row in discovered} == set(TEST_NAMES) and len(summary['ctest_names']) == 14 and set(summary['ctest_names']) == set(TEST_NAMES))
    record('nearest_then_pv_sixth_ctest_position:' + profile, [row['name'] for row in discovered][4:6] == ['forge_nearest_pawn_tests', 'forge_pv_metadata_tests'])
    expected = expected_tests(build)
    record('exact14_discovered_commands:' + profile, all(row['command'] == expected.get(row['name']) for row in discovered))
    text = (directory / 'ctest.stdout').read_text()
    record('original_ctest14_passes:' + profile, '100% tests passed, 0 tests failed out of 14' in text and len(re.findall(r'Test\s+#\d+:.*Passed', text)) == 14)
    last_path = directory / 'original-LastTest.log'
    last = last_path.read_text()
    record('actual14_lasttest_passes:' + profile, last.count('Test Passed.') == 14)
    block = re.search(r'\n\d+/14 Testing: forge_correction_history_tests\n(.*?)(?=\n\d+/14 Testing:|\Z)', last, re.S)
    correction = block[1] if block else ''
    record('actual54_correction_checks:' + profile, re.findall(r'^SUMMARY checks=(\d+) failures=(\d+)\s*$', correction, re.M) == [('54', '0')] and len(re.findall(r'^PASS ', correction, re.M)) == 54 and not re.search(r'^FAIL ', correction, re.M))
    runtime_block = re.search(r'\n\d+/14 Testing: forge_runtime_psqt_tests\n(.*?)(?=\n\d+/14 Testing:|\Z)', last, re.S)
    runtime_text = runtime_block[1] if runtime_block else ''
    record('actual347_runtime_psqt_checks:' + profile, re.findall(r'^SUMMARY checks=(\d+) failures=(\d+)\s*$', runtime_text, re.M) == [('347', '0')] and len(re.findall(r'^PASS ', runtime_text, re.M)) == 347 and not re.search(r'^FAIL ', runtime_text, re.M) and summary['runtime_psqt_contract_actual_summaries'] == [['347', '0']])

    pawn_block = re.search(r'\n\d+/14 Testing: forge_pawn_span_tests\n(.*?)(?=\n\d+/14 Testing:|\Z)', last, re.S)
    pawn_text = pawn_block[1] if pawn_block else ''
    pawn_checks = str(context['clear']['expected_pawn_span_checks'])
    record('actual_pawn_span_checks:' + profile, re.findall(r'^pawn_span_tests: (\d+) checks, (\d+) failures\s*$', pawn_text, re.M) == [(pawn_checks, '0')] and not re.search(r'^FAIL ', pawn_text, re.M) and summary['pawn_span_contract_actual_summaries'] == [[pawn_checks, '0']])

    nearest_block = re.search(r'\n\d+/14 Testing: forge_nearest_pawn_tests\n(.*?)(?=\n\d+/14 Testing:|\Z)', last, re.S)
    nearest_text = nearest_block[1] if nearest_block else ''
    nearest_expected = [('395840', '791680', '0')]
    record('actual_nearest_pawn_checks:' + profile, re.findall(r'^Nearest pawn distance: sets (\d+) checks (\d+) failures (\d+)\s*$', nearest_text, re.M) == nearest_expected and not re.search(r'^nearest mismatch ', nearest_text, re.M) and summary['nearest_pawn_contract_actual_summaries'] == [list(nearest_expected[0])])
    nearest_assertions = len(re.findall(r'(?m)^static_assert\(', (SOURCE / 'tests/nearest_pawn_tests.cpp').read_text()))
    record('nearest_six_compile_time_assertions:' + profile, nearest_assertions == summary['nearest_constexpr_assertions'] == context['clear']['expected_nearest_constexpr_assertions'] == 6)

    pv_block = re.search(r'\n\d+/14 Testing: forge_pv_metadata_tests\n(.*?)(?=\n\d+/14 Testing:|\Z)', last, re.S)
    pv_text = pv_block[1] if pv_block else ''
    record('actual56_pv_metadata_assertions:' + profile, re.findall(r'^PV metadata: assertions (\d+) failures (\d+)\s*$', pv_text, re.M) == [('56', '0')] and not re.search(r'^FAIL ', pv_text, re.M) and summary['pv_metadata_contract_actual_summaries'] == [['56', '0']])
    pv_rows = re.findall(r'^PV_METADATA_CASE (\w+) nodes=(\d+) aborted=([01]) flag=([01]) pv_moves=(\d+)\s*$', pv_text, re.M)
    pv_names = ['PV_nonPVhit', 'PV_PVhit', 'PV_nohit', 'nullwindow_TTcut', 'PV_abort_verification']
    record('actual_five_pv_metadata_rows:' + profile, [row[0] for row in pv_rows] == pv_names and [list(row) for row in pv_rows] == summary['pv_metadata_case_rows'])
    controls = {name: (int(nodes), int(aborted), int(flag), int(moves)) for name, nodes, aborted, flag, moves in pv_rows}
    record('actual_pv_metadata_case_semantics:' + profile, len(controls) == 5 and all(controls[name][0] > 0 and controls[name][1] == 0 and controls[name][2] == 1 and controls[name][3] > 0 for name in pv_names[:3]) and controls.get('nullwindow_TTcut') == (1, 0, 0, 0) and controls.get('PV_abort_verification') == (2, 1, 1, 0))

    for name in ['ownbook-regression.json', 'Testing/Temporary/LastTest.log', 'Testing/Temporary/CTestCostData.txt', 'uci-regression.log', 'CMakeCache.txt', 'compile_commands.json']:
        record('original_copy_exact:' + profile + ':' + name, (build / name).read_bytes() == (directory / ('original-' + Path(name).name)).read_bytes())
    before = summary['binary_sha256_before']
    current = {name: digest(build / name) for name in BINARY_NAMES}
    record('all17_artifact_identities:' + profile, set(before) == set(BINARY_NAMES) and before == summary['binary_sha256_after_tests'] == summary['binary_sha256_after'] == current)
    record('source_test_identities:' + profile, summary['source_sha256_before_tests'] == summary['source_sha256_after_tests'] == context.get('source') and summary['test_source_sha256_before_tests'] == summary['test_source_sha256_after_tests'] == {name: value for name, value in context.get('source', {}).items() if name.startswith('tests/')} and summary['source_files_unchanged'] is True)
    cache = (directory / 'original-CMakeCache.txt').read_text()
    record('native_off_cache:' + profile, 'FORGE_NATIVE:BOOL=OFF' in cache and re.search(r'^CMAKE_CXX_COMPILER:(?:STRING|FILEPATH)=' + re.escape(CXX) + r'$', cache, re.M) is not None)
    compilation = load(directory / 'original-compile_commands.json')
    record('full18_compilation_records:' + profile, len(compilation) == 18)
    record('pawn_span_compilation_present:' + profile, sum(Path(row['file']) == SOURCE / 'tests/pawn_span_tests.cpp' for row in compilation) == 1)
    record('nearest_pawn_compilation_present:' + profile, sum(Path(row['file']) == SOURCE / 'tests/nearest_pawn_tests.cpp' for row in compilation) == 1)
    record('pv_metadata_compilation_present:' + profile, sum(Path(row['file']) == SOURCE / 'tests/pv_metadata_tests.cpp' for row in compilation) == 1)
    for row in compilation:
        tokens = shlex.split(row['command'])
        record('strict_actual_flags:' + profile + ':' + row['file'], tokens[0] == CXX and all(flag in tokens for flag in FLAGS + ['-DNDEBUG', '-std=gnu++20']) and ('-O3' if profile == 'release' else '-O2') in tokens and not any(token.startswith('-flto') or token in ['-ffast-math', '-march=native', '-ffp-contract=fast'] for token in tokens))
        if profile in ['asan', 'tsan']:
            record('actual_sanitizer_instrumentation:' + profile + ':' + row['file'], ('-fsanitize=address,undefined' if profile == 'asan' else '-fsanitize=thread') in tokens and '-fno-omit-frame-pointer' in tokens and '-fno-pie' in tokens)
    if profile in ['asan', 'tsan']:
        link = (build / 'CMakeFiles/forge.dir/link.txt').read_text()
        record('actual_sanitizer_link:' + profile, ('-fsanitize=address,undefined' if profile == 'asan' else '-fsanitize=thread') in link and '-no-pie' in link)
    diagnostics = scan_logs(profile, [directory / 'ctest.stdout', directory / 'ctest.stderr', last_path, directory / 'original-uci-regression.log', directory / 'original-ownbook-regression.json'])
    context[profile] = summary
    return {'profile': profile, 'recorded_status': summary['status'], 'ctest_passes': 14, 'correction_checks': 54, 'runtime_psqt_checks': 347, 'pawn_span_checks': int(pawn_checks), 'nearest_pawn_checks': 791680, 'nearest_pawn_sets': 395840, 'nearest_constexpr_assertions': nearest_assertions, 'pv_metadata_assertions': 56, 'pv_metadata_cases': [list(row) for row in pv_rows], 'binaries': current, 'diagnostics': diagnostics, 'started_utc': summary['started_utc'], 'completed_utc': summary['completed_utc']}


def release_signature():
    directory = HERE / 'release-signature-wrapper-attempt1'
    wrapper = load(directory / 'summary.json')
    protocol_path = HERE / 'RELEASE-SIGNATURE-PROTOCOL.json'
    protocol = load(protocol_path)
    clear = context['clear']
    record('release_signature_wrapper_pass', wrapper['status'] == 'PASS' and wrapper['source_commit'] == REV and wrapper['timing_comparison'] is False)
    record('explicit_zero_observer_protocol', protocol['schema'] == 'pv-metadata-release-signature-v1' and protocol['baseline_source_commit'] == PARENT_REV and protocol['exact_parent_search_parity_required'] is False and protocol['observational_cold_warm_searches'] == 0 and clear['exact_search_parity_required'] is False and clear['observational_cold_warm_searches'] == 0 and wrapper['exact_search_parity_required'] is False and wrapper['observational_cold_warm_searches'] == 0)
    baseline_source = Path(protocol['baseline_source_root'])
    parent_data = git('archive', PARENT_REV, 'CMakeLists.txt', 'LICENSE', 'src', 'include', 'tests', 'bench', 'tools')
    with tarfile.open(fileobj=io.BytesIO(parent_data)) as archive:
        parent_source = {item.name: sha(archive.extractfile(item).read()) for item in archive.getmembers() if item.isfile()}
    actual_parent = {p.relative_to(baseline_source).as_posix(): digest(p) for p in baseline_source.rglob('*') if p.is_file()}
    record('baseline21_complete_source_preserved', len(parent_source) == 76 and actual_parent == parent_source == wrapper['baseline_source_sha256_before'] == wrapper['baseline_source_sha256_after'])
    record('candidate_complete_source_signature_bound', wrapper['source_sha256_before'] == wrapper['source_sha256_after'] == context.get('source'))
    allowed_existing = {'CMakeLists.txt', 'src/uci.cpp', 'src/search.cpp'}
    candidate_source = context.get('source', {})
    record('only_declared_frozen22_source_changes', set(candidate_source) == set(parent_source) | {'tests/pv_metadata_tests.cpp'} and all(candidate_source[name] == value for name, value in parent_source.items() if name not in allowed_existing))
    baseline_search = (baseline_source / 'src/search.cpp').read_text()
    anchor = '            ss->excluded_move = move;\n            const int singular_score = search(board, ss, singular_depth, singular_beta - 1, singular_beta, cut_node);\n'
    fixed = '            const bool saved_tt_pv = ss->tt_pv;\n' + anchor + '            ss->tt_pv = saved_tt_pv;\n'
    record('exact_two_line_caller_tt_pv_save_restore', baseline_search.count(anchor) == 1 and (SOURCE / 'src/search.cpp').read_text() == baseline_search.replace(anchor, fixed, 1))
    paths = {name: Path(value) for name, value in wrapper['input_paths'].items()}
    release_gate = context['release']
    expected_paths = {'candidate/' + name: BASE / 'pv-metadata-native-release' / name for name in BINARY_NAMES}
    expected_paths.update(baseline_engine=Path(protocol['baseline_engine']), baseline_core=Path(protocol['baseline_core']), baseline_nnue_object=Path(protocol['baseline_nnue_object']), release_signature_protocol=protocol_path)
    expected_paths.update({'baseline_source/' + name: baseline_source / name for name in protocol['protected_nonsearch_source_sha256']})
    record('exact_release_signature_input_paths', paths == expected_paths)
    current = {name: digest(path) for name, path in paths.items()}
    record('all_signature_inputs_preserved', current == wrapper['input_sha256_before'] == wrapper['input_sha256_after'])
    record('candidate_all17_bound_to_release', len(release_gate['binary_sha256_after']) == 17 and all(current['candidate/' + name] == value for name, value in release_gate['binary_sha256_after'].items()))
    record('baseline21_engine_core_pinned', current['baseline_engine'] == protocol['baseline_engine_sha256'] == '769583f71cf6af053010f1ea9033bd92b5104e4a7235af1b9f61b689d5a5174b' and current['baseline_core'] == protocol['baseline_core_sha256'] == 'f2c3d5f5ecd14d97e19ba32af67e0b3c2579339dc3b7266bf85f9df9c275fde3')
    record('baseline21_nnue_object_pinned', current['baseline_nnue_object'] == protocol['baseline_nnue_object_sha256'] == 'e8dfc576e6b42ffa4de5d4991d0f3ae7c3e9be7f5a818126c520dee386f6a967')
    record('candidate_nnue_object_exact_parent21', current['candidate/CMakeFiles/forge_core.dir/src/nnue.cpp.o'] == current['baseline_nnue_object'])
    protected = protocol['protected_nonsearch_source_sha256']
    root_gate = load(HERE / 'ROOT-FROZEN-SOURCE-GATES.json')
    record('protected_nonsearch_boundaries', set(protected).issubset(root_gate['unchanged_boundaries']) and all(candidate_source[name] == parent_source[name] == current['baseline_source/' + name] == value for name, value in protected.items()))
    steps = wrapper['steps']
    record('exact_one_signature_step', [row['label'] for row in steps] == ['bench11'])
    for row in steps:
        saved = load(directory / 'bench11-command.json')
        record('signature_command_facts', {key: value for key, value in row.items() if key != 'label'} == saved and row['command'] == [str(BASE / 'pv-metadata-native-release/forge')] and row['cwd'] == str(ROOT) and row['timeout_seconds'] == 30 and row['exit_code'] == 0 and row['error'] is None and row['timed_out'] is False and row['input_sha256_after'] == current and row['source_sha256_after'] == candidate_source and row['baseline_source_sha256_after'] == parent_source)
        streams('signature:bench11', directory, row, '.bin')
        cleanup_fact('signature:bench11', row['cleanup'])
        record('signature_exact_stdin', (directory / 'bench11.stdin.bin').read_bytes() == b'bench 11\nquit\n' and digest(directory / 'bench11.stdin.bin') == row['stdin_sha256'])
    raw = (directory / 'bench11.stdout.bin').read_bytes()
    signatures = [int(value) for value in re.findall(rb'^info string bench depth 11 nodes (\d+) time \d+ nps \d+\s*$', raw, re.M)]
    record('preregistered_frozen22_bench292545', signatures == wrapper['actual_bench11_signatures'] == [292545] and wrapper['bench11_expected_nodes'] == protocol['default_bench11_expected_nodes'] == clear['expected_bench11_nodes'] == 292545)
    record('signature_between_release_and_asan', datetime.datetime.fromisoformat(context['release']['completed_utc']) <= datetime.datetime.fromisoformat(wrapper['started_utc']) <= datetime.datetime.fromisoformat(wrapper['completed_utc']) <= datetime.datetime.fromisoformat(context['asan']['started_utc']))
    diagnostics = scan_logs('release_signature', [directory / 'bench11.stdout.bin', directory / 'bench11.stderr.bin'])
    return {'preregistered_default_bench11_nodes': signatures, 'signature_processes': len(steps), 'exact_parent_search_parity_required': False, 'observational_cold_warm_searches': 0, 'protected_nonsearch_files': len(protected), 'baseline_complete_source_files': len(parent_source), 'diagnostics': diagnostics}

def optional_active(required):
    import chess
    wrapper_path = HERE / 'active-uci-wrapper-attempt1/COMMAND.json'
    if not wrapper_path.exists():
        record('optional_active_presence', not required, required=required, performed=False)
        return {'performed': False, 'required': required}
    wrapper = load(wrapper_path)
    directory = HERE / 'active-uci-tsan-attempt1'
    config = load(directory / 'configuration.json')
    summary = load(directory / 'summary.json')
    result = load(directory / 'process-00/result.json')
    protocol = load(HERE / 'ACTIVE-UCI-PROTOCOL.json')
    record('active_wrapper_pass', wrapper['status'] == 'PASS' and wrapper['exit_code'] == 0 and wrapper['error'] is None and wrapper['timed_out'] is False)
    cleanup_fact('active_wrapper', wrapper['cleanup'])
    record('active_default_unsuppressed_tsan', wrapper['tsan_options'] == config['tsan_options'] == 'halt_on_error=1:exitcode=66' and wrapper['tsan_disabled_checks'] == [] and config['attempts'] == 1 and config['stop_before_active_mutations'] is False)
    record('active_source_unchanged', wrapper['source_sha256_before'] == wrapper['source_sha256_after'] == context.get('source'))
    record('active_exact_wrapper_command', wrapper['command'] == [PYTHON, '-B', str(HERE / 'active-uci-edges.py'), '--engine', str(BASE / 'pv-metadata-native-tsan/forge'), '--output', str(directory), '--session-timeout', '90'] and wrapper['cwd'] == str(ROOT) and wrapper['timeout_seconds'] == 120 and config['engine'] == str(BASE / 'pv-metadata-native-tsan/forge') and config['session_timeout_seconds'] == 90)
    inputs = {'engine': BASE / 'pv-metadata-native-tsan/forge', 'core': BASE / 'pv-metadata-native-tsan/libforge_core.a', 'runtime_psqt_test_object': BASE / 'pv-metadata-native-tsan/CMakeFiles/forge_runtime_psqt_tests.dir/tests/runtime_psqt_tests.cpp.o', 'runtime_psqt_test_executable': BASE / 'pv-metadata-native-tsan/forge_runtime_psqt_tests', 'pawn_span_test_object': BASE / 'pv-metadata-native-tsan/CMakeFiles/forge_pawn_span_tests.dir/tests/pawn_span_tests.cpp.o', 'pawn_span_test_executable': BASE / 'pv-metadata-native-tsan/forge_pawn_span_tests', 'nnue_object': BASE / 'pv-metadata-native-tsan/CMakeFiles/forge_core.dir/src/nnue.cpp.o', 'nearest_pawn_test_object': BASE / 'pv-metadata-native-tsan/CMakeFiles/forge_nearest_pawn_tests.dir/tests/nearest_pawn_tests.cpp.o', 'nearest_pawn_test_executable': BASE / 'pv-metadata-native-tsan/forge_nearest_pawn_tests', 'pv_metadata_test_object': BASE / 'pv-metadata-native-tsan/CMakeFiles/forge_pv_metadata_tests.dir/tests/pv_metadata_tests.cpp.o', 'pv_metadata_test_executable': BASE / 'pv-metadata-native-tsan/forge_pv_metadata_tests', 'active_driver': HERE / 'active-uci-edges.py', 'trusted_driver': HERE / 'trusted-run-full-engine-tt.py'}
    hashes = {name: digest(path) for name, path in inputs.items()}
    record('active_all_input_identities', hashes == wrapper['input_sha256_before'] == wrapper['input_sha256_after'])
    record('active_frozen_helper_identity', hashes['trusted_driver'] == context.get('source', {}).get('tools/audit/run-full-engine-tt.py') == protocol['trusted_driver_sha256'])
    record('active_driver_protocol_identity', hashes['active_driver'] == protocol['adapted_active_sha256'] == config['driver_sha256'] and config['trusted_driver_sha256'] == hashes['trusted_driver'])
    original_active = ROOT / protocol['original_active_driver']
    record('active_only_locator_adapted', digest(original_active) == protocol['original_active_sha256'] and original_active.read_text().replace("trusted_path = root / 'tools/audit/run-full-engine-tt.py'", "trusted_path = Path(__file__).with_name('trusted-run-full-engine-tt.py')", 1) == inputs['active_driver'].read_text())
    record('active_session_pass_and_final_capture', summary['status'] == 'passed' and summary['completed_all_scenarios'] is True and summary['hard_deadline_expired'] is False and summary['session'] == result and result['completed'] is True and result['exit_code'] == 0 and result['signal'] is None and result['capture_complete'] is True and result['reader_threads_joined'] is True and result['stream_hashes_final'] is True and result['reader_errors'] == [] and result['sanitizer_classification'] == 'none')
    record('active_engine_hashes', summary['engine_sha256_before'] == summary['engine_sha256_after'] == config['engine_sha256'] == hashes['engine'])
    record('active_oracle_version', config['python_chess_version'] == chess.__version__, oracle_version=chess.__version__)
    event_data = (directory / 'events.jsonl').read_bytes()
    events = [json.loads(line) for line in event_data.splitlines()]
    record('active_event_hash_sequence', sha(event_data) == summary['events_sha256'] and [row['sequence'] for row in events] == list(range(1, len(events) + 1)))
    record('active_no_error_deadline_kill_events', not any(row['kind'] in ['reader_error', 'forced_kill', 'hard_session_deadline_expired'] for row in events))
    for stream in ['stdin', 'stdout', 'stderr']:
        data = (directory / ('process-00/' + stream + '.bin')).read_bytes()
        reconstructed = b''.join(base64.b64decode(row['base64'], validate=True) for row in events if row['kind'] == 'bytes' and row.get('process') == 0 and row['stream'] == stream)
        record('active_raw_bytes_reassembled:' + stream, data == reconstructed and sha(data) == result['stream_sha256'][stream])
    raw_stdin = (directory / 'process-00/stdin.bin').read_bytes()
    record('active_command_bytes_exact', raw_stdin == ''.join(row['text'] + '\n' for row in events if row['kind'] == 'command' and row.get('process') == 0).encode('ascii'))
    record('active_both_output_eofs', {row['stream'] for row in events if row['kind'] == 'eof' and row.get('process') == 0} == {'stdout', 'stderr'})
    searches = result['searches']
    labels = ['active1-threads4', 'active4-hash-resize', 'active4-threads1', 'active1-clear-hash', 'active1-newgame', 'active1-position', 'active1-stop', 'active1-quit']
    mutations = ['setoption name Threads value 4', 'setoption name Hash value 2', 'setoption name Threads value 1', 'setoption name Clear Hash', 'ucinewgame', 'position startpos moves e2e4 e7e5', 'stop', 'quit']
    record('active_exact8_scenarios', len(searches) == 8 and [row['label'] for row in searches] == labels and [row['mutation'] for row in searches] == mutations)
    positions = ['startpos', 'fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1', 'fen 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1']
    moved = chess.Board(); moved.push_uci('e2e4'); moved.push_uci('e7e5')
    expected_positions = [positions[0], positions[1], positions[2], positions[1], positions[2], positions[1], 'fen ' + moved.fen(), positions[1]]
    record('active_exact_searched_positions', [row['position'] for row in searches] == expected_positions and [row['quit_edge'] for row in searches] == [False] * 7 + [True])

    for index, item in enumerate(searches):
        label = item['label']
        record('active_completion_samples:' + label, item['completed'] is True and item['legality'] == 'checked_with_python_chess' and item['start_monotonic_ns'] <= item['mutation_sent_monotonic_ns'] <= item['finish_monotonic_ns'] and item['node_hashfull_samples'] and any(row['nodes'] > 0 for row in item['node_hashfull_samples']) and all(0 <= row['hashfull'] <= 1000 for row in item['node_hashfull_samples']))
        board = chess.Board() if item['position'] == 'startpos' else chess.Board(item['position'].removeprefix('fen '))
        fields = item['bestmove_line'].split()
        move = chess.Move.from_uci(fields[1])
        legal = move in board.legal_moves
        if len(fields) == 4:
            board.push(move)
            legal = legal and fields[2] == 'ponder' and chess.Move.from_uci(fields[3]) in board.legal_moves
        record('active_saved_move_legal:' + label, legal)
        start = next(row['sequence'] for row in events if row['kind'] == 'active_edge_start' and row['label'] == label)
        end = next(row['sequence'] for row in events if row['kind'] == 'active_edge_complete' and row['label'] == label)
        segment = [row for row in events if start < row['sequence'] < end]
        position_commands = [row['text'] for row in events if row['kind'] == 'command' and row['text'].startswith('position ') and row['sequence'] < start]
        record('active_actual_searched_position:' + label, position_commands and position_commands[-1] == 'position ' + item['position'])
        consumed = [row['text'] for row in segment if row['kind'] == 'line']
        record('active_exact_consumed_lines:' + label, consumed == item['observed_lines'])
        go = next(row['sequence'] for row in segment if row['kind'] == 'command' and row['text'] == 'go infinite')
        mutation = next(row['sequence'] for row in segment if row['kind'] == 'command' and row['text'] == item['mutation'])
        positive = [row['sequence'] for row in segment if row['kind'] == 'line' and re.search(r'^info depth .*\bnodes [1-9][0-9]*\b', row['text'])]
        record('active_positive_nodes_before_mutation:' + label, any(go < value < mutation for value in positive) and not any(row['kind'] == 'command' and row['text'] == 'stop' and go < row['sequence'] < mutation for row in segment))
        bests = [i for i, line in enumerate(consumed) if line.startswith('bestmove ')]
        record('active_one_ordered_bestmove:' + label, len(bests) == 1 and (index == 7 or (item['bestmove_before_readyok'] is True and bests[0] < consumed.index('readyok'))))
    raw_stdout = (directory / 'process-00/stdout.bin').read_bytes()
    record('active8_raw_bestmoves', len(re.findall(rb'(?m)^bestmove ', raw_stdout)) == 8)
    for stream in ['stdout', 'stderr']:
        record('active_wrapper_stream_hash:' + stream, digest(wrapper_path.parent / (stream + '.bin')) == wrapper[stream + '_sha256'])
    diagnostic = scan_logs('active', [directory / 'process-00/stdout.bin', directory / 'process-00/stderr.bin', wrapper_path.parent / 'stdout.bin', wrapper_path.parent / 'stderr.bin'])
    return {'performed': True, 'scenarios': len(searches), 'saved_move_oracle': 'python-chess ' + chess.__version__, 'engine_sha256': hashes['engine'], 'diagnostics': diagnostic}


def whole_originals():
    path = HERE / 'ORIGINALS-FINAL-SHA256.json'
    snapshot = load(path)
    record('whole_originals_snapshot_source', snapshot['source_commit'] == REV and snapshot['engines_or_builds_executed_for_snapshot'] is False)
    expected_roots = {'source': str(SOURCE), **{profile: str(BASE / ('pv-metadata-native-' + profile)) for profile in ['release', 'asan', 'tsan']}}
    record('whole_originals_exact_four_roots', {label: tree['root'] for label, tree in snapshot['trees'].items()} == expected_roots)
    counts = {}
    for label, tree in snapshot['trees'].items():
        root = Path(tree['root'])
        current = {p.relative_to(root).as_posix(): p for p in root.rglob('*') if p.is_file()}
        record('whole_originals_inventory:' + label, set(current) == set(tree['files']))
        counts[label] = len(current)
        for name, item in tree['files'].items():
            expected_sha = item if isinstance(item, str) else item['sha256']
            okay = digest(current[name]) == expected_sha
            if isinstance(item, dict) and 'bytes' in item:
                okay = okay and current[name].stat().st_size == item['bytes']
            if isinstance(item, dict) and 'mode' in item:
                okay = okay and stat.S_IMODE(current[name].stat().st_mode) == item['mode']
            record('whole_originals_file:' + label + ':' + name, okay)
        directory_modes = {'.': stat.S_IMODE(root.stat().st_mode), **{p.relative_to(root).as_posix(): stat.S_IMODE(p.stat().st_mode) for p in root.rglob('*') if p.is_dir()}}
        record('whole_originals_directory_modes:' + label, directory_modes == tree['directory_modes'])
    record('whole_originals_tree_counts', counts.get('source') == 77 and all(counts.get(profile, 0) > 0 for profile in ['release', 'asan', 'tsan']), observed=counts)
    for label, item in snapshot['single_files'].items():
        target = Path(item['path'])
        record('whole_originals_single:' + label, digest(target) == item['sha256'] and target.stat().st_size == item['bytes'] and stat.S_IMODE(target.stat().st_mode) == item['mode'])
    compiler = snapshot['compiler']
    record('whole_originals_compiler_hash', compiler['path'] == CXX and str(Path(CXX).resolve()) == compiler['resolved_path'] and digest(Path(CXX)) == compiler['sha256'])
    return {'snapshot_sha256': digest(path), 'file_counts': counts, 'single_files': list(snapshot['single_files'])}


def no_live_groups():
    live = []
    for directory in Path('/proc').iterdir():
        if directory.name.isdigit():
            try:
                text = (directory / 'stat').read_text()
                fields = text[text.rfind(')') + 2:].split()
                if int(fields[2]) in groups and fields[0] != 'Z':
                    live.append({'pid': int(directory.name), 'group': int(fields[2]), 'state': fields[0]})
            except (OSError, ValueError, IndexError):
                pass
    record('no_current_live_owned_groups', not live, live=live)
    return {'groups': sorted(groups), 'live_processes': live}


def main():
    global fact_stream, REV
    parser = argparse.ArgumentParser()
    parser.add_argument('--require-active', action='store_true', default=True, help='Frozen22 final audit always requires the eight active-TSan searches')
    args = parser.parse_args()
    clear = load(HERE / 'ROOT-CLEARANCE.json')
    if clear.get('authorized') is not True:
        raise SystemExit('Preparation only: explicit root clearance is pending; no audit attempted')
    candidate = clear.get('source_commit')
    if not isinstance(candidate, str) or re.fullmatch(r'[0-9a-f]{40}', candidate) is None:
        raise SystemExit('Exact frozen source SHA required; no audit attempted')
    if type(clear.get('expected_pawn_span_checks')) is not int or clear['expected_pawn_span_checks'] <= 0:
        raise SystemExit('Root-frozen pawn-span check count required; no audit attempted')
    if clear.get('expected_nearest_checks') != 791680 or clear.get('expected_nearest_sets') != 395840 or clear.get('expected_nearest_constexpr_assertions') != 6:
        raise SystemExit('Exact frozen nearest-pawn schema required; no audit attempted')
    if clear.get('exact_search_parity_required') is not False or clear.get('observational_cold_warm_searches') != 0 or clear.get('expected_pv_metadata_assertions') != 56:
        raise SystemExit('Explicit frozen22 zero-observer/PV56 root protocol required; no audit attempted')
    REV = candidate
    context['clear'] = clear
    paths = [HERE / ('independent-audit' + suffix) for suffix in ['.json', '.md', '-facts.jsonl']]
    if any(path.exists() for path in paths):
        raise SystemExit('Refusing to overwrite a previous audit attempt')
    with paths[2].open('x') as fact_stream:
        stage('frozen_source', frozen_source)
        for profile in ['release', 'asan', 'tsan']:
            stage(profile, lambda profile=profile: audit_profile(profile))
        stage('release_signature', release_signature)
        stage('active_uci', lambda: optional_active(args.require_active))
        stage('whole_originals', whole_originals)
        stage('process_groups', no_live_groups)
        profile_records = [context.get(name) for name in ['release', 'asan', 'tsan']]
        if all(profile_records):
            record('three_profiles_executed_serially', all(datetime.datetime.fromisoformat(profile_records[i]['completed_utc']) <= datetime.datetime.fromisoformat(profile_records[i + 1]['started_utc']) for i in [0, 1]))
        failed = [row for row in checks if not row['passed']]
        report = {'status': 'passed' if not failed else 'failed', 'audited_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'source_commit': REV, 'parent_source_commit': PARENT_REV, 'check_count': len(checks), 'failed_check_count': len(failed), 'checks': checks, 'facts': facts, 'facts_stream': paths[2].name, 'facts_stream_sha256': digest(paths[2]), 'checker_sha256': digest(Path(__file__)), 'engine_compiler_or_test_execution_during_audit': False, 'original_evidence_mutated': False, 'qualified_driver_limitations': ['The 1200-second profile timeout applies per recorded command.', 'The release signature is one30-second bounded process; exact parent search-response equality is intentionally invalid for this fix, and the root-approved observational count is0.', 'Finite fixtures and TSan coverage do not establish universal correctness or playing strength.'], 'scope': 'Bounded PV-metadata search-correctness evidence: saved baseline21 RED and actual frozen22 core regression, single benchmark signature and active-TSan coverage; no private-ABI cross-link or exact parent-response equality claim. No NPS, Elo or native-Ryzen performance claim.'}
        with paths[0].open('x') as stream:
            json.dump(report, stream, indent=2, allow_nan=False); stream.write('\n')
        details = 'All independent checks passed.' if not failed else 'Failed checks: ' + ', '.join(row['name'] for row in failed)
        text = f"""PV-metadata independent evidence audit: {report['status']}.

{details} Check count: {len(checks)}. Every check/stage fact was flushed before
the final gate. No engines, compilers or tests ran and no originals were changed.

Exact source77/Git/root gates; fourteen CTests per profile (42total), actual PV56
assertions/five raw cases, nearest791680/395840sets+6constexpr, pawn37320,
runtime347 and correction54; fatal default TSan, strict flags, cleanup and
seventeen-artifact identities; source+three-build byte/size/mode originals.

Saved actual unmodified21 RED is pinned (56assertions,2expected failures).
Parent21 complete76source, protected nonsearch boundaries, engine/core/NNUE
object are pinned; only the two-line caller tt_pv save/restore is allowed in
search.cpp. Candidate Release NNUE object must equal the parent object.

One default bench292545 signature follows Release and precedes ASan. Root must
explicitly authorize exact_search_parity_required=false and observation count0;
no exact parent search equality or cold/warm observation is claimed. All eight
active TSan transitions remain required. Finite coverage does not establish
universal correctness, source authenticity beyond Git/root pins, speed or Elo.
"""
        with paths[1].open('x') as stream:
            stream.write(text)
    print(json.dumps({'status': report['status'], 'check_count': len(checks), 'failed_check_count': len(failed), 'facts': {name: value for name, value in facts.items() if name in ['release_signature', 'active_uci']}}, indent=2))
    return 0 if not failed else 1


if __name__ == '__main__':
    raise SystemExit(main())

