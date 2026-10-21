from pathlib import Path
import json,re
HERE=Path(__file__).resolve().parent
PARENT='2e151d019bc58dff2ab4e76e99ef99516af8d222'
SOURCE_COMMIT='ff2e269c6058be84456e3b98344826d17b0056eb' # Root-declared frozen22 SHA; full native clearance remains required.
def load_freeze(stage='build'):
    assert stage in ('source','build')
    path=HERE/'WINDOWS-BUILD-CLEAR.json'
    if not path.is_file():raise RuntimeError('22 Windows OFFLINE PREPARATION ONLY: explicit root full-native42/8 clearance is required before exports/build/runtime/package/audit')
    data=json.loads(path.read_text())
    assert isinstance(SOURCE_COMMIT,str) and re.fullmatch(r'[0-9a-f]{40}',SOURCE_COMMIT),'Exact root22 source SHA not bound'
    assert data.get('authorization')=='22 WINDOWS BUILD CLEAR','Root22 execution authorization missing'
    assert data.get('source_commit')==SOURCE_COMMIT and data.get('parent_source_commit')==PARENT,'Incorrect frozen source/parent identity'
    for field,value in [('runtime_summary_checks',347),('correction_checks',54),('pawn_span_checks',37320),('nearest_pawn_checks',791680),('nearest_pawn_sets',395840),('pv_metadata_assertions',56),('source_files',74)]:
        assert type(data.get(field)) is int and data[field]==value,'Root22 count mismatch: '+field
    assert data.get('bench_expected_nodes') is None,'Search-changing Windows22 signature must start unknown'
    assert data.get('bench_signature_policy')=='FIRST_NORMAL_CANDIDATE_CAPTURE_ONLY','Candidate first-capture signature policy required'
    assert data.get('root_proof_namespace')=='validation/pv-metadata-20261021/root-verification','Incorrect root22 proof namespace'
    return data
