from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
PARENT='fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e'
SOURCE_COMMIT='2e151d019bc58dff2ab4e76e99ef99516af8d222'
def load_freeze(stage='build'):
    assert stage in ('source','build')
    source=HERE/'ROOT-SOURCE-FREEZE.json'
    path=source if stage=='source' and source.is_file() else HERE/'WINDOWS-BUILD-CLEAR.json'
    if not path.is_file():raise RuntimeError('21 Windows OFFLINE PREPARATION ONLY: explicit root full-native clearance is required before exports/build/runtime/package/audit')
    data=json.loads(path.read_text())
    expected='21 WINDOWS SOURCE EXPORT CLEAR' if path==source else '21 WINDOWS BUILD CLEAR'
    assert data.get('authorization')==expected, 'Root21 execution authorization missing'
    assert data.get('source_commit')==SOURCE_COMMIT and data.get('parent_source_commit')==PARENT,'Incorrect frozen source/parent identity'
    for field,value in [('runtime_summary_checks',347),('correction_checks',54),('pawn_span_checks',37320),('nearest_pawn_checks',791680),('nearest_pawn_sets',395840),('bench_expected_nodes',352313),('source_files',73)]:
        assert type(data.get(field)) is int and data[field]==value,'Root21 count/signature mismatch: '+field
    return data
