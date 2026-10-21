#!/usr/bin/env python3
"""Root read-only rehash of frozen native22 originals; executes no engine/build."""
from pathlib import Path
import datetime, hashlib, io, json, stat, subprocess, tarfile

REPO = Path('/workspace/dwqww')
HERE = Path(__file__).resolve().parent
EVIDENCE = REPO / 'validation/pv-metadata-native-20261021'
REV = 'ff2e269c6058be84456e3b98344826d17b0056eb'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load(path):
    return json.loads(path.read_text())

def check_file(path, expected):
    assert path.is_file() and not path.is_symlink(), str(path)
    assert sha(path) == expected['sha256'], str(path)
    assert path.stat().st_size == expected['bytes'], str(path)
    assert stat.S_IMODE(path.stat().st_mode) == expected['mode'], str(path)

def main():
    receipt = load(EVIDENCE / 'FINAL-RECEIPT.json')
    snapshot = load(EVIDENCE / 'ORIGINALS-FINAL-SHA256.json')
    assert snapshot['source_commit'] == REV
    assert snapshot['engines_or_builds_executed_for_snapshot'] is False
    counts = {}
    for label, tree in snapshot['trees'].items():
        root = Path(tree['root'])
        actual = {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
        assert actual == set(tree['files']), label
        for name, expected in tree['files'].items():
            check_file(root / name, expected)
        directories = {'.': stat.S_IMODE(root.stat().st_mode), **{
            str(p.relative_to(root)): stat.S_IMODE(p.stat().st_mode)
            for p in root.rglob('*') if p.is_dir()}}
        assert directories == tree['directory_modes'], label
        counts[label] = len(actual)
    assert counts['source'] == 77 and set(counts) == {'source', 'release', 'asan', 'tsan'}
    assert all(counts[p] > 0 for p in ('release', 'asan', 'tsan'))
    for record in snapshot['single_files'].values():
        check_file(Path(record['path']), record)
    compiler = snapshot['compiler']
    assert sha(Path(compiler['path'])) == compiler['sha256']
    assert str(Path(compiler['path']).resolve()) == compiler['resolved_path']
    archive = subprocess.check_output(['git', 'archive', REV, 'CMakeLists.txt', 'LICENSE', 'bench', 'include', 'src', 'tests', 'tools'], cwd=REPO)
    with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
        git_inputs = {m.name: hashlib.sha256(stream.extractfile(m).read()).hexdigest()
                      for m in stream.getmembers() if m.isfile()}
    source = {n: v['sha256'] for n, v in snapshot['trees']['source']['files'].items()}
    assert git_inputs == source
    gate = load(EVIDENCE / 'ROOT-FROZEN-SOURCE-GATES.json')
    assert gate['inputs'] == source and gate['source_commit'] == REV
    clear = load(EVIDENCE / 'ROOT-CLEARANCE.json')
    assert clear['source_commit'] == REV and clear['authorized'] is True
    assert clear['expected_full_native_ctests'] == 42
    assert clear['expected_pv_metadata_assertions'] == 56
    assert clear['default_tsan_options'] == 'halt_on_error=1:exitcode=66'
    assert clear['suppression_or_deadlock_detector_disabled'] is False
    audit = load(EVIDENCE / 'independent-audit.json')
    assert audit['status'] == 'passed' and audit['source_commit'] == REV
    assert audit['check_count'] == len(audit['checks']) and audit['check_count'] > 0
    assert audit['failed_check_count'] == 0 and all(c['passed'] for c in audit['checks'])
    assert audit['engine_compiler_or_test_execution_during_audit'] is False
    for profile in ('release', 'asan', 'tsan'):
        result = load(EVIDENCE / ('frozen-' + profile + '-attempt1/summary.json'))
        assert result['status'] == 'PASS' and result['source_commit'] == REV
        assert len(result['ctest_names']) == 14
        assert result['ctest_names'][4:6] == ['forge_nearest_pawn_tests', 'forge_pv_metadata_tests']
        assert result['pv_metadata_contract_actual_summaries'] == [['56', '0']]
        cases = result['pv_metadata_case_rows']
        assert [row[0] for row in cases] == ['PV_nonPVhit', 'PV_PVhit', 'PV_nohit', 'nullwindow_TTcut', 'PV_abort_verification']
        assert [row[3] for row in cases] == ['1', '1', '1', '0', '1']
        assert cases[-1][1:] == ['2', '1', '1', '0']
        assert result['runtime_psqt_contract_actual_summaries'] == [['347', '0']]
        assert result['pawn_span_contract_actual_summaries'] == [['37320', '0']]
        assert result['nearest_pawn_contract_actual_summaries'] == [['395840', '791680', '0']]
        assert result['nearest_constexpr_assertions'] == 6
        assert result['source_sha256_before_tests'] == result['source_sha256_after_tests'] == source
        assert result['binary_sha256_before'] == result['binary_sha256_after']
    signature = load(EVIDENCE / 'release-signature-wrapper-attempt1/summary.json')
    assert signature['status'] == 'PASS' and signature['actual_bench11_signatures'] == [292545]
    assert signature['exact_search_parity_required'] is False
    assert signature['observational_cold_warm_searches'] == 0
    assert load(EVIDENCE / 'active-uci-wrapper-attempt1/COMMAND.json')['status'] == 'PASS'
    nnue = Path(snapshot['trees']['release']['root']) / 'CMakeFiles/forge_core.dir/src/nnue.cpp.o'
    assert sha(nnue) == snapshot['single_files']['baseline_nnue_object']['sha256']
    assert receipt['status'] == 'STABLE' and receipt['source_commit'] == REV
    assert receipt['native_ctests'] == 42 and receipt['default_tsan_active_checks'] == 8
    assert receipt['exact_search_parity_required'] is False
    assert receipt['observational_cold_warm_searches'] == 0
    assert receipt['bench11_nodes'] == 292545
    attempts = {}
    for profile in ('release', 'asan', 'tsan'):
        entry = receipt['native_profiles'][profile]
        assert type(entry['attempts']) is int and entry['attempts'] == 1
        assert type(entry['ctest_count']) is int and entry['ctest_count'] == 14
        original = EVIDENCE / entry['receipt_path']
        assert sha(original) == entry['receipt_sha256']
        attempts[profile] = entry['attempts']
    manifest = EVIDENCE / 'EVIDENCE-SHA256SUMS'
    bound = {}
    for line in manifest.read_text().splitlines():
        expected, name = line.split('  ', 1)
        assert len(expected) == 64 and all(c in '0123456789abcdef' for c in expected)
        assert not Path(name).is_absolute() and '..' not in Path(name).parts and name not in bound
        file = EVIDENCE / name
        assert file.is_file() and not file.is_symlink() and sha(file) == expected, name
        bound[name] = expected
    actual = {p.relative_to(EVIDENCE).as_posix() for p in EVIDENCE.rglob('*') if p.is_file()}
    assert actual == set(bound) | {'EVIDENCE-SHA256SUMS'}
    assert not any(p.is_symlink() for p in EVIDENCE.rglob('*'))
    report = {'status': 'PASS_ROOT_FULL_NATIVE22_ORIGINALS_AND_GIT_SOURCE_REVIEW',
              'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'source_commit': REV, 'whole_live_original_trees': counts,
              'whole_live_original_files': sum(counts.values()),
              'single_originals_rehashed': len(snapshot['single_files']),
              'source_git_blobs_verified': len(git_inputs),
              'ctest': 42, 'runtime_psqt_checks_each_profile': 347,
              'pawn_span_checks_each_profile': 37320,
              'nearest_pawn_checks_each_profile': 791680,
              'nearest_target_sets_each_profile': 395840,
              'nearest_constexpr_assertions_each_profile': 6,
              'active_uci': 8, 'exact_search_parity_required': False,
              'observational_cold_warm_searches': 0,
              'pv_metadata_assertions_each_profile': 56,
              'bench11_nodes': 292545,
              'independent_audit_passed': audit['check_count'],
              'native_final_receipt_sha256': sha(EVIDENCE / 'FINAL-RECEIPT.json'),
              'originals_snapshot_sha256': sha(EVIDENCE / 'ORIGINALS-FINAL-SHA256.json'),
              'native_nnue_object_bit_identical_to_parent21': True,
              'nnue_object_sha256': sha(nnue),
              'engine_or_build_execution_by_this_review': 0,
              'engine_gate_retries': sum(a - 1 for a in attempts.values()),
              'native_profile_attempts': attempts,
              'native_manifest_sha256': sha(manifest),
              'evidence_records_rehashed': len(bound),
              'exact_evidence_tree_verified': True,
              'root_originals_verifier_sha256': sha(Path(__file__)),
              'nps_difference': None, 'elo_gain': None}
    with (HERE / 'NATIVE.json').open('x') as output:
        json.dump(report, output, indent=2); output.write('\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
