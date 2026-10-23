#!/usr/bin/env python3
"""Independent source/data review only; never import or run reviewed code."""
from pathlib import Path, PurePosixPath
import ast
import datetime
import hashlib
import json
import re
import stat

REPO = Path('/workspace/dwqww')
PACKET = REPO / '.github/hosted-see-proof-performance'
VALIDATION = REPO / 'validation/hosted-see-proof-performance-20261021'
HERE = Path(__file__).resolve().parent
WORKFLOW = REPO / '.github/workflows/forge-hosted-see-proof-performance.yml'
TEMPLATE = VALIDATION / 'template-originals'
checks, findings = [], []


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(name, passed, **detail):
    row = {'name': name, 'passed': bool(passed), **detail}
    checks.append(row)
    if not passed:
        findings.append(row)
    return bool(passed)


def safe(name):
    if (not isinstance(name, str) or PurePosixPath(name).is_absolute()
            or '\\' in name or any(x in ('', '.', '..') for x in name.split('/'))):
        raise ValueError('Unsafe literal evidence entry: ' + repr(name))
    path = REPO / name
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        if stat.S_ISLNK(current.lstat().st_mode):
            raise ValueError('Symlink component: ' + str(current))
    if not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError('Nonregular evidence: ' + str(path))
    return path


def verify_manifest(path, count):
    # Both producers record repository-relative names, resolved once at REPO.
    before = path.read_bytes()
    rows = []
    names = set()
    for line in before.decode().splitlines():
        match = re.fullmatch(r'([0-9a-f]{64})  (.+)', line)
        if not match:
            raise ValueError('Malformed manifest row')
        expected, name = match.groups()
        if name in names:
            raise ValueError('Duplicate manifest entry: ' + name)
        names.add(name)
        target = safe(name)
        if not (target.is_relative_to(PACKET) or target.is_relative_to(VALIDATION) or target == WORKFLOW):
            raise ValueError('Entry outside packet/proof scope: ' + name)
        observed = sha(target)
        check('sealed_file:' + name, observed == expected)
        rows.append({'path': name, 'expected_sha256': expected, 'observed_sha256': observed})
    check('manifest_count:' + path.name, len(rows) == count, observed=len(rows), expected=count)
    check('manifest_unchanged:' + path.name, path.read_bytes() == before)
    return {'path': str(path), 'sha256': hashlib.sha256(before).hexdigest(),
            'explicit_resolution_base': str(REPO), 'row_count': len(rows), 'files': rows}


def tree(path):
    return ast.parse(path.read_text())


def functions(parsed):
    return {n.name: n for n in parsed.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def dump(node):
    return ast.dump(node, include_attributes=False)


def literals(parsed):
    result = {}
    for node in parsed.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                result[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                pass
    return result


def main():
    output = HERE / 'REVIEW.json'
    if output.exists() or output.is_symlink():
        raise SystemExit('Refusing to overwrite an independent review')
    seals = [verify_manifest(VALIDATION / 'EVIDENCE-SHA256SUMS', 61),
             verify_manifest(PACKET / 'PACKAGE-SHA256SUMS', 10)]
    cfg = json.loads((PACKET / 'protocol.json').read_text())
    checkpoint = json.loads((VALIDATION / 'PREPARATION-CHECKPOINT.json').read_text())
    offline = json.loads((VALIDATION / 'OFFLINE-RESULT.json').read_text())
    for name, expected in checkpoint['pins'].items():
        check('checkpoint_pin:' + name, sha(safe(name)) == expected)
    parsed = {p.name: tree(p) for p in sorted(PACKET.glob('*.py'))}
    check('seven_execution_sources_parse_without_import', len(parsed) == 7)
    common = literals(parsed['common.py'])
    analysis = literals(parsed['analysis.py'])
    evidence = literals(parsed['build_evidence.py'])
    check('actual23_and24_identity', common['BASELINE'] == cfg['baseline_sha'] == '1d3ed25bea2c8b781f7ee5a178af0f66061b3984'
          and common['CANDIDATE'] == cfg['candidate_sha'] == '7db08eac6ead99d641834c56ccec06a06600586a')
    check('signature_honestly_unbound', common['EXPECTED_NODES'] is None and analysis['EXPECTED_NODES'] is None
          and cfg['expected_nodes'] is None and cfg['candidate_first_native_signature_nodes'] is None)
    check('readiness_proofs_captures_reviews_pending', cfg['status'].startswith('DRAFT_DISABLED')
          and cfg['workflow_status'] == 'DISABLED' and cfg['workflow_sha256'] is None
          and cfg['correctness_evidence_sha256'] == {} and cfg['transport_captures'] == {}
          and all(cfg[k].startswith('PENDING') for k in ['source_gates_status', 'parity_review_status', 'capture_review_status', 'root_review_status', 'independent_review_status']))
    workflow = WORKFLOW.read_text()
    check('workflow_disabled_twice', re.search(r'^on: \[\]\s*$', workflow, re.M) is not None
          and '    if: ${{ false }}' in workflow and 'workflow_dispatch' not in workflow)
    check('explicit_full_source_and_test_counts', evidence['SOURCE_FILE_COUNTS'] == cfg['source_file_counts'] == {'baseline': 77, 'candidate': 77}
          and len(evidence['BASELINE_TESTS']) == 14 and evidence['BASELINE_TESTS'][4:6] == ('forge_nearest_pawn_tests', 'forge_pv_metadata_tests'))
    check('candidate_uses_same_fourteen_named_suites', 'CANDIDATE_TESTS=BASELINE_TESTS' in (PACKET / 'build_evidence.py').read_text())
    check('strict_release_flags', common['FLAGS'] == cfg['release_flags'] == evidence['RELEASE_FLAGS']
          == '-O3 -DNDEBUG -march=x86-64-v3 -mtune=generic -fno-fast-math -ffp-contract=off -fno-lto')
    check('fifteen_aa_thirtyone_ab_five_benches_no_retries', cfg['aa_blocks'] == 15 and cfg['ab_blocks'] == 31
          and cfg['benches_per_process'] == analysis['BENCHES_PER_PROCESS'] == 5
          and cfg['attempts'] == 1 and cfg['fault_retries'] == 0
          and cfg['bounds']['planned_fresh_processes'] == 188 and cfg['bounds']['planned_bench_commands'] == 940)
    check('all_thirteen_future_proofs_explicit', len(common['REQUIRED_PROOFS']) == 13
          and list(common['REQUIRED_PROOFS']) == cfg['mandatory_finite_proof_paths'])
    current_run, old_run = functions(parsed['run_hosted.py']), functions(tree(TEMPLATE / 'run_hosted.py'))
    for name in ['validate_sample', 'run_experiment']:
        check('unchanged_timing_function:' + name, dump(current_run[name]) == dump(old_run[name]))
    current_build, old_build = functions(parsed['build_evidence.py']), functions(tree(TEMPLATE / 'build_evidence.py'))
    check('all_build_evidence_functions_unchanged', current_build.keys() == old_build.keys()
          and all(dump(node) == dump(old_build[name]) for name, node in current_build.items()))
    current_analysis, old_analysis = functions(parsed['analysis.py']), functions(tree(TEMPLATE / 'analysis.py'))
    check('statistical_functions_unchanged', all(dump(node) == dump(old_analysis[name]) for name, node in current_analysis.items() if name != 'parse_bench'))
    parse = current_analysis['parse_bench']
    check('parser_only_added_pending_signature_guard', isinstance(parse.body[0], ast.If)
          and [dump(n) for n in parse.body[1:]] == [dump(n) for n in old_analysis['parse_bench'].body])
    main = current_run['main']
    outer = next(n for n in main.body if isinstance(n, ast.Try))
    restore = outer.finalbody[0]
    check('independent_outer_finally_restores_affinity', isinstance(restore, ast.Try)
          and 'os.sched_setaffinity(0, old_affinity)' in ast.unparse(restore.body[0])
          and any(isinstance(n, ast.Try) and n.finalbody for n in outer.body))
    check('restore_failure_invalidates_gain_and_preserves_operation_error',
          'raise operation_error from restore_error' in ast.unparse(restore)
          and 'verified_hosted_gain=False' in (PACKET / 'run_hosted.py').read_text())
    for name, expected in [('owned_process.py', '461a65d2fecdf208994749cb0d44c56bf2f8524610f211a4bf76bd019c25704d'),
                           ('archive_results.py', '952a090fee4f5ce67df93f5f389be5e46138f5b5787161c96156d80ad1fbaf6c')]:
        check('qualified_helper_unchanged:' + name, sha(PACKET / name) == expected and (PACKET / name).read_bytes() == (TEMPLATE / name).read_bytes())
    transport = functions(parsed['common.py'])['transport_paths']
    transport_text = ast.unparse(transport)
    check('capture_role_selector_keeps_original_identity_guards', all(value in transport_text for value in [
        "entry.get('provenance_capture_label', label)", "capture.get('source_commit') != commit",
        "before != after", "before.get('forge') != entry['engine_sha256']",
        "capture.get('process_facts') != facts", "source != capture.get('source_sha256_after')",
        "capture.get(stream + '_sha256') != sha(paths[stream])"]))
    for stream in ['stdout', 'stderr']:
        check('retained_complete_offline_stream:' + stream, sha(VALIDATION / ('offline-final-attempt1.' + stream)) == offline[stream + '_sha256'])
    final_test_log = (VALIDATION / 'offline-final-attempt1.stderr').read_text()
    check('retained_complete_fortytwo_test_result', offline['tests'] == 42 and offline['exit_code'] == 0
          and offline['tool_completion_exit_observed'] is True and 'Ran 42 tests in 10.454s\n\nOK' in final_test_log
          and sum(offline['suite_breakdown'].values()) == 42)
    for filename, marker in [('lifecycle-red.stderr', 'FAILED (failures=2)'), ('lifecycle-green.stderr', '\nOK\n'),
                             ('capture-adapter-red.stderr', 'FAILED (errors=1)'), ('capture-adapter-green.stderr', '\nOK\n')]:
        check('first_red_green_retained:' + filename, marker in (VALIDATION / filename).read_text())
    reuse = json.loads((VALIDATION / 'ACTUAL23-REUSE-REFERENCE.json').read_text())
    for name, expected in reuse['input_bytes_modes'].items():
        target = safe(name)
        check('actual23_reference_unchanged:' + name, sha(target) == expected['sha256']
              and stat.S_IMODE(target.stat().st_mode) == expected['mode'])
    entry = reuse['baseline_role_entry']
    provenance = json.loads(safe(entry['provenance_path']).read_text())
    original_side = provenance['captures'][entry['provenance_capture_label']]
    source_map = json.loads(safe(entry['source_manifest_path']).read_text())['inputs']
    check('actual23_original_candidate_role_is_preserved', entry['provenance_capture_label'] == 'candidate'
          and original_side['source_commit'] == common['BASELINE'] == entry['source_commit']
          and provenance['captures']['baseline']['source_commit'] == 'ff2e269c6058be84456e3b98344826d17b0056eb'
          and original_side['source_sha256_before'] == original_side['source_sha256_after'] == source_map
          and len(source_map) == 77 and original_side['binary_sha256_before'] == original_side['binary_sha256_after']
          and original_side['binary_sha256_before']['forge'] == entry['engine_sha256'])
    report = {'status': 'PASS_DISABLED_SOURCE_DATA_REVIEW_NOT_LAUNCH_AUTHORIZATION' if not findings else 'FAILED_DISABLED_SOURCE_DATA_REVIEW',
              'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'checks': checks,
              'check_count': len(checks), 'findings': findings, 'seals': seals,
              'reviewer_source_sha256': sha(Path(__file__)), 'protocol_sha256': sha(PACKET / 'protocol.json'),
              'workflow_sha256': sha(WORKFLOW), 'checkpoint_sha256': sha(VALIDATION / 'PREPARATION-CHECKPOINT.json'),
              'instructions_read': {str(p): sha(p) for p in [REPO / 'AGENTS.md', REPO / '.agents/skills/validating-chess-strength/SKILL.md']},
              'method': 'Independent manual source/diff review plus standard-library AST, exact SHA and retained data checks. Reviewed packet modules and tests were never imported or executed.',
              'qualifications': ['This verdict covers the current disabled packet only; it does not qualify actual24 native validation, capture, enabled bytes or a hosted launch.',
                                 'Retained42-test exit/completion facts come from the sealed original receipt and raw streams; tests were not independently rerun.',
                                 'The role-selector positive test temporarily binds the original23 signature and a same-source candidate role. It proves consumer compatibility, not actual24 producer acceptance.',
                                 'Outer finally restoration depends on Python finally executing; hard host termination is outside its guarantee.',
                                 'No speed, Elo, pure SEE-kernel, Windows/Ryzen or general clock-reliability conclusion is made.'],
              'pending_before_enablement': cfg['remaining_proof_inputs'],
              'engine_build_test_git_network_workflow_execution': False, 'existing_inputs_modified': False}
    with output.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'status': report['status'], 'check_count': len(checks), 'findings': findings,
                      'seal_rows': [r['row_count'] for r in seals], 'review_sha256': sha(output)}, indent=2))
    return int(bool(findings))


if __name__ == '__main__':
    raise SystemExit(main())
