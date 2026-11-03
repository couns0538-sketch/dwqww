"""Cross-check actual source lines, not just self-consistent profile metadata."""
import hashlib
import json
from pathlib import Path

import chess
import pytest

import audit_raw_labels as audit
import profile_corpus as profile
import report_corpus as report


def prepare(tmp_path, monkeypatch):
    source=tmp_path/'forge_selfplay_003.txt'
    monkeypatch.setattr(report,'EXPECTED_SOURCES',{source.name})
    values=[('w',100,'1'),('b',-100,'1'),('w',-100,'0'),('b',100,'0'),
            ('w',0,'0.5'),('b',0,'0.5'),('w',50,'?'),('b',-50,'?')]
    source.write_text(''.join(chess.STARTING_FEN.replace(' w ',' '+turn+' ')+f' | {score} | {result}\n'
                              for turn,score,result in values))
    Path(str(source)+'.md5').write_text(hashlib.md5(source.read_bytes()).hexdigest()+'  '+source.name+'\n')
    output=tmp_path/'profile'
    profile.run(profile.freeze_plan([source]),output,mirror_stride=1)
    return output/'SUMMARY.json'


def test_actual_selected_source_labels_and_full_fens_match(tmp_path,monkeypatch):
    path=prepare(tmp_path,monkeypatch)
    result=audit.audit_reservoirs([path],tmp_path/'audit')
    assert result['rows']==8 and result['training_ready'] is False
    rows=[json.loads(line) for line in (tmp_path/'audit/audit_reservoir.jsonl').read_text().splitlines()]
    assert [row['result_stm'] for row in rows]==[1,-1,-1,1,0,0,None,None]
    assert result['sources'][0]['source_lines']==8
    with pytest.raises(FileExistsError):audit.audit_reservoirs([path],tmp_path/'audit')


@pytest.mark.parametrize('damage',['score','white','stm','bool_white','bool_stm',
                                  'float_score','float_white','float_stm','full_fen','source_row'])
def test_rehashed_but_false_reservoir_is_rejected(tmp_path,monkeypatch,damage):
    path=prepare(tmp_path,monkeypatch)
    sample=path.with_name('000.sample.jsonl')
    rows=[json.loads(line) for line in sample.read_text().splitlines()]
    if damage=='score':rows[0]['score_stm']=-100
    elif damage=='white':rows[0]['result_white']=-1
    elif damage=='stm':rows[0]['result_stm']=-1
    elif damage=='bool_white':rows[0]['result_white']=True
    elif damage=='bool_stm':rows[0]['result_stm']=True
    elif damage=='float_score':rows[0]['score_stm']=100.0
    elif damage=='float_white':rows[0]['result_white']=1.0
    elif damage=='float_stm':rows[0]['result_stm']=1.0
    elif damage=='full_fen':rows[0]['fen']=rows[0]['fen'].replace(' 0 1',' 1 1')
    else:rows[0]['source_row']=100
    sample.write_text(''.join(json.dumps(row)+'\n' for row in rows))
    summary=json.loads(path.read_text())
    summary['sources'][0]['sample_sha256']=audit.sha256(sample)
    path.with_name('000.json').write_text(json.dumps(summary['sources'][0]))
    path.write_text(json.dumps(summary))
    with pytest.raises(ValueError):audit.audit_reservoirs([path],tmp_path/'audit')
    assert not (tmp_path/'audit').exists()
