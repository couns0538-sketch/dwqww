from pathlib import Path
import json,re
HERE=Path(__file__).resolve().parent
PARENT='61f598056572dfade6994af8ad2e38817cd28aa3'
EXPECTED_BENCH=352313
EXPECTED_RUNTIME=347
EXPECTED_CORRECTION=54
EXPECTED_PAWN=37320
EXPECTED_SOURCE_FILES=72
def load_freeze(stage='build'):
    assert stage in ('source','build'), 'Invalid authorization stage'
    source=HERE/'ROOT-SOURCE-FREEZE.json'
    path=source if stage=='source' and source.is_file() else HERE/'WINDOWS-BUILD-CLEAR.json'
    if not path.is_file():raise RuntimeError('20 Windows preparation only: root frozen source and full native/build clearance required')
    data=json.loads(path.read_text())
    expected='20 WINDOWS SOURCE EXPORT CLEAR' if path==source else '20 WINDOWS BUILD CLEAR'
    assert data.get('authorization')==expected, 'Incorrect root20 authorization'
    commit=data.get('source_commit')
    assert isinstance(commit,str) and re.fullmatch('[0-9a-f]{40}',commit) and commit!=PARENT, 'Root20 source not frozen'
    assert data.get('parent_source_commit')==PARENT, 'Incorrect immutable Windows19 parent'
    for field,value in [('runtime_summary_checks',EXPECTED_RUNTIME),('correction_checks',EXPECTED_CORRECTION),('pawn_span_checks',EXPECTED_PAWN),('bench_expected_nodes',EXPECTED_BENCH),('source_files',EXPECTED_SOURCE_FILES)]:
        assert type(data.get(field)) is int and data[field]==value, 'Root20 preregistered count/signature mismatch: '+field
    return data
