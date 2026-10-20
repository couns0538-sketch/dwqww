#!/usr/bin/env python3
"""Read-only accepted-lineage OwnBook evidence audit; executes only Git reads."""
from pathlib import Path
import datetime
import hashlib
import json
import re
import shlex
import stat
import struct
import subprocess

ROOT = Path('/workspace/dwqww')
HERE = ROOT / 'validation/accepted-ownbook-integration-20261020'
BASE = Path('/workspace/.cloud-setup')
COMMITS = {'baseline': '356e863dbd86d2ce24b8ee9486d7406f1d525480',
           'candidate': '5101c2529d386b7c3a04ba9156a69ee34df6bb43'}
TEST = 'validation/hourly/2026-10-20-ownbook-native/test_ownbook.py'
TEST_SHA = '220648e27b1a45af593174321a093c0947b4599b3fe315048f0f4001529f8588'
TEST_NAMES = {'forge_tests', 'match_tool_tests', 'uci_regression', 'ponder_regression'}
STEP_NAMES = ['configure', 'build', 'ctest-discovery', 'ctest', 'ownbook']
BUILD_FILES = ['forge', 'forge_tests', 'forge_bench', 'libforge_core.a', 'CMakeCache.txt',
               'compile_commands.json', 'CTestTestfile.cmake']
DIAGNOSTIC = re.compile(r'AddressSanitizer|LeakSanitizer|runtime error:|UndefinedBehaviorSanitizer|SUMMARY:.*Sanitizer', re.I)
checks = []
sha = lambda data: hashlib.sha256(data).hexdigest()
load = lambda path: json.loads(path.read_text())


def check(name, condition):
    checks.append({'name': name, 'passed': bool(condition)})
    if not condition:
        raise AssertionError(name)


def git(*arguments):
    return subprocess.check_output(['git', *arguments], cwd=ROOT)


def file_identity(path):
    check('regular_file:' + str(path), path.is_file() and not path.is_symlink())
    return {'sha256': sha(path.read_bytes()), 'bytes': path.stat().st_size}


def source_snapshot(label):
    manifest = load(HERE / (label + '-source.json'))
    commit = COMMITS[label]
    root = BASE / ('accepted-ownbook-' + label + '-source')
    check('source_manifest_identity:' + label, manifest['commit'] == commit and manifest['root'] == str(root))
    check('source_tree_identity:' + label, manifest['tree'] == git('rev-parse', commit + '^{tree}').decode().strip())
    rows = git('ls-tree', '-r', commit, '--', *manifest['selectors']).decode().splitlines()
    tree = {}
    for row in rows:
        metadata, name = row.split('\t', 1)
        mode, kind, blob = metadata.split()
        check('source_git_blob_kind:' + label + ':' + name, kind == 'blob')
        tree[name] = (mode, blob)
    actual = {p.relative_to(root).as_posix(): p for p in root.rglob('*') if p.is_file()}
    check('complete_source_inventory:' + label, set(actual) == set(tree) == set(manifest['files']))
    identity = {}
    for name, path in actual.items():
        recorded = manifest['files'][name]
        identity[name] = file_identity(path)
        expected_bytes = git('show', commit + ':' + name)
        check('source_git_hash_size:' + label + ':' + name,
              identity[name] == {'sha256': sha(expected_bytes), 'bytes': len(expected_bytes)} ==
              {k: recorded[k] for k in ['sha256', 'bytes']})
        check('source_git_mode_blob:' + label + ':' + name,
              (recorded['git_mode'], recorded['git_blob']) == tree[name] and
              stat.S_IMODE(path.stat().st_mode) == (int(tree[name][0], 8) & 0o777))
    return identity


def source_record(name, record, label, expected):
    check(name, record['source_commit'] == COMMITS[label] and record['matches_frozen_source'] is True and record['sha256'] == expected)


def live_groups(group_ids):
    found = []
    for path in Path('/proc').iterdir():
        if not path.name.isdigit():
            continue
        try:
            raw = (path / 'stat').read_text()
            fields = raw[raw.rfind(')') + 2:].split()
            if int(fields[2]) in group_ids and fields[0] != 'Z':
                found.append({'pid': int(path.name), 'group_id': int(fields[2]), 'state': fields[0]})
        except (OSError, ValueError, IndexError):
            pass
    return found


def command_record(directory, label, expected_command, group_ids):
    record = load(directory / (label + '-command.json'))
    check('command_exact:' + str(directory.name) + ':' + label, record['label'] == label and record['command'] == expected_command)
    check('command_success:' + str(directory.name) + ':' + label,
          record['return_code'] == 0 and record['error'] is None and record['timed_out'] is False)
    check('command_cwd:' + str(directory.name) + ':' + label, record['cwd'] == str(ROOT))
    check('command_owned_cleanup:' + str(directory.name) + ':' + label,
          record['cleanup']['no_live_owned_processes'] is True and
          record['cleanup'].get('unexpected_live_members_after_command') is False and
          not any(p['state'] != 'Z' for p in record['cleanup']['after']))
    group_ids.add(record['cleanup']['group_id'])
    for stream in ['stdout', 'stderr']:
        check('command_stream_hash:' + str(directory.name) + ':' + label + ':' + stream,
              sha((directory / (label + '.' + stream)).read_bytes()) == record[stream + '_sha256'])
    check('command_time_order:' + str(directory.name) + ':' + label,
          datetime.datetime.fromisoformat(record['started_utc']) <= datetime.datetime.fromisoformat(record['completed_utc']))
    return record


def ownbook_segments(path, expected_leak):
    lines = path.read_text().splitlines()
    check('directional_transcript:' + str(path.parent.parent.name), all(line.startswith(('> ', '< ')) for line in lines))
    commands = [line[2:] for line in lines if line.startswith('> ')]
    check('ownbook_command_sequence:' + str(path.parent.parent.name),
          [c for c in commands if c.startswith('go ')] == ['go movetime 150', 'go movetime 150', 'go depth 2', 'go movetime 150'] and
          [c for c in commands if c.startswith('setoption name OwnBook')] ==
          ['setoption name OwnBook value false', 'setoption name OwnBook value true', 'setoption name OwnBook value false'])
    files = [c.removeprefix('setoption name Book File value ') for c in commands if c.startswith('setoption name Book File value ')]
    check('ownbook_fixture_loaded:' + str(path.parent.parent.name), len(files) == 1 and files[0].endswith('/book with spaces.bin') and
          '< info string loaded book ' + files[0] + ' with 1 entries' in lines)
    segments = []
    for index, line in enumerate(lines):
        if not line.startswith('> go '):
            continue
        following = []
        for item in lines[index + 1:]:
            if item.startswith('> '):
                break
            following.append(item.removeprefix('< '))
        best = [item for item in following if item.startswith('bestmove ')]
        check('one_bestmove_segment:' + str(path.parent.parent.name) + ':' + str(len(segments)), len(best) == 1)
        move = best[0].split()[1]
        check('move_syntax_segment:' + str(path.parent.parent.name) + ':' + str(len(segments)), re.fullmatch(r'[a-h][1-8][a-h][1-8][qrbn]?', move) is not None)
        segments.append({'command': line[2:], 'book': any(item.startswith('info string book move ') for item in following), 'move': move})
    check('book_toggle_depth_segments:' + str(path.parent.parent.name),
          [row['book'] for row in segments] == [expected_leak, True, False, expected_leak])
    check('enabled_book_e2e4:' + str(path.parent.parent.name), segments[1]['move'] == 'e2e4')
    return segments


def main():
    summary = load(HERE / 'SUMMARY.json')
    check('all_profile_summary_pass', summary['status'] == 'PASS_ALL_LOCAL_ACCEPTED_LINEAGE_GATES' and summary['integration_performed'] is False and summary['no_retries'] is True)
    protocol = load(HERE / 'PROTOCOL.json')
    check('protocol_exact_lineage', protocol['commits'] == COMMITS)
    check('protocol_bounded_serial_no_retry', protocol['jobs'] == 2 and protocol['phases_serial'] is True and protocol['phase_timeout_seconds'] == 1200 and protocol['no_retries'] is True and protocol['forge_native'] is False)
    for tool in ['gcc', 'cmake', 'python']:
        check('frozen_tool_hash:' + tool, sha(Path(protocol[tool + '_path']).read_bytes()) == protocol[tool + '_sha256'])
    check('gcc14_version', '14.2.0' in (HERE / 'preflight/gcc-version.stdout').read_text())
    check('common_strict_flags', protocol['common_release_flags'] == '-fno-fast-math -ffp-contract=off -fno-lto')
    identities = {label: source_snapshot(label) for label in COMMITS}
    delta = sorted(name for name in identities['baseline'] if identities['baseline'][name] != identities['candidate'][name])
    check('only_uci_existing_delta', delta == ['src/uci.cpp'])
    check('only_original_test_added', set(identities['candidate']) - set(identities['baseline']) == {TEST})
    baseline_uci = git('show', COMMITS['baseline'] + ':src/uci.cpp')
    candidate_uci = git('show', COMMITS['candidate'] + ':src/uci.cpp')
    old = b'game_search && (own_book || !book_file.empty()) && !book.empty()'
    new = b'game_search && own_book && !book.empty()'
    check('sole_exact_uci_condition_replacement', baseline_uci.count(old) == 1 and baseline_uci.replace(old, new, 1) == candidate_uci)
    test_bytes = git('show', COMMITS['candidate'] + ':' + TEST)
    test_path = Path(protocol['candidate_original_test'])
    check('original_156_line_script_exact', len(test_bytes.splitlines()) == 156 and sha(test_bytes) == TEST_SHA == protocol['candidate_original_test_sha256'] and test_path.read_bytes() == test_bytes)
    fixture_sha = sha(struct.pack('>QHHI', 0x463B96181691FC9C, (12 << 6) | 28, 100, 0))
    groups = set()
    preflight = HERE / 'preflight'
    command_record(preflight, 'gcc-version', [protocol['gcc_path'], '--version'], groups)
    help_record = command_record(preflight, 'original-test-help', [protocol['python_path'], '-B', str(test_path), '--help'], groups)
    source_record('preflight_original_test_source_unchanged_before', help_record['before']['source'], 'candidate', identities['candidate'])
    source_record('preflight_original_test_source_unchanged_after', help_record['after']['source'], 'candidate', identities['candidate'])
    profiles = []
    last_completed = None
    for name in ['baseline-release', 'candidate-release', 'candidate-asan']:
        label = 'baseline' if name == 'baseline-release' else 'candidate'
        asan = name == 'candidate-asan'
        expected_leak = label == 'baseline'
        directory = HERE / (name + '-attempt1')
        build = BASE / ('accepted-ownbook-' + name)
        source = BASE / ('accepted-ownbook-' + label + '-source')
        result = load(directory / 'RESULTS.json')
        check('profile_pass:' + name, result['status'] == 'PASS' and result['error'] is None and result['source_commit'] == COMMITS[label] and result['asan_ubsan'] is asan)
        check('profile_script_identity:' + name, result['candidate_original_test_commit'] == COMMITS['candidate'] and result['candidate_original_test_sha256'] == TEST_SHA)
        check('profile_fatal_environment:' + name, result['environment_subset']['PYTHONDONTWRITEBYTECODE'] == '1')
        if asan:
            check('fatal_asan_ubsan_leak_options', result['environment_subset']['ASAN_OPTIONS'] == 'halt_on_error=1:abort_on_error=1:detect_leaks=1' and result['environment_subset']['UBSAN_OPTIONS'] == 'halt_on_error=1:print_stacktrace=1')
        expected_commands = protocol['commands'][name]
        check('exact_five_steps:' + name, [row[0] for row in expected_commands] == STEP_NAMES and [step['label'] for step in result['steps']] == STEP_NAMES)
        steps = []
        for step_name, command in expected_commands:
            step = command_record(directory, step_name, command, groups)
            check('duplicated_step_record:' + name + ':' + step_name, step == result['steps'][len(steps)])
            for when in ['before', 'after']:
                source_record('source_frozen:' + name + ':' + step_name + ':' + when, step[when]['source'], label, identities[label])
            started = datetime.datetime.fromisoformat(step['started_utc'])
            completed = datetime.datetime.fromisoformat(step['completed_utc'])
            check('serial_execution:' + name + ':' + step_name, last_completed is None or last_completed <= started)
            last_completed = completed
            steps.append(step)
        build_anchor = steps[1]['after']['build']
        check('build_current_exact:' + name, build_anchor == result['after']['build'] == {file: file_identity(build / file) for file in BUILD_FILES})
        for step in steps[2:]:
            check('tested_build_before_after_unchanged:' + name + ':' + step['label'], step['before']['build'] == step['after']['build'] == build_anchor)
        check('phase1200_budget:' + name, result['timeout_seconds_total_phase'] == 1200 and (datetime.datetime.fromisoformat(steps[-1]['completed_utc']) - datetime.datetime.fromisoformat(steps[0]['started_utc'])).total_seconds() < 1200)
        for when in ['before', 'after']:
            source_record('overall_source_frozen:' + name + ':' + when, result[when]['source'], label, identities[label])
        discovery = load(directory / 'ctest-discovery.stdout')['tests']
        check('exact_four_ctest_names:' + name, len(discovery) == 4 and {row['name'] for row in discovery} == TEST_NAMES)
        expected_tests = {'forge_tests': [str(build / 'forge_tests')], 'match_tool_tests': [protocol['python_path'], str(source / 'tools/match/test_match_tools.py')], 'uci_regression': [protocol['python_path'], str(source / 'tools/uci_regression.py'), str(build / 'forge'), '--log', str(build / 'uci-regression.log')], 'ponder_regression': [protocol['python_path'], str(source / 'tools/ponder_regression.py'), str(build / 'forge')]}
        check('exact_ctest_executables:' + name, all(row['command'] == expected_tests[row['name']] for row in discovery))
        ctest_text = (directory / 'ctest.stdout').read_text()
        check('four_raw_ctest_passes:' + name, '100% tests passed, 0 tests failed out of 4' in ctest_text and len(re.findall(r'Test #\d+:.*Passed', ctest_text)) == 4)
        last_test = build / 'Testing/Temporary/LastTest.log'
        check('four_actual_lasttest_passes:' + name, last_test.read_text().count('Test Passed.') == 4 and re.search(r'Ran 15 tests', last_test.read_text()) is not None)
        cache = (build / 'CMakeCache.txt').read_text()
        check('native_off_and_sanitizer_cache:' + name, 'FORGE_NATIVE:BOOL=OFF' in cache and 'FORGE_ENABLE_SANITIZERS:BOOL=' + ('ON' if asan else 'OFF') in cache)
        for row in load(build / 'compile_commands.json'):
            tokens = shlex.split(row['command'])
            check('strict_gcc_compile_flags:' + name + ':' + row['file'], tokens[0] == protocol['gcc_path'] and all(flag in tokens for flag in ['-O3', '-DNDEBUG', '-fno-fast-math', '-ffp-contract=off', '-fno-lto']) and not any(flag in tokens for flag in ['-ffast-math', '-march=native', '-flto']))
            if asan:
                check('asan_ubsan_instrumented:' + row['file'], '-fsanitize=address,undefined' in tokens and '-fno-omit-frame-pointer' in tokens and '-fno-pie' in tokens)
        if asan:
            link = (build / 'CMakeFiles/forge.dir/link.txt').read_text()
            check('asan_ubsan_link', '-fsanitize=address,undefined' in link and '-no-pie' in link)
        own_result = load(directory / 'ownbook-original/result.json')
        check('five_original_ownbook_assertions:' + name, own_result == result['original_ownbook_result'] and own_result['result'] == 'PASS' and own_result['expected_baseline_leak'] is expected_leak and own_result['disabled_first'] is expected_leak and own_result['disabled_after_toggle'] is expected_leak and own_result['enabled'] is True and own_result['fixture_sha256'] == fixture_sha and own_result['tests'] == ['one-entry Polyglot fixture loaded', 'original bypass reproduced' if expected_leak else 'OwnBook false respected', 'enabled external book selects e2e4', 'depth analysis bypasses book', 'post-toggle behavior verified'])
        own_command = steps[-1]['command']
        check('unmodified_script_against_exact_engine:' + name, own_command == [protocol['python_path'], '-B', str(test_path), str(build / 'forge'), '--expect-leak', 'yes' if expected_leak else 'no', '--out', str(directory / 'ownbook-original')])
        segments = ownbook_segments(directory / 'ownbook-original/raw_uci.log', expected_leak)
        if asan:
            for path in [directory / 'ctest.stdout', directory / 'ctest.stderr', directory / 'ownbook.stdout', directory / 'ownbook.stderr', directory / 'ownbook-original/raw_uci.log', last_test]:
                check('no_sanitizer_diagnostic:' + str(path), DIAGNOSTIC.search(path.read_text(errors='replace')) is None)
        profiles.append({'profile': name, 'ctests_passed': 4, 'ownbook_assertions_passed': 5, 'expected_baseline_leak': expected_leak, 'segments': segments, 'tested_engine': build_anchor['forge'], 'tested_core': build_anchor['libforge_core.a']})
    check('release_core_identical', profiles[0]['tested_core'] == profiles[1]['tested_core'])
    remaining = live_groups(groups)
    check('no_current_live_owned_groups', not remaining)
    return {'status': 'passed', 'source_commits': COMMITS, 'source_file_counts': {k: len(v) for k, v in identities.items()}, 'original_test_sha256': TEST_SHA, 'original_test_lines': 156, 'profiles': profiles, 'ctest_suites_passed': 12, 'original_ownbook_assertions_passed': 15, 'owned_groups_checked': sorted(groups), 'current_live_owned_processes': remaining, 'sanitizer_diagnostics': [], 'engine_execution_during_audit': False, 'build_or_test_execution_during_audit': False, 'integration_performed_by_audit': False, 'transcript_qualification': 'Original directional text transcripts strip CRLF and combine engine stdout/stderr; they are not original process-byte captures.', 'scope': 'The specific external Polyglot book toggle/depth contract on these exact local builds. No universal legality, OwnBook completeness, speed, strength, remote-CI artifact, or integration acceptance claim.'}


if __name__ == '__main__':
    assert not (HERE / 'independent-audit.json').exists() and not (HERE / 'independent-audit.md').exists(), 'Never overwrite an audit attempt'
    try:
        report = main()
    except BaseException as error:
        report = {'status': 'failed', 'error_type': type(error).__name__, 'error': str(error), 'engine_execution_during_audit': False}
        raise
    finally:
        report.update(audited_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), check_count=len(checks), checks=checks, checker_sha256=sha(Path(__file__).read_bytes()))
        with (HERE / 'independent-audit.json').open('x') as stream:
            json.dump(report, stream, indent=2); stream.write('\n')
        if report['status'] == 'passed':
            text = f"""Independent accepted-lineage OwnBook audit passed {len(checks)} checks.

Exact source356e863 and source5101c25 exports match Git. The sole production
change requires OwnBook=true for timed external-book selection; the original
156-line candidate script is unchanged and runs against all three exact builds.
Baseline Release reproduces the disabled-book leak before and after toggling;
candidate Release and ASan/UBSan suppress it. Every profile uses e2e4 when
external book is enabled and bypasses book for depth2 analysis. All 12 original
CTest suites and 15 original OwnBook assertions passed. GCC14.2, common strict
float flags, FORGE_NATIVE=OFF, fatal sanitizer/leak options, recorded return
codes, process-group cleanup and before/after source/executable/core identities
agree with original evidence. No current live owned process group remains.

The directional UCI text strips CRLF and combines stderr/stdout; it is not a
raw process-byte capture. Returned moves were syntax-checked, not independently
legality-oracle checked. This is the bounded external-book toggle/depth contract;
it does not establish universal correctness, speed, strength, remote-CI artifact
accessibility or an integration decision. The audit ran no engines or tests.
"""
        else:
            text = 'Independent audit FAILED; attempt retained.\n\n' + report['error_type'] + ': ' + report['error'] + '\nNo engine or test was executed by the audit.\n'
        with (HERE / 'independent-audit.md').open('x') as stream:
            stream.write(text)
    print(json.dumps({key: report[key] for key in ['status', 'check_count', 'source_file_counts', 'ctest_suites_passed', 'original_ownbook_assertions_passed']}, indent=2))
