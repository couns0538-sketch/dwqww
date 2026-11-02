import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from records import dumps
from test_adapter import rows
import pytest

def test_explicit_holdout_selection_preserves_order_and_duplicates(tmp_path):
    from clear_holdouts import write_selection
    r=rows()
    source=tmp_path/'rows.jsonl'; source.write_text('\n'.join(map(dumps,[r[0],r[1],r[1],r[2]]))+'\n')
    # Both White rows match by board+turn despite differing source and score.
    blocked={' '.join(r[0]['fen'].split()[:2])}
    output=tmp_path/'selected'
    report=write_selection(source,output,blocked)
    assert report['input']==4 and report['kept']==2 and report['holdout_excluded']==2
    kept=[json.loads(x) for x in (output/'records.jsonl').read_text().splitlines()]
    assert kept==[r[1],r[1]]
    assert (output/'records.jsonl').read_bytes()==(output/'metadata.jsonl').read_bytes()

def test_missing_complete_holdouts_fail_before_publication(tmp_path):
    from clear_holdouts import run
    from filter_positions import sha256
    (tmp_path/'independent_audit').mkdir(); (tmp_path/'filtered_default').mkdir()
    source=tmp_path/'filtered_default/records.jsonl'; source.write_text(dumps(rows()[0])+'\n')
    (tmp_path/'filtered_default/report.json').write_text(json.dumps({'hashes':{'records.jsonl':sha256(source)}}))
    (tmp_path/'independent_audit/audit.json').write_text(json.dumps({'holdouts':[]}))
    with pytest.raises(ValueError,match='holdout'):
        run(tmp_path)
    assert not (tmp_path/'holdout_cleared').exists()

def test_changed_source_stays_unpublished(tmp_path,monkeypatch):
    import clear_holdouts as c
    from filter_positions import sha256
    (tmp_path/'independent_audit').mkdir(); (tmp_path/'filtered_default').mkdir()
    source=tmp_path/'filtered_default/records.jsonl'; source.write_text(dumps(rows()[0])+'\n')
    (tmp_path/'filtered_default/report.json').write_text(json.dumps({'hashes':{'records.jsonl':sha256(source)}}))
    holds=[]; pins={}
    for shard in ('013','014'):
        p=tmp_path/f'{shard}.txt'; p.write_text(rows()[1]['fen']+' | 0 | 0.5\n')
        digest=sha256(p); pins[shard]=(digest,1)
        holds.append(dict(shard=shard,path=str(p),sha256=digest,rows=1,complete_scan=True))
    (tmp_path/'independent_audit/audit.json').write_text(json.dumps({'holdouts':holds}))
    monkeypatch.setattr(c,'EXPECTED_HOLDOUTS',pins)
    original=c.write_selection
    def changed(*args,**kwargs):
        source.write_text(dumps(rows()[2])+'\n')
        return original(*args,**kwargs)
    monkeypatch.setattr(c,'write_selection',changed)
    with pytest.raises(ValueError,match='source changed'):
        c.run(tmp_path)
    assert not (tmp_path/'holdout_cleared').exists()
    assert (tmp_path/'holdout_cleared.partial').exists()
