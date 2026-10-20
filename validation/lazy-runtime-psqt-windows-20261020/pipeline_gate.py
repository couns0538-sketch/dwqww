from pathlib import Path
import json,re
HERE=Path(__file__).resolve().parent
PARENT='fc51e43c26f735cbc1ffabf0fcf64f48a4592c0b'
EXPECTED_SOURCE='61f598056572dfade6994af8ad2e38817cd28aa3'
EXPECTED_BENCH=352313
EXPECTED_CORRECTION=54
EXPECTED_RUNTIME=347
def load_freeze(stage='build'):
    assert stage in ('source','build'), 'Invalid authorization stage'
    path=HERE/('ROOT-SOURCE-FREEZE.json' if stage=='source' else 'WINDOWS-BUILD-CLEAR.json')
    if not path.is_file(): raise RuntimeError('19 Windows build/runtime/package gate remains closed until explicit root build clearance')
    data=json.loads(path.read_text())
    expected='19 WINDOWS SOURCE EXPORT CLEAR' if stage=='source' else '19 WINDOWS BUILD CLEAR'
    assert data.get('authorization')==expected, 'Root 19 authorization missing for requested stage'
    assert isinstance(data.get('source_commit'),str) and re.fullmatch('[0-9a-f]{40}',data['source_commit']) and data['source_commit']==EXPECTED_SOURCE, 'Incorrect frozen source SHA'
    assert data.get('parent_source_commit')==PARENT, 'Incorrect immutable Windows18 parent'
    count=data.get('runtime_summary_checks')
    assert isinstance(count,int) and not isinstance(count,bool) and count==EXPECTED_RUNTIME, 'Root final runtime SUMMARY count mismatch'
    assert data.get('correction_checks',EXPECTED_CORRECTION)==EXPECTED_CORRECTION, 'Parent correction regression count mismatch'
    assert data.get('bench_expected_nodes')==EXPECTED_BENCH, 'Exact parent signature must be preregistered'
    return data
