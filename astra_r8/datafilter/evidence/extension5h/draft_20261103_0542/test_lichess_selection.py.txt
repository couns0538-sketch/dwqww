"""Synthetic full-state Lichess evaluations; no public corpus is imported."""
from copy import deepcopy
import json

import chess
import pytest

from records import dumps, lichess_record, read_records, validate_record

CASTLING='r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 7 42'


def evaluation(cp=20,depth=12,line='e2e4'):
    return {'depth':depth,'pvs':[{'cp':cp,'line':line}]}


def source(evals=None,fen=chess.STARTING_FEN):
    return {'fen':fen,'evals':[evaluation()] if evals is None else evals}


def test_deepest_entry_and_first_pv_selected_with_provenance():
    shallow=evaluation(10,depth=10)
    shallow['pvs'].append({'cp':9,'line':'d2d4'})
    deep=evaluation(30,depth=30,line='g1f3')
    deep['pvs'].append({'cp':29,'line':'d2d4'})
    row=lichess_record(source([shallow,deep]),'fixture',1)
    assert row['score_stm']==30 and row['depth']==30 and row['best_move']=='g1f3'
    assert row['lichess_eval_index']==1 and row['lichess_raw_best_move']=='g1f3'
    assert row['lichess_move_format']=='uci_chess960'
    assert row['result_white'] is row['result_stm'] is None and row['has_result'] is False
    assert validate_record(row) is row


def test_equal_depth_prefers_earliest_entry():
    row=lichess_record(source([evaluation(15),evaluation(25)]),'fixture',1)
    assert row['raw_score']==15 and row['lichess_eval_index']==0


def test_unknown_depth_is_retained_and_ranks_below_known_zero():
    unknown=evaluation(99);unknown.pop('depth')
    row=lichess_record(source([unknown]),'fixture',1)
    assert row['depth'] is None
    selected=lichess_record(source([unknown,evaluation(20,depth=0)]),'fixture',1)
    assert selected['depth']==0 and selected['lichess_eval_index']==1


@pytest.mark.parametrize('turn,raw,canonical',[
    ('w','e1h1','e1g1'),('w','e1a1','e1c1'),
    ('b','e8h8','e8g8'),('b','e8a8','e8c8')])
def test_castling_notation_normalized_without_chess960_rules(turn,raw,canonical):
    fen=CASTLING.replace(' w ',f' {turn} ')
    row=lichess_record(source([evaluation(20,line=raw)],fen),'fixture',1)
    assert row['fen']==fen and row['best_move']==canonical
    assert row['lichess_raw_best_move']==raw
    assert row['ply']==82+(turn=='b') and row['has_result'] is False
    assert validate_record(row) is row
    from filter_positions import matches
    assert matches(row)[1] is False


@pytest.mark.parametrize('fen,move',[
    (CASTLING.replace('KQkq','-'),'e1h1'),
    (CASTLING.replace('R3K2R','R3KB1R'),'e1h1'),
    ('r3k2r/8/8/8/8/5r2/8/R3K2R w KQkq - 7 42','e1h1'),
    (CASTLING,'e1b1'),(CASTLING,'0000')])
def test_illegal_castling_and_null_moves_rejected(fen,move):
    with pytest.raises(ValueError):
        lichess_record(source([evaluation(line=move)],fen),'fixture',1)


@pytest.mark.parametrize('kind,score',[('cp',123),('cp',-123),('mate',3),('mate',-3)])
@pytest.mark.parametrize('turn',['w','b'])
def test_white_relative_score_becomes_stm_with_unknown_result(kind,score,turn):
    item={'depth':12,'pvs':[{kind:score}]}
    fen=chess.STARTING_FEN.replace(' w ',f' {turn} ')
    row=lichess_record(source([item],fen),'fixture',1)
    assert row['raw_score']==score and row['score_type']==kind
    assert row['score_stm']==score*(1 if turn=='w' else -1)
    assert row['best_move'] is None and row['lichess_raw_best_move'] is None
    assert row['has_result'] is False and row['result_stm'] is None


@pytest.mark.parametrize('value',[True,-1,1.5,'12',{},[]])
def test_invalid_depth_rejected_even_when_another_entry_is_deeper(value):
    with pytest.raises(ValueError,match='depth'):
        lichess_record(source([evaluation(depth=20),evaluation(depth=value)]),'fixture',1)


@pytest.mark.parametrize('pv',[{'cp':1,'mate':2},{},{'cp':True},{'cp':1.5},
    {'mate':'3'},{'cp':1,'line':None},{'cp':1,'line':[]},None])
def test_malformed_selected_pv_is_rejected(pv):
    with pytest.raises(ValueError):
        lichess_record(source([{'depth':10,'pvs':[pv]}]),'fixture',1)


@pytest.mark.parametrize('evals',[[],{},None,[None],[{}],[{'pvs':[]}],
    [{'pvs':None}],[{'pvs':{}}]])
def test_malformed_evaluation_list_rejected(evals):
    with pytest.raises(ValueError):
        lichess_record({'fen':chess.STARTING_FEN,'evals':evals},'fixture',1)


def test_four_field_fen_explains_missing_counters_without_synthesizing():
    fen=' '.join(chess.STARTING_FEN.split()[:4])
    with pytest.raises(ValueError,match='counters'):
        lichess_record(source(fen=fen),'fixture',1)


@pytest.mark.parametrize('field,value',[('lichess_eval_index',True),('lichess_eval_index',-1),
    ('lichess_move_format','uci'),('lichess_raw_best_move','d2d4'),
    ('lichess_raw_best_move','0000'),('lichess_raw_best_move',None)])
def test_normalized_lichess_provenance_tampering_rejected(field,value):
    row=lichess_record(source(),'fixture',1)
    row[field]=value
    with pytest.raises(ValueError):validate_record(row)


def test_incomplete_new_provenance_rejected_but_legacy_record_accepted():
    row=lichess_record(source(),'fixture',1)
    new_fields={'lichess_eval_index','lichess_raw_best_move','lichess_move_format'}
    legacy={key:value for key,value in row.items() if key not in new_fields}
    assert validate_record(legacy) is legacy
    incomplete=deepcopy(row);incomplete.pop('lichess_eval_index')
    with pytest.raises(ValueError):validate_record(incomplete)
    row['source_kind']='selfplay'
    with pytest.raises(ValueError):validate_record(row)


def test_filter_preserves_castling_and_selection_provenance(tmp_path):
    from filter_positions import run_filter
    inp=tmp_path/'lichess.jsonl'
    inp.write_text(json.dumps(source([evaluation(line='e1h1')],CASTLING))+'\n')
    report=run_filter(inp,tmp_path/'filtered',kind='lichess',drop_capture_bestmove=True)
    assert report['input']==report['kept']==1 and report['coverage']['result']==0
    result=list(read_records(tmp_path/'filtered/records.jsonl'))
    assert result[0]['best_move']=='e1g1' and result[0]['lichess_raw_best_move']=='e1h1'
    assert (tmp_path/'filtered/metadata.jsonl').read_bytes()==(tmp_path/'filtered/records.jsonl').read_bytes()
    assert (tmp_path/'filtered/records.jsonl').read_text()==dumps(result[0])+'\n'


def test_malformed_lichess_is_reported_with_source_line_and_never_published(tmp_path):
    from filter_positions import run_filter
    inp=tmp_path/'bad.jsonl'
    bad=source();bad['evals'][0]['pvs'][0]['line']=None
    inp.write_text(json.dumps(source())+'\n'+json.dumps(bad)+'\n')
    with pytest.raises(ValueError,match='bad.jsonl:2:'):
        run_filter(inp,tmp_path/'filtered',kind='lichess')
    assert not (tmp_path/'filtered').exists()
