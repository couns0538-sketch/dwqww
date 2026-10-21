from pathlib import Path
import hashlib,json,re
HERE=Path(__file__).resolve().parent
PARENT='1d3ed25bea2c8b781f7ee5a178af0f66061b3984'
SOURCE_COMMIT='7db08eac6ead99d641834c56ccec06a06600586a'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load_freeze(stage='build'):
    assert stage in ('source','build')
    path=HERE/'WINDOWS-BUILD-CLEAR.json'
    if not path.is_file():raise RuntimeError('24 Windows OFFLINE PREPARATION ONLY: explicit root full-native42/8/56parity clearance required before exports/build/runtime/package/audit')
    data=json.loads(path.read_text())
    assert data.get('authorization')=='24 WINDOWS BUILD CLEAR'
    assert data.get('source_commit')==SOURCE_COMMIT and data.get('parent_source_commit')==PARENT
    for field,value in [('runtime_summary_checks',347),('correction_checks',54),('pawn_span_checks',37320),('nearest_pawn_checks',791680),('nearest_pawn_sets',395840),('pv_metadata_assertions',56),('source_files',74),('tt_groups',12),('see_threshold_assertions',504)]:
        assert type(data.get(field)) is int and data[field]==value,'Root24 count mismatch: '+field
    assert data.get('bench_expected_nodes') is None and data.get('bench_signature_policy')=='FIRST_NORMAL_CANDIDATE_CAPTURE_ONLY'
    assert data.get('parent_bench_parity_nodes')==334752,'Same-platform pure optimization parity required after first actual capture'
    assert data.get('root_proof_namespace')=='validation/see-proof-reuse-candidate-20261021'
    assert data.get('root_source_gates_path')=='/workspace/dwqww/validation/see-proof-reuse-candidate-20261021/ROOT-FROZEN24-SOURCE-GATES.json'
    for field in ['root_source_gates_sha256','root_native_proof_sha256']:
        assert isinstance(data.get(field),str) and re.fullmatch(r'[0-9a-f]{64}',data[field])
    assert data.get('root_source_gates_sha256')=='8be7f3a73111350eca27adbe76bf001e5ab26915c73f1201c3056f881a87afd1'
    sourcegate=Path(data['root_source_gates_path']);assert sha(sourcegate)==data['root_source_gates_sha256']
    g=json.loads(sourcegate.read_text());assert g['source_commit']==SOURCE_COMMIT and g['baseline_commit']==PARENT
    assert g['inputs']==json.loads((HERE/'PREPARED-EXPECTED77.json').read_text())
    nativepath=Path(data['root_native_proof_path']);assert sha(nativepath)==data['root_native_proof_sha256']
    native=json.loads(nativepath.read_text());assert native['source_commit']==SOURCE_COMMIT and native['ctest']==42 and native['active_uci']==8
    assert data.get('production_search_sha256')==g['inputs']['src/search.cpp']
    assert data.get('core_test_sha256')==g['inputs']['tests/tests.cpp']
    assert data.get('tt_test_sha256')=='cc2fe3e9fb0059f409876345e8cfb3c008ede401751a4dad76b022f743238fd5'
    assert data.get('pv_metadata_test_sha256')=='8000b717a298c4c8bb637752fcc57a0ce485110a12edc4a505f3d0452620bd1e'
    return data
