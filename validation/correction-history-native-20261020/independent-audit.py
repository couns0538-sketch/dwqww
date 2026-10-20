#!/usr/bin/env python3
"""Audit saved correction-history evidence; never run engines, compilers or tests.

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
import subprocess
import tarfile

ROOT = Path('/workspace/dwqww')
HERE = ROOT / 'validation/correction-history-native-20261020'
SOURCE = Path('/workspace/.cloud-setup/correction-history-native-source')
REV = 'fc51e43c26f735cbc1ffabf0fcf64f48a4592c0b'
PARENT_REV = '47f0560221d986e41a309853e1295c557fcf5bf6'
BASE = Path('/workspace/.cloud-setup')
CMAKE = '/workspace/.cloud-setup/venv/bin/cmake'
CTEST = '/workspace/.cloud-setup/venv/bin/ctest'
PYTHON = '/workspace/.cloud-setup/venv/bin/python'
CXX = '/usr/bin/g++-14'
BINARY_NAMES = ['forge', 'forge_tests', 'forge_tt_tests', 'forge_rule50_tests',
                'forge_legal_witness_tests', 'forge_correction_history_tests', 'forge_bench', 'libforge_core.a']
FLAGS = ['-march=x86-64-v3', '-mtune=znver5', '-fno-fast-math', '-ffp-contract=off', '-fno-lto']
TEST_NAMES = ['forge_tests', 'forge_correction_history_tests', 'forge_tt_tests', 'forge_rule50_tests',
              'forge_legal_witness_tests', 'match_tool_tests', 'windows_validation_tests',
              'uci_regression', 'ponder_regression', 'ownbook_regression']
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
    data = git('archive', REV, 'CMakeLists.txt', 'LICENSE', 'src', 'include', 'tests', 'bench', 'tools')
    expected = {}
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        for item in archive.getmembers():
            if item.isfile():
                expected[item.name] = sha(archive.extractfile(item).read())
    actual = {p.relative_to(SOURCE).as_posix(): digest(p) for p in SOURCE.rglob('*') if p.is_file()}
    record('exact_frozen_source_git_tar', (HERE / 'frozen-source-fc51e43.tar').read_bytes() == data)
    record('exact73_source_git_export_manifest', len(expected) == 73 and expected == actual == load(HERE / 'frozen-source-fc51e43-files.json'))
    context['source'] = expected
    static = load(HERE / 'STATIC-SOURCE-GATES.json')
    record('static_source_gate_identity', static['source_commit'] == REV and static['source_sha256'] == expected)
    record('static_correction_contract_identity', static['permanent_test_expected_checks'] == 54 and static['full_ctest_expected_count'] == 10 and static['permanent_test_sha256'] == expected['tests/correction_history_tests.cpp'])
    record('gcc14_record', '14.2.0' in static['compiler_version'])
    provenance = load(HERE / 'DRIVER-PROVENANCE.json')
    record('original_profile_driver_unchanged', digest(HERE / 'run-frozen-validation.py') == provenance['driver_sha256'])
    extras = load(HERE / 'EXTRAS-DRIVER-PROVENANCE.json')
    for name, value in extras['scripts'].items():
        record('original_extras_driver_unchanged:' + name, digest(HERE / name) == value)
    source_text = '\n'.join((SOURCE / name).read_text() for name in expected if name.startswith(('src/', 'include/')) and name.endswith(('.cpp', '.hpp')))
    record('no_source_tsan_suppression_hooks', re.search(r'__tsan_default_suppressions|no_sanitize_thread|no_sanitize\s*\(\s*"thread"', source_text) is None)
    return {'source_commit': REV, 'source_files': len(expected), 'source_tar_sha256': sha(data), 'compiler_record': static['compiler_version'].splitlines()[0]}


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
    result.update(match_tool_tests=[PYTHON, str(SOURCE / 'tools/match/test_match_tools.py')],
                  windows_validation_tests=[PYTHON, str(SOURCE / 'tools/match/tests/test_windows_validate.py')],
                  uci_regression=[PYTHON, str(SOURCE / 'tools/uci_regression.py'), str(build / 'forge'), '--log', str(build / 'uci-regression.log')],
                  ponder_regression=[PYTHON, str(SOURCE / 'tools/ponder_regression.py'), str(build / 'forge')],
                  ownbook_regression=[PYTHON, str(SOURCE / 'tools/ownbook_regression.py'), str(build / 'forge'), str(build / 'ownbook-regression.json')])
    return result


def audit_profile(profile):
    directory = HERE / ('frozen-' + profile + '-attempt1')
    build = BASE / ('correction-history-native-' + profile)
    summary = load(directory / 'summary.json')
    record('profile_pass:' + profile, summary['status'] == 'PASS' and summary['source_commit'] == REV, observed_status=summary['status'])
    record('profile_tar_identity:' + profile, summary['source_archive_sha256'] == digest(HERE / 'frozen-source-fc51e43.tar'))
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
    record('exact10_discovered_names:' + profile, len(discovered) == 10 and [row['name'] for row in discovered] == TEST_NAMES and summary['ctest_names'] == TEST_NAMES)
    expected = expected_tests(build)
    record('exact10_discovered_commands:' + profile, all(row['command'] == expected.get(row['name']) for row in discovered))
    text = (directory / 'ctest.stdout').read_text()
    record('original_ctest10_passes:' + profile, '100% tests passed, 0 tests failed out of 10' in text and len(re.findall(r'Test\s+#\d+:.*Passed', text)) == 10)
    last_path = directory / 'original-LastTest.log'
    last = last_path.read_text()
    record('actual10_lasttest_passes:' + profile, last.count('Test Passed.') == 10)
    block = re.search(r'\n\d+/10 Testing: forge_correction_history_tests\n(.*?)(?=\n\d+/10 Testing:|\Z)', last, re.S)
    correction = block[1] if block else ''
    record('actual54_correction_checks:' + profile, re.findall(r'^SUMMARY checks=(\d+) failures=(\d+)\s*$', correction, re.M) == [('54', '0')] and len(re.findall(r'^PASS ', correction, re.M)) == 54 and not re.search(r'^FAIL ', correction, re.M))
    for name in ['ownbook-regression.json', 'Testing/Temporary/LastTest.log', 'Testing/Temporary/CTestCostData.txt', 'uci-regression.log', 'CMakeCache.txt', 'compile_commands.json']:
        record('original_copy_exact:' + profile + ':' + name, (build / name).read_bytes() == (directory / ('original-' + Path(name).name)).read_bytes())
    before = summary['binary_sha256_before']
    current = {name: digest(build / name) for name in BINARY_NAMES}
    record('all8_binary_core_identities:' + profile, set(before) == set(BINARY_NAMES) and before == summary['binary_sha256_after_tests'] == summary['binary_sha256_after'] == current)
    record('source_test_identities:' + profile, summary['source_sha256_before_tests'] == summary['source_sha256_after_tests'] == context.get('source') and summary['test_source_sha256_before_tests'] == summary['test_source_sha256_after_tests'] == {name: value for name, value in context.get('source', {}).items() if name.startswith('tests/')} and summary['source_files_unchanged'] is True)
    cache = (directory / 'original-CMakeCache.txt').read_text()
    record('native_off_cache:' + profile, 'FORGE_NATIVE:BOOL=OFF' in cache and re.search(r'^CMAKE_CXX_COMPILER:(?:STRING|FILEPATH)=' + re.escape(CXX) + r'$', cache, re.M) is not None)
    compilation = load(directory / 'original-compile_commands.json')
    record('full14_compilation_records:' + profile, len(compilation) == 14)
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
    return {'profile': profile, 'recorded_status': summary['status'], 'ctest_passes': 10, 'correction_checks': 54, 'binaries': current, 'diagnostics': diagnostics, 'started_utc': summary['started_utc'], 'completed_utc': summary['completed_utc']}


def release_extras():
    directory = HERE / 'release-extras-attempt1'
    build = BASE / 'correction-history-native-release'
    summary = load(directory / 'summary.json')
    record('release_extras_pass', summary['status'] == 'PASS' and summary['source_commit'] == REV)
    current = {name: digest(Path(path)) for name, path in summary['input_paths'].items()}
    record('extras_inputs_unchanged', current == summary['input_sha256_before'] == summary['input_sha256_after'])
    record('frozen_parent_core_hash', current['parent_core'] == 'd772f89980edb0e9f7fd5da99ef5c7bdb402aa8319082907b2bf31180359bd12')
    record('extras_sources_unchanged', summary['source_sha256_before'] == summary['source_sha256_after'] == context.get('source'))
    red = BASE / 'correction-history-native-parent-red'
    obj = build / 'CMakeFiles/forge_correction_history_tests.dir/tests/correction_history_tests.cpp.o'
    parent_core = BASE / 'forge-promotion-release/libforge_core.a'
    expected_commands = [
        ('link-parent-red', [CXX, *FLAGS, '-O3', '-DNDEBUG', str(obj), str(parent_core), '-pthread', '-o', str(red)], 0),
        ('parent-contract-red', [str(red)], 1), ('bench11', [str(build / 'forge')], 0)]
    record('exact_three_extras_steps', [row['label'] for row in summary['steps']] == [row[0] for row in expected_commands])
    for step, (label, command, code) in zip(summary['steps'], expected_commands):
        record('exact_extras_command:' + label, step == load(directory / (label + '-command.json')) and step['command'] == command and step['expected_exit_code'] == step['exit_code'] == code and step['error'] is None and step['timed_out'] is False)
        cleanup_fact('extras:' + label, step['cleanup'])
        streams('extras:' + label, directory, step, '.bin')
        record('extras_input_snapshot:' + label, step['input_sha256_after'] == current and step['source_sha256_after'] == context.get('source'))
    red_hash = digest(red)
    record('parent_red_executable_unchanged', red_hash == summary['parent_red_executable_sha256_before'] == summary['parent_red_executable_sha256_after'] == summary['parent_red_executable_sha256_final'])
    text = (directory / 'parent-contract-red.stdout.bin').read_text()
    red_summary = re.findall(r'^SUMMARY checks=(\d+) failures=(\d+)\s*$', text, re.M)
    fail_lines = re.findall(r'^FAIL .+$', text, re.M)
    record('same_object_parent_expected17_of54_red', red_summary == [('54', '17')] and len(fail_lines) == 17 and len(re.findall(r'^PASS ', text, re.M)) == 37 and fail_lines == summary['parent_contract_actual_fail_lines'] and summary['parent_contract_actual_summaries'] == [['54', '17']])
    abi = load(directory / 'ABI-PROVENANCE.json')
    parent_headers = git('ls-tree', '-r', '--format=%(path) %(objectname)', PARENT_REV, 'include').decode()
    candidate_headers = git('ls-tree', '-r', '--format=%(path) %(objectname)', REV, 'include').decode()
    record('exact_abi_headers', parent_headers == candidate_headers == abi['parent_headers_tree'] == abi['candidate_headers_tree'] and abi['headers_identical'] is True)
    record('same_object_no_parent_recompile', abi['test_object_recompiled_for_parent'] is False and abi['parent_core_rebuilt'] is False and abi['compiler'] == CXX and abi['flags'] == FLAGS + ['-O3', '-DNDEBUG'])
    candidate_link = (build / 'CMakeFiles/forge_correction_history_tests.dir/link.txt').read_text()
    parent_link = (BASE / 'forge-promotion-release/CMakeFiles/forge_tests.dir/link.txt').read_text()
    record('original_abi_link_records', candidate_link == abi['candidate_original_link_command'] and parent_link == abi['parent_original_link_command'] and 'CMakeFiles/forge_correction_history_tests.dir/tests/correction_history_tests.cpp.o' in candidate_link)
    stdin = (directory / 'bench11.stdin.bin').read_bytes()
    raw = (directory / 'bench11.stdout.bin').read_bytes()
    signature = [int(value) for value in re.findall(rb'^info string bench depth 11 nodes (\d+) time \d+ nps \d+\s*$', raw, re.M)]
    record('one_raw_bench_actual_positive', stdin == b'bench 11\nquit\n' and len(signature) == 1 and signature[0] > 0 and signature == summary['actual_bench11_signatures'], observed_nodes=signature, expectation_policy='Observed candidate value only; no older/native-parity expectation')
    record('bench_controller_did_not_impose_node_count', 'assert len(sig)==1 and int(sig[0])>0' in (HERE / 'run-release-extras.py').read_text())
    return {'parent_checks': 54, 'parent_failures_under_new_contract': 17, 'candidate_checks': 54, 'candidate_failures': 0, 'candidate_object_sha256': current['candidate_test_object'], 'parent_core_sha256': current['parent_core'], 'parent_red_sha256': red_hash, 'actual_release_bench11_nodes': signature, 'behavior_scope': 'New residual-increment contract; parent RED does not establish an old correctness bug.', 'speed_or_strength_claim': False}


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
    record('active_exact_wrapper_command', wrapper['command'] == [PYTHON, '-B', str(HERE / 'active-uci-edges.py'), '--engine', str(BASE / 'correction-history-native-tsan/forge'), '--output', str(directory), '--session-timeout', '90'] and wrapper['cwd'] == str(ROOT) and wrapper['timeout_seconds'] == 120 and config['engine'] == str(BASE / 'correction-history-native-tsan/forge') and config['session_timeout_seconds'] == 90)
    inputs = {'engine': BASE / 'correction-history-native-tsan/forge', 'core': BASE / 'correction-history-native-tsan/libforge_core.a', 'test_object': BASE / 'correction-history-native-tsan/CMakeFiles/forge_correction_history_tests.dir/tests/correction_history_tests.cpp.o', 'active_driver': HERE / 'active-uci-edges.py', 'trusted_driver': HERE / 'trusted-run-full-engine-tt.py'}
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
    record('whole_originals_snapshot_source', snapshot['source_commit'] == REV and snapshot['engines_or_builds_executed_for_this_snapshot'] is False)
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
            record('whole_originals_file:' + label + ':' + name, okay)
    record('whole_originals_tree_counts', counts == {'source': 73, 'release': 137, 'asan': 137, 'tsan': 137}, observed=counts)
    for label, item in snapshot['single_files'].items():
        target = Path(item['path'])
        record('whole_originals_single:' + label, digest(target) == item['sha256'] and target.stat().st_size == item['bytes'])
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
    global fact_stream
    parser = argparse.ArgumentParser()
    parser.add_argument('--require-active', action='store_true')
    args = parser.parse_args()
    paths = [HERE / ('independent-audit' + suffix) for suffix in ['.json', '.md', '-facts.jsonl']]
    if any(path.exists() for path in paths):
        raise SystemExit('Refusing to overwrite a previous audit attempt')
    with paths[2].open('x') as fact_stream:
        stage('frozen_source', frozen_source)
        for profile in ['release', 'asan', 'tsan']:
            stage(profile, lambda profile=profile: audit_profile(profile))
        stage('release_extras', release_extras)
        stage('active_uci', lambda: optional_active(args.require_active))
        stage('whole_originals', whole_originals)
        stage('process_groups', no_live_groups)
        profile_records = [context.get(name) for name in ['release', 'asan', 'tsan']]
        if all(profile_records):
            record('three_profiles_executed_serially', all(datetime.datetime.fromisoformat(profile_records[i]['completed_utc']) <= datetime.datetime.fromisoformat(profile_records[i + 1]['started_utc']) for i in [0, 1]))
        failed = [row for row in checks if not row['passed']]
        report = {'status': 'passed' if not failed else 'failed', 'audited_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'source_commit': REV, 'parent_source_commit': PARENT_REV, 'check_count': len(checks), 'failed_check_count': len(failed), 'checks': checks, 'facts': facts, 'facts_stream': paths[2].name, 'facts_stream_sha256': digest(paths[2]), 'checker_sha256': digest(Path(__file__)), 'engine_compiler_or_test_execution_during_audit': False, 'original_evidence_mutated': False, 'qualified_driver_limitations': ['Original driver discovery gate checked ten-count plus correction-test presence; this audit checks the exact ten names and commands independently.', 'Original driver did not explicitly scan sanitizer logs; this audit scans original CTest/UCI/OwnBook and optional active logs independently.', 'The 1200-second outer timeout applies to each recorded command, not the whole profile.'], 'scope': 'Unaccepted residual-increment strength ablation with bounded validation of the selected behavior contract. Parent contract RED does not prove an old correctness defect; benchmark nodes do not establish speed or Elo.'}
        with paths[0].open('x') as stream:
            json.dump(report, stream, indent=2, allow_nan=False); stream.write('\n')
        details = 'All independent checks passed.' if not failed else 'Failed checks: ' + ', '.join(row['name'] for row in failed)
        text = f"""Correction-history independent evidence audit: {report['status']}.

{details} Check count: {len(checks)}. Every check and stage fact was flushed to
{paths[2].name} before this final gate. No engines, compilers or tests ran and
no original source/evidence was changed.

The audit compares source TAR/export73 with Git, exact ten CTest names/commands,
actual54-check correction logs, original stream hashes, strict compiler/sanitizer
settings, cleanup facts and unchanged source/eight-binary identities. It also
checks the same-object parent17/54 RED with ABI/hash records and one raw positive
observed Release bench signature. Optional active UCI evidence, when present,
is checked for eight positive-node transitions, saved-move legality, exact raw
byte/event reconstruction, default TSan facts and orderly completion.

Original-driver limitations remain explicit: discovery asserted only ten-count
plus correction-test presence; no explicit sanitizer log scan preceded its
PASS; timeout1200 applies per command. Independent checks cover the first two
omissions without rerunning engines. This is an unaccepted strength ablation;
parent RED does not establish an old correctness bug, and benchmark nodes do
not establish speed, NPS, Elo, Windows or physical-Ryzen performance.
"""
        with paths[1].open('x') as stream:
            stream.write(text)
    print(json.dumps({'status': report['status'], 'check_count': len(checks), 'failed_check_count': len(failed), 'facts': {name: value for name, value in facts.items() if name in ['release_extras', 'active_uci']}}, indent=2))
    return 0 if not failed else 1


if __name__ == '__main__':
    raise SystemExit(main())
