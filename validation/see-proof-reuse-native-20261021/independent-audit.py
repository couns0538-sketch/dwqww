#!/usr/bin/env python3
"""Audit saved24 pure SEE proof-reuse/parity evidence; never run engines, compilers or tests.

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
HERE = ROOT / 'validation/see-proof-reuse-native-20261021'
SOURCE = Path('/workspace/.cloud-setup/see-proof-reuse-native-source')
REV = None  # Set only in main after explicit root clearance for the frozen source.
PARENT_REV = '1d3ed25bea2c8b781f7ee5a178af0f66061b3984'
PV_RED_REV = '2e151d019bc58dff2ab4e76e99ef99516af8d222'
ALLOWED_SOURCE_CHANGES = {'CMakeLists.txt', 'src/uci.cpp', 'src/search.cpp', 'tests/tests.cpp'}
BASE = Path('/workspace/.cloud-setup')
CMAKE = '/workspace/.cloud-setup/venv/lib/python3.12/site-packages/cmake/data/bin/cmake'
CTEST = '/workspace/.cloud-setup/venv/lib/python3.12/site-packages/cmake/data/bin/ctest'
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
    record('exact_root_clearance', clear['authorized'] is True and clear['source_commit'] == REV and clear['baseline_source_commit'] == PARENT_REV and clear['required_version'] == '6.4.24' and clear['expected_runtime_psqt_checks'] == 347 and clear['expected_pawn_span_checks'] == 37320 and clear['expected_nearest_checks'] == 791680 and clear['expected_nearest_sets'] == 395840 and clear['expected_nearest_constexpr_assertions'] == 6 and clear['expected_pv_metadata_assertions'] == 56 and clear['expected_pv_metadata_test_source_sha256'] == '8000b717a298c4c8bb637752fcc57a0ce485110a12edc4a505f3d0452620bd1e' and clear['exact_search_parity_required'] is True and clear['expected_cold_warm_searches'] == 56 and clear['source_files'] == 77 and clear['expected_ctest_per_profile'] == 14 and clear['expected_bench11_nodes'] is None and clear['benchmark_signature_mode'] == 'FIRST_CAPTURE_EXCLUSIVE_FREEZE' and clear['strict_fp'] is True and clear['no_lto'] is True and clear['profiles_sequential'] is True and clear['build_jobs'] == 2 and clear['default_tsan_options'] == 'halt_on_error=1:exitcode=66' and clear['suppression_or_deadlock_detector_disabled'] is False and clear['performance_or_strength_inference'] is False)
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
    record('root_frozen_504_SEE_contract_schema', clear['expected_see_threshold_assertions']==504 and clear['expected_see_threshold_success_line']=='SEE threshold contract: assertions 504 failures 0')
    record('root_frozen_monotonic_core_test_source', expected['tests/tests.cpp'] == clear['expected_core_tests_source_sha256'])
    record('root_frozen_tt_regression_source', expected['tests/tt_coherence_tests.cpp'] == clear['expected_tt_test_source_sha256'])
    root_gate = load(HERE / 'ROOT-FROZEN-SOURCE-GATES.json')
    record('root_frozen_source_gate_identity', root_gate['source_commit'] == REV and root_gate['baseline_commit'] == PARENT_REV and root_gate['inputs'] == expected and set(root_gate['unchanged_boundaries']) == set(expected) - ALLOWED_SOURCE_CHANGES)
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
    record('actual_red_test_schema_identity', protocol['historical_pv_red_source_commit'] == PV_RED_REV and digest(schema_path) == protocol['pv_metadata_test_schema_sha256'] == '0b146976915b9a40b25873b0be2c168322331cd68bc352608db49bc860d6d252' and expected['tests/pv_metadata_tests.cpp'] == protocol['pv_metadata_test_source_sha256'] == schema['source_sha256'] == '8000b717a298c4c8bb637752fcc57a0ce485110a12edc4a505f3d0452620bd1e')
    red_path = schema_path.parent / 'baseline-attempt1/result.json'
    red = load(red_path)
    record('actual_saved_baseline21_red', digest(red_path) == schema['baseline_result_sha256'] and red['status'] == 'EXPECTED_BASELINE_RED_PERMANENT_REGRESSION' and red['source_commit'] == PV_RED_REV and red['assertions'] == schema['observed_baseline_assertions'] == 56 and schema['observed_baseline_failures'] == 2 and schema['observed_baseline_exit_code'] == 1 and red['inputs_before'] == red['inputs_after'] and red['core_unchanged'] is True and red['all_other_assertions_passed'] is True)
    red_steps = red['steps']
    record('baseline_red_expected_process_exits', [row['label'] for row in red_steps] == ['compile-link', 'actual-core-unit'] and [row['exit_code'] for row in red_steps] == [0, 1] and all(row['cleanup']['no_live_owned_processes'] and not row['cleanup']['unexpected_live_members_after_command'] for row in red_steps))
    for row in red_steps:
        for stream in ['stdout', 'stderr']:
            record('baseline_red_saved_stream:' + row['label'] + ':' + stream, digest(red_path.parent / (row['label'] + '.' + stream)) == row[stream + '_sha256'])
    red_stdout = (red_path.parent / 'actual-core-unit.stdout').read_text()
    red_stderr = (red_path.parent / 'actual-core-unit.stderr').read_text()
    record('baseline_red_actual56_two_failures', re.findall(r'^PV metadata: assertions (\d+) failures (\d+)\s*$', red_stdout, re.M) == [('56', '2')] and re.findall(r'^FAIL (.*)$', red_stderr, re.M) == schema['observed_failed_assertions'] == red['expected_failures'])
    record('baseline_red_actual_five_rows', [list(row) for row in re.findall(r'^PV_METADATA_CASE (\w+) nodes=(\d+) aborted=([01]) flag=([01]) pv_moves=(\d+)\s*$', red_stdout, re.M)] == schema['case_rows'] == red['case_rows'])
    return {'source_commit': REV, 'source_files': len(expected), 'source_tar_sha256': sha(data), 'runtime_psqt_checks': 347, 'pawn_span_checks': clear['expected_pawn_span_checks'], 'nearest_pawn_checks': 791680, 'nearest_pawn_sets': 395840, 'nearest_constexpr_assertions': 6, 'correction_history_checks': 54, 'historical_pv_red_source_commit': PV_RED_REV, 'historical_pv_red_saved_assertions': 56, 'historical_pv_red_saved_failures': 2, 'parent_red_executed_during_audit': False}


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
    build = BASE / ('see-proof-reuse-native-' + profile)
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
    core_block = re.search(r'(?ms)^\d+/\d+ Testing: forge_tests\n.*?(?=^\d+/\d+ Testing: |\Z)', last)
    core_text = core_block.group() if core_block else ''
    record('actual504_SEE_threshold_contract:' + profile, re.findall(r'^SEE threshold contract: assertions (\d+) failures (\d+)\s*$',core_text,re.M)==[('504','0')] and summary['see_threshold_contract_actual_summaries']==[['504','0']] and summary['core_tests_source_sha256']==context['source']['tests/tests.cpp']==context['clear']['expected_core_tests_source_sha256'])
    tt_block = re.search(r'\n\d+/14 Testing: forge_tt_tests\n(.*?)(?=\n\d+/14 Testing:|\Z)', last, re.S)
    tt_text = tt_block[1] if tt_block else ''
    tt_groups = context['clear']['expected_tt_groups']
    tt_success = context['clear']['expected_tt_group_success_line']
    record('actual_root_frozen_tt_groups:' + profile, re.findall(r'^All(\d+) TT coherence/regression groups passed\s*$', tt_text, re.M) == summary['tt_coherence_contract_actual_groups'] == [str(tt_groups)] and tt_text.splitlines().count(tt_success) == 1 and summary['tt_coherence_actual_success_lines'] == [tt_success] and not re.search(r'^FAIL ', tt_text, re.M))

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
    return {'profile': profile, 'recorded_status': summary['status'], 'ctest_passes': 14, 'correction_checks': 54, 'tt_coherence_groups': tt_groups, 'tt_coherence_success_line': tt_success, 'runtime_psqt_checks': 347, 'pawn_span_checks': int(pawn_checks), 'nearest_pawn_checks': 791680, 'nearest_pawn_sets': 395840, 'nearest_constexpr_assertions': nearest_assertions, 'pv_metadata_assertions': 56, 'pv_metadata_cases': [list(row) for row in pv_rows], 'binaries': current, 'diagnostics': diagnostics, 'started_utc': summary['started_utc'], 'completed_utc': summary['completed_utc']}


def release_signature():
    directory = HERE / 'release-signature-wrapper-attempt1'
    wrapper = load(directory / 'summary.json')
    protocol_path = HERE / 'RELEASE-SIGNATURE-PROTOCOL.json'
    protocol = load(protocol_path)
    clear = context['clear']
    record('release_signature_wrapper_pass', wrapper['status'] == 'PASS' and wrapper['source_commit'] == REV and wrapper['timing_comparison'] is False)
    record('explicit_exact56_parity_protocol', protocol['schema'] == 'see-proof-reuse-release-signature-v1' and protocol['baseline_source_commit'] == PARENT_REV and protocol['exact_parent_search_parity_required'] is True and protocol['required_cold_warm_searches'] == 56 and clear['exact_search_parity_required'] is True and clear['expected_cold_warm_searches'] == 56 and wrapper['exact_search_parity_required'] is True and wrapper['expected_cold_warm_searches'] == 56)
    baseline_source = Path(protocol['baseline_source_root'])
    parent_data = git('archive', PARENT_REV, 'CMakeLists.txt', 'LICENSE', 'src', 'include', 'tests', 'bench', 'tools')
    with tarfile.open(fileobj=io.BytesIO(parent_data)) as archive:
        parent_source = {item.name: sha(archive.extractfile(item).read()) for item in archive.getmembers() if item.isfile()}
    actual_parent = {p.relative_to(baseline_source).as_posix(): digest(p) for p in baseline_source.rglob('*') if p.is_file()}
    record('baseline23_complete_source_preserved', len(parent_source) == 77 and actual_parent == parent_source == wrapper['baseline_source_sha256_before'] == wrapper['baseline_source_sha256_after'])
    record('candidate_complete_source_signature_bound', wrapper['source_sha256_before'] == wrapper['source_sha256_after'] == context.get('source'))
    candidate_source = context.get('source', {})
    record('only_root_declared_frozen24_source_changes', set(candidate_source) == set(parent_source) and len(parent_source) == 77 and all(candidate_source[name] == value for name, value in parent_source.items() if name not in ALLOWED_SOURCE_CHANGES))
    paths = {name: Path(value) for name, value in wrapper['input_paths'].items()}
    release_gate = context['release']
    expected_paths = {'candidate/' + name: BASE / 'see-proof-reuse-native-release' / name for name in BINARY_NAMES}
    expected_paths.update(baseline_engine=Path(protocol['baseline_engine']), baseline_core=Path(protocol['baseline_core']), baseline_nnue_object=Path(protocol['baseline_nnue_object']), release_signature_protocol=protocol_path)
    expected_paths.update({'baseline_source/' + name: baseline_source / name for name in protocol['protected_nonsearch_source_sha256']})
    record('exact_release_signature_input_paths', paths == expected_paths)
    current = {name: digest(path) for name, path in paths.items()}
    record('all_signature_inputs_preserved', current == wrapper['input_sha256_before'] == wrapper['input_sha256_after'])
    record('candidate_all17_bound_to_release', len(release_gate['binary_sha256_after']) == 17 and all(current['candidate/' + name] == value for name, value in release_gate['binary_sha256_after'].items()))
    record('baseline23_engine_core_pinned', current['baseline_engine'] == protocol['baseline_engine_sha256'] == '85a3eeaf4c513e1790cb4c2593edb02063cba42d91eb7fc1bd303de026bd2b07' and current['baseline_core'] == protocol['baseline_core_sha256'] == '310ea85577ddd8a4b88479256dbe57fb576a384f24958d46324e82583dbd77c9')
    record('baseline23_nnue_object_pinned', current['baseline_nnue_object'] == protocol['baseline_nnue_object_sha256'] == 'e8dfc576e6b42ffa4de5d4991d0f3ae7c3e9be7f5a818126c520dee386f6a967')
    record('candidate_nnue_object_exact_parent23', current['candidate/CMakeFiles/forge_core.dir/src/nnue.cpp.o'] == current['baseline_nnue_object'])
    protected = protocol['protected_nonsearch_source_sha256']
    root_gate = load(HERE / 'ROOT-FROZEN-SOURCE-GATES.json')
    record('protected_nonsearch_boundaries', set(protected).issubset(root_gate['unchanged_boundaries']) and all(candidate_source[name] == parent_source[name] == current['baseline_source/' + name] == value for name, value in protected.items()))
    steps = wrapper['steps']
    record('exact_one_signature_step', [row['label'] for row in steps] == ['bench11'])
    for row in steps:
        saved = load(directory / 'bench11-command.json')
        record('signature_command_facts', {key: value for key, value in row.items() if key != 'label'} == saved and row['command'] == [str(BASE / 'see-proof-reuse-native-release/forge')] and row['cwd'] == str(ROOT) and row['timeout_seconds'] == 30 and row['exit_code'] == 0 and row['error'] is None and row['timed_out'] is False and row['input_sha256_after'] == current and row['source_sha256_after'] == candidate_source and row['baseline_source_sha256_after'] == parent_source)
        streams('signature:bench11', directory, row, '.bin')
        cleanup_fact('signature:bench11', row['cleanup'])
        record('signature_exact_stdin', (directory / 'bench11.stdin.bin').read_bytes() == b'bench 11\nquit\n' and digest(directory / 'bench11.stdin.bin') == row['stdin_sha256'])
    raw = (directory / 'bench11.stdout.bin').read_bytes()
    signatures = [int(value) for value in re.findall(rb'^info string bench depth 11 nodes (\d+) time \d+ nps \d+\s*$', raw, re.M)]
    record('first_actual_bench11_capture_mode', wrapper['bench11_expected_nodes'] is None and protocol['default_bench11_expected_nodes'] is None and clear['expected_bench11_nodes'] is None and wrapper['benchmark_signature_mode'] == protocol['benchmark_signature_mode'] == clear['benchmark_signature_mode'] == 'FIRST_CAPTURE_EXCLUSIVE_FREEZE')
    record('one_positive_actual_bench11_signature', signatures == wrapper['actual_bench11_signatures'] and len(signatures) == 1 and signatures[0] > 0)
    freeze_path = HERE / 'BENCH-SIGNATURE-FREEZE.json'
    freeze = load(freeze_path)
    record('observed_first_signature_then_parent_comparison', freeze['nodes'] == protocol['baseline_default_bench11_nodes'] == 292545 and wrapper['parent_signature_comparison_after_capture'] == 'PASS')
    record('exclusive_bench_signature_freeze_identity', wrapper['bench_signature_freeze_path'] == freeze_path.name and wrapper['bench_signature_freeze_sha256'] == digest(freeze_path))
    record('frozen_first_actual_bench_source_artifacts', freeze['status'] == 'FROZEN_FIRST_ACTUAL_RELEASE_BENCH11' and freeze['source_commit'] == REV and freeze['release_engine_sha256'] == current['candidate/forge'] and freeze['release_core_sha256'] == current['candidate/libforge_core.a'] and freeze['benchmark_depth'] == 11 and type(freeze['nodes']) is int and freeze['nodes'] > 0 and signatures == [freeze['nodes']] and freeze['signature_processes'] == 1 and freeze['timing_or_elo_inference'] is False)
    record('frozen_first_actual_bench_original_streams', all(freeze['raw_' + stream + '_sha256'] == digest(directory / ('bench11.' + stream + '.bin')) for stream in ['stdin', 'stdout', 'stderr']))
    record('frozen_first_actual_bench_all_inputs', freeze['input_sha256_before'] == freeze['input_sha256_after'] == wrapper['input_sha256_before'] == wrapper['input_sha256_after'] == current)
    record('frozen_first_actual_bench_capture_time', datetime.datetime.fromisoformat(wrapper['started_utc']) <= datetime.datetime.fromisoformat(freeze['captured_utc']) <= datetime.datetime.fromisoformat(wrapper['completed_utc']))
    record('signature_between_release_and_asan', datetime.datetime.fromisoformat(context['release']['completed_utc']) <= datetime.datetime.fromisoformat(wrapper['started_utc']) <= datetime.datetime.fromisoformat(wrapper['completed_utc']) <= datetime.datetime.fromisoformat(context['asan']['started_utc']))
    diagnostics = scan_logs('release_signature', [directory / 'bench11.stdout.bin', directory / 'bench11.stderr.bin'])
    return {'first_captured_default_bench11_nodes': signatures, 'bench_signature_freeze_sha256': digest(freeze_path), 'signature_processes': len(steps), 'exact_parent_search_parity_required': True, 'required_cold_warm_searches': 56, 'protected_nonsearch_files': len(protected), 'baseline_complete_source_files': len(parent_source), 'diagnostics': diagnostics}

def release_parity():
    import chess
    directory = HERE / 'release-parity-wrapper-attempt1'
    output = HERE / 'search-parity-attempt1'
    wrapper = load(directory / 'summary.json')
    protocol = load(HERE / 'PARITY-PROTOCOL.json')
    config = load(output / 'configuration.json')
    summary = load(output / 'summary.json')
    record('release_parity_wrapper_pass', wrapper['status'] == 'PASS' and wrapper['source_commit'] == REV and wrapper['no_parent_red'] is True and wrapper['timing_comparison'] is False)
    record('parity_schema_v1', protocol['schema'] == 'see-proof-reuse-parity-v1' and protocol['candidate_evaluator_file_byte_equality_required'] is False and protocol['parent_red'] is False and protocol['private_worker_crosslink'] is False)
    cases = [
        {'name': 'start', 'position': 'startpos', 'depth': 7},
        {'name': 'kiwipete', 'position': 'fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1', 'depth': 6},
        {'name': 'middlegame', 'position': 'fen r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10', 'depth': 6},
        {'name': 'endgame', 'position': 'fen 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1', 'depth': 7},
        {'name': 'promotion-white', 'position': 'fen 8/k1P5/2K5/8/8/8/8/8 w - - 0 1', 'depth': 1},
        {'name': 'promotion-black', 'position': 'fen 8/8/8/8/8/2k5/K1p5/8 b - - 0 1', 'depth': 1},
        {'name': 'rule50-near95', 'position': 'fen 7k/8/8/8/8/8/8/K6R b - - 95 80', 'depth': 7}]
    record('parity_exact_preregistered_cases_modes', protocol['cases'] == cases and protocol['nnue_modes'] == ['default', 'disabled'] and protocol['threads'] == 1 and protocol['hash_mib'] == 32 and protocol['ownbook'] is False and protocol['ponder'] is False and protocol['total_depth_searches'] == 56 and protocol['exact_comparison_excludes'] == ['time', 'nps'])
    baseline_source = Path(protocol['baseline_public_source_root'])
    parent_data = git('archive', PARENT_REV, 'CMakeLists.txt', 'LICENSE', 'src', 'include', 'tests', 'bench', 'tools')
    parent_source = {}
    with tarfile.open(fileobj=io.BytesIO(parent_data)) as archive:
        for item in archive.getmembers():
            if item.isfile():
                parent_source[item.name] = sha(archive.extractfile(item).read())
    actual_parent_source = {path.relative_to(baseline_source).as_posix(): digest(path) for path in baseline_source.rglob('*') if path.is_file()}
    record('baseline23_complete_source_preserved', len(parent_source) == 77 and actual_parent_source == parent_source == wrapper['baseline_source_sha256_before'] == wrapper['baseline_source_sha256_after'])
    record('candidate_complete_source_parity_bound', wrapper['source_sha256_before'] == wrapper['source_sha256_after'] == context.get('source'))
    paths = {name: Path(value) for name, value in wrapper['input_paths'].items()}
    current = {name: digest(value) for name, value in paths.items()}
    record('all_parity_wrapper_inputs_preserved', current == wrapper['input_sha256_before'] == wrapper['input_sha256_after'])
    release_gate = context.get('release', {})
    record('parity_candidate_all17_bound_to_release', all(current.get('candidate/' + name) == value for name, value in release_gate['binary_sha256_after'].items()) and len(release_gate['binary_sha256_after']) == 17)
    record('baseline23_engine_core_pinned', current['baseline_engine'] == protocol['baseline_engine_sha256'] == '85a3eeaf4c513e1790cb4c2593edb02063cba42d91eb7fc1bd303de026bd2b07' and current['baseline_core'] == protocol['baseline_core_sha256'] == '310ea85577ddd8a4b88479256dbe57fb576a384f24958d46324e82583dbd77c9')
    record('baseline23_nnue_object_pinned', paths.get('baseline_nnue_object') == Path(protocol['baseline_nnue_object']) and current['baseline_nnue_object'] == protocol['baseline_nnue_object_sha256'] == 'e8dfc576e6b42ffa4de5d4991d0f3ae7c3e9be7f5a818126c520dee386f6a967')
    record('candidate_nnue_object_exact_parent23', current['candidate/CMakeFiles/forge_core.dir/src/nnue.cpp.o'] == current['baseline_nnue_object'])
    public_names = {'include/forge/eval.hpp', 'src/eval.cpp', 'include/forge/board.hpp', 'src/board.cpp'}
    record('baseline_all4_public_pins', set(protocol['baseline_public_source_sha256']) == public_names and all(current['baseline_public/' + name] == protocol['baseline_public_source_sha256'][name] == parent_source[name] for name in public_names))
    candidate_public = {name: digest(SOURCE / name) for name in public_names}
    board_names = {'include/forge/board.hpp', 'src/board.cpp'}
    record('candidate_board_only_byte_equality', set(protocol['unchanged_board_source_sha256']) == board_names and {name: candidate_public[name] for name in board_names} == wrapper['candidate_board_source_sha256'] == protocol['unchanged_board_source_sha256'])
    record('candidate_evaluator_additions_hashed_not_rejected', candidate_public == wrapper['candidate_public_source_sha256'] and all(candidate_public[name] == context.get('source', {}).get(name) for name in public_names) and wrapper['candidate_evaluator_file_byte_equality_required'] is False)
    expected_steps = [('cold-warm-parity', [PYTHON, '-B', str(HERE / 'search-parity.py')], 1200)]
    record('exact_one_release_parity_step', [row['label'] for row in wrapper['steps']] == [row[0] for row in expected_steps])
    for row, (label, command, timeout) in zip(wrapper['steps'], expected_steps):
        saved = load(directory / (label + '-command.json'))
        record('parity_command_facts:' + label, {key: value for key, value in row.items() if key != 'label'} == saved and row['command'] == command and row['timeout_seconds'] == timeout and row['exit_code'] == 0 and row['error'] is None and row['timed_out'] is False and row['input_sha256_after'] == current and row['source_sha256_after'] == context.get('source') and row['baseline_source_sha256_after'] == parent_source)
        streams('parity:' + label, directory, row, '.bin')
        cleanup_fact('parity:' + label, row['cleanup'])
    freeze_path=HERE/'BENCH-SIGNATURE-FREEZE.json';freeze=load(freeze_path)
    record('separate_first_benchmark_frozen_before_parity', wrapper['bench_signature_freeze_sha256']==digest(freeze_path) and freeze['source_commit']==REV and freeze['nodes']==protocol['baseline_default_bench11_nodes']==292545 and protocol['default_bench11_expected_nodes'] is None)
    record('parity_after_first_signature_before_asan', datetime.datetime.fromisoformat(load(HERE/'release-signature-wrapper-attempt1/summary.json')['completed_utc']) <= datetime.datetime.fromisoformat(wrapper['started_utc']) <= datetime.datetime.fromisoformat(wrapper['completed_utc']) <= datetime.datetime.fromisoformat(context['asan']['started_utc']))
    record('parity_complete_bound_configuration', summary['status'] == 'passed' and summary['configuration'] == config and config['protocol'] == protocol and config['source_commit'] == REV and config['attempts'] == 1 and config['timing_comparison'] is False and config['engine_sha256_before'] == summary['engine_sha256_after'] == {'baseline': current['baseline_engine'], 'candidate': current['candidate/forge']} and config['driver_sha256'] == current['parity_driver'] and config['trusted_driver_sha256'] == current['trusted_driver'])
    record('parity_oracle_version', config['python_chess_version'] == chess.__version__, oracle_version=chess.__version__)
    raw_events = (output / 'events.jsonl').read_bytes()
    events = [json.loads(line) for line in raw_events.splitlines()]
    record('parity_event_sequence_and_hash', sha(raw_events) == summary['events_sha256'] and [row['sequence'] for row in events] == list(range(1, len(events) + 1)))
    record('parity_no_error_kill_events', not any(row['kind'] in ['reader_error', 'forced_kill', 'hard_session_deadline_expired'] for row in events))
    sessions = summary['sessions']
    expected_order = [(mode, case['name'], label) for mode in ['default', 'disabled'] for case in cases for label in ['baseline', 'candidate']]
    record('exact28_sessions_no_replacements', len(sessions) == 28 and [(row['nnue_mode'], row['case'], row['engine_label']) for row in sessions] == expected_order and [row['index'] for row in sessions] == list(range(28)))
    info_re = re.compile(r'^info depth (?P<depth>\d+) seldepth (?P<seldepth>\d+) score (?P<kind>cp|mate) (?P<score>-?\d+)(?: (?P<bound>lowerbound|upperbound))? nodes (?P<nodes>\d+) nps (?P<nps>\d+) hashfull (?P<hashfull>\d+) time (?P<time>\d+) pv(?: (?P<pv>.*))?$')
    best_re = re.compile(r'^bestmove (?P<best>[a-h][1-8][a-h][1-8][qrbn]?)(?: ponder (?P<ponder>[a-h][1-8][a-h][1-8][qrbn]?))?$')
    volatile = re.compile(r'\b(time|nps)\s+\d+\b')
    data = {}
    search_count, info_rows = 0, 0
    def legal_sequence(board, moves):
        position = board.copy()
        for text in moves:
            move = chess.Move.from_uci(text)
            if move not in position.legal_moves:
                return False
            position.push(move)
        return True
    all_output_logs = []
    for session in sessions:
        index = session['index']
        process = output / ('process-' + str(index).zfill(2))
        result = load(process / 'result.json')
        prefix = str(index) + ':' + session['engine_label'] + ':' + session['nnue_mode'] + ':' + session['case']
        record('parity_complete_session:' + prefix, result == session and result['completed'] is True and result['exit_code'] == 0 and result['signal'] is None and result['capture_complete'] is True and result['reader_threads_joined'] is True and result['stream_hashes_final'] is True and result['reader_errors'] == [] and result['sanitizer_classification'] == 'none' and all(item in ['sent stop', 'sent quit'] for item in result['cleanup']))
        expected_engine = protocol['engines'][session['engine_label']]
        record('parity_actual_process_engine:' + prefix, result['argv'] == [expected_engine] and result['cwd'] == str(Path(expected_engine).parent))
        process_events = [row for row in events if row.get('process') == index]
        raw = {}
        for stream in ['stdin', 'stdout', 'stderr']:
            raw[stream] = (process / (stream + '.bin')).read_bytes()
            decoded = b''.join(base64.b64decode(row['base64'], validate=True) for row in process_events if row['kind'] == 'bytes' and row['stream'] == stream)
            record('parity_raw_bytes_reconstructed:' + prefix + ':' + stream, raw[stream] == decoded and sha(raw[stream]) == result['stream_sha256'][stream])
        commands = [row['text'] for row in process_events if row['kind'] == 'command']
        record('parity_command_bytes:' + prefix, raw['stdin'] == ''.join(command + '\n' for command in commands).encode('ascii'))
        record('parity_stream_eofs:' + prefix, {row['stream'] for row in process_events if row['kind'] == 'eof'} == {'stdout', 'stderr'} and [row['exit_code'] for row in process_events if row['kind'] == 'exit'] == [0])
        consumed_lines = [row['text'] for row in process_events if row['kind'] == 'line']
        stdout_lines = raw['stdout'].split(b'\n')
        if stdout_lines and stdout_lines[-1] == b'':
            stdout_lines.pop()
        decoded_lines = [line.rstrip(b'\r').decode('utf-8', errors='replace') for line in stdout_lines]
        record('parity_every_emitted_stdout_line_consumed:' + prefix, decoded_lines == consumed_lines)
        case = next(row for row in cases if row['name'] == session['case'])
        record('parity_exact_two_search_requests:' + prefix, [command for command in commands if command.startswith('go ')] == ['go depth ' + str(case['depth'])] * 2 and len(re.findall(rb'(?m)^bestmove ', raw['stdout'])) == 2)
        record('parity_modes_threads_hash_book:' + prefix, 'option name UseNNUE type check default true' in result['identification'] and 'setoption name OwnBook value false' in commands and 'setoption name Ponder value false' in commands and 'setoption name Threads value 1' in commands and 'setoption name Hash value 32' in commands and [command for command in commands if command.startswith('setoption name UseNNUE ')] == (['setoption name UseNNUE value false'] if session['nnue_mode'] == 'disabled' else []))
        searches = result['searches']
        record('parity_cold_warm_pair_present:' + prefix, len(searches) == 2 and [row['state'] for row in searches] == ['cold', 'warm'])
        start_events = [row for row in process_events if row['kind'] == 'search_start']
        record('parity_single_newgame_before_cold:' + prefix, commands.count('ucinewgame') == 1 and any(row['kind'] == 'command' and row['text'] == 'ucinewgame' and row['sequence'] < start_events[0]['sequence'] for row in process_events))
        between = [row['text'] for row in process_events if row['kind'] == 'command' and start_events[0]['sequence'] < row['sequence'] < start_events[1]['sequence']]
        record('parity_warm_state_preserved:' + prefix, not any(command == 'ucinewgame' or command == 'setoption name Clear Hash' or command.startswith(('setoption name Hash ', 'setoption name Threads ', 'setoption name UseNNUE ')) for command in between))
        normalized_pair = []
        for search in searches:
            search_count += 1
            label = prefix + ':' + search['state']
            board = chess.Board() if case['position'] == 'startpos' else chess.Board(case['position'].removeprefix('fen '))
            record('parity_search_identity:' + label, search['completed'] is True and search['label'] == case['name'] + '/' + search['state'] and search['position'] == case['position'] and search['depth_limit'] == case['depth'])
            rows = search['raw_lines']
            parsed = []
            for number, line in enumerate(rows[:-1]):
                match = info_re.fullmatch(line)
                record('parity_info_grammar:' + label + ':' + str(number), match is not None)
                if match is None:
                    continue
                fact = match.groupdict()
                for key in ['depth', 'seldepth', 'score', 'nodes', 'nps', 'hashfull', 'time']:
                    fact[key] = int(fact[key])
                fact['pv'] = (fact['pv'] or '').split()
                record('parity_info_logical_values:' + label + ':' + str(number), fact['nodes'] > 0 and 0 <= fact['hashfull'] <= 1000 and bool(fact['pv']) and legal_sequence(board, fact['pv']))
                parsed.append(fact)
                info_rows += 1
            record('parity_all_structured_fields_reparsed:' + label, parsed == search['structured_info'] and bool(parsed))
            best = best_re.fullmatch(rows[-1])
            record('parity_bestmove_grammar:' + label, best is not None)
            if best is not None and parsed:
                move_sequence = [best['best']] + ([best['ponder']] if best['ponder'] else [])
                record('parity_bestmove_ponder_legal:' + label, legal_sequence(board, move_sequence) and best['best'] == search['bestmove'] and best['ponder'] == search['ponder'] and parsed[-1]['pv'][0] == best['best'])
                record('parity_requested_depth_or_early_mate:' + label, 1 <= parsed[-1]['depth'] <= case['depth'] and (parsed[-1]['depth'] == case['depth'] or parsed[-1]['kind'] == 'mate'))
            normalized = [volatile.sub(lambda match: match[1] + ' <excluded>', row) for row in rows]
            record('parity_only_time_nps_excluded:' + label, normalized == search['normalized_lines'])
            normalized_pair.append(normalized)
            purpose = search['label'] + ': bestmove'
            event_rows = [row['text'] for row in process_events if row['kind'] == 'line' and row.get('purpose') == purpose]
            captured = [row for row in process_events if row['kind'] == 'search_output_captured' and row['label'] == search['label']]
            completed = [row for row in process_events if row['kind'] == 'search_complete' and row['label'] == search['label']]
            record('parity_search_rows_match_events:' + label, event_rows == rows and len(captured) == 1 and captured[0]['raw_lines'] == rows and len(completed) == 1 and all(completed[0][key] == value for key, value in search.items()))
        data[(session['nnue_mode'], session['case'], session['engine_label'])] = normalized_pair
        all_output_logs.extend([process / 'stdout.bin', process / 'stderr.bin'])
    comparisons = []
    for mode in ['default', 'disabled']:
        for case in cases:
            baseline = data[(mode, case['name'], 'baseline')]
            candidate = data[(mode, case['name'], 'candidate')]
            comparison = {'nnue_mode': mode, 'case': case['name'], 'cold_exact': baseline[0] == candidate[0], 'warm_exact': baseline[1] == candidate[1], 'excluded_fields': ['time', 'nps']}
            comparisons.append(comparison)
            record('all_rows_baseline_candidate_exact:' + mode + ':' + case['name'], comparison['cold_exact'] and comparison['warm_exact'])
    record('exact14_comparison_receipts', comparisons == summary['comparisons'] == wrapper['parity_comparisons'] and len(comparisons) == 14 and search_count == 56)
    diagnostics = scan_logs('parity_all_stdout_stderr', [directory / 'cold-warm-parity.stdout.bin', directory / 'cold-warm-parity.stderr.bin', *all_output_logs])
    return {'sessions': len(sessions), 'depth_searches': search_count, 'comparison_pairs': len(comparisons), 'structured_info_rows': info_rows, 'all_logical_rows_exact': all(row['cold_exact'] and row['warm_exact'] for row in comparisons), 'separately_observed_default_bench11_nodes': freeze['nodes'], 'oracle': 'python-chess ' + chess.__version__, 'baseline_public_files_pinned': 4, 'candidate_byte_equal_board_files': 2, 'candidate_evaluator_byte_equality_required': False, 'parent_red_performed': False, 'diagnostics': diagnostics}


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
    record('active_exact_wrapper_command', wrapper['command'] == [PYTHON, '-B', str(HERE / 'active-uci-edges.py'), '--engine', str(BASE / 'see-proof-reuse-native-tsan/forge'), '--output', str(directory), '--session-timeout', '90'] and wrapper['cwd'] == str(ROOT) and wrapper['timeout_seconds'] == 120 and config['engine'] == str(BASE / 'see-proof-reuse-native-tsan/forge') and config['session_timeout_seconds'] == 90)
    inputs = {'engine': BASE / 'see-proof-reuse-native-tsan/forge', 'core': BASE / 'see-proof-reuse-native-tsan/libforge_core.a', 'runtime_psqt_test_object': BASE / 'see-proof-reuse-native-tsan/CMakeFiles/forge_runtime_psqt_tests.dir/tests/runtime_psqt_tests.cpp.o', 'runtime_psqt_test_executable': BASE / 'see-proof-reuse-native-tsan/forge_runtime_psqt_tests', 'pawn_span_test_object': BASE / 'see-proof-reuse-native-tsan/CMakeFiles/forge_pawn_span_tests.dir/tests/pawn_span_tests.cpp.o', 'pawn_span_test_executable': BASE / 'see-proof-reuse-native-tsan/forge_pawn_span_tests', 'nnue_object': BASE / 'see-proof-reuse-native-tsan/CMakeFiles/forge_core.dir/src/nnue.cpp.o', 'nearest_pawn_test_object': BASE / 'see-proof-reuse-native-tsan/CMakeFiles/forge_nearest_pawn_tests.dir/tests/nearest_pawn_tests.cpp.o', 'nearest_pawn_test_executable': BASE / 'see-proof-reuse-native-tsan/forge_nearest_pawn_tests', 'pv_metadata_test_object': BASE / 'see-proof-reuse-native-tsan/CMakeFiles/forge_pv_metadata_tests.dir/tests/pv_metadata_tests.cpp.o', 'pv_metadata_test_executable': BASE / 'see-proof-reuse-native-tsan/forge_pv_metadata_tests', 'active_driver': HERE / 'active-uci-edges.py', 'trusted_driver': HERE / 'trusted-run-full-engine-tt.py'}
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
    expected_roots = {'source': str(SOURCE), **{profile: str(BASE / ('see-proof-reuse-native-' + profile)) for profile in ['release', 'asan', 'tsan']}}
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
    parser.add_argument('--require-active', action='store_true', default=True, help='Frozen24 final audit always requires the eight active-TSan searches')
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
    if clear.get('exact_search_parity_required') is not True or clear.get('expected_cold_warm_searches') != 56 or clear.get('expected_pv_metadata_assertions') != 56:
        raise SystemExit('Explicit frozen24 exact56search/PV56 root protocol required; no audit attempted')
    if type(clear.get('expected_tt_groups')) is not int or clear['expected_tt_groups'] <= 0:
        raise SystemExit('Root-frozen actual TT group count required; no audit attempted')
    if not isinstance(clear.get('expected_tt_test_source_sha256'), str) or re.fullmatch(r'[0-9a-f]{64}', clear['expected_tt_test_source_sha256']) is None:
        raise SystemExit('Root-frozen TT regression source SHA required; no audit attempted')
    if not isinstance(clear.get('expected_tt_group_success_line'), str) or not clear['expected_tt_group_success_line'] or '\n' in clear['expected_tt_group_success_line'] or '\r' in clear['expected_tt_group_success_line']:
        raise SystemExit('Root-frozen exact TT group success line required; no audit attempted')
    if clear.get('expected_bench11_nodes', 'missing') is not None or clear.get('benchmark_signature_mode') != 'FIRST_CAPTURE_EXCLUSIVE_FREEZE':
        raise SystemExit('First actual benchmark capture/freeze mode required; no audit attempted')
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
        stage('release_parity', release_parity)
        stage('active_uci', lambda: optional_active(args.require_active))
        stage('whole_originals', whole_originals)
        stage('process_groups', no_live_groups)
        profile_records = [context.get(name) for name in ['release', 'asan', 'tsan']]
        if all(profile_records):
            record('three_profiles_executed_serially', all(datetime.datetime.fromisoformat(profile_records[i]['completed_utc']) <= datetime.datetime.fromisoformat(profile_records[i + 1]['started_utc']) for i in [0, 1]))
        failed = [row for row in checks if not row['passed']]
        report = {'status': 'passed' if not failed else 'failed', 'audited_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'source_commit': REV, 'parent_source_commit': PARENT_REV, 'check_count': len(checks), 'failed_check_count': len(failed), 'checks': checks, 'facts': facts, 'facts_stream': paths[2].name, 'facts_stream_sha256': digest(paths[2]), 'checker_sha256': digest(Path(__file__)), 'engine_compiler_or_test_execution_during_audit': False, 'original_evidence_mutated': False, 'qualified_driver_limitations': ['The1200-second profile timeout applies per recorded command.', 'One first-captured benchmark is frozen before comparison with parent23;56exact cold/warm dual-NNUE searches are mandatory.', 'Finite fixtures and TSan coverage do not establish universal correctness or playing strength.'], 'scope': 'Pure SEE proof reuse optimization: root-pinned77source/14CTest each profile, TT12/PV56, exact56cold/warm parity including NNUEdisabled, firstactual benchmark comparedaftercapture to parent23 and8active defaultTSan. No timing/Elo claim.'}
        with paths[0].open('x') as stream:
            json.dump(report, stream, indent=2, allow_nan=False); stream.write('\n')
        details = 'All independent checks passed.' if not failed else 'Failed checks: ' + ', '.join(row['name'] for row in failed)
        text = f"""SEE proof reuse independent evidence audit: {report['status']}.

{details} Check count: {len(checks)}. Every check/stage fact was flushed before
the final gate. No engines, compilers or tests ran and no originals were changed.

Exact77source/Git/root gates;14CTest per profile42total, PV56/TT12 and preserved
other finite tests; fatal default TSan, strict flags, cleanup and17artifact identity.
Parent23 full77source and NNUEobject identity; only root-declared CMake/UCI/search/core-test changes.
One first actual candidate benchmark is frozen before comparing with parent292545.
All56cold/warm searches across7cases and default/disabledNNUE must match every
logical info/PV/bestmove field, excluding onlytime/NPS. Eight activeTSan transitions required.
This pure-optimization qualification differs from23's intentional TTpolicy trial.
Finite coverage does not prove universal correctness, speed or Elo.
"""
        with paths[1].open('x') as stream:
            stream.write(text)
    print(json.dumps({'status': report['status'], 'check_count': len(checks), 'failed_check_count': len(failed), 'facts': {name: value for name, value in facts.items() if name in ['release_signature', 'active_uci']}}, indent=2))
    return 0 if not failed else 1


if __name__ == '__main__':
    raise SystemExit(main())

