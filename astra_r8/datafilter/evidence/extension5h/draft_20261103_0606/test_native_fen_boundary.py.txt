"""Forge-valid text must not reach the installed native parser ambiguously."""
from copy import deepcopy

import chess
import pytest

from records import record


def row(fen):
    return record(fen,20,'cp',None,'native-boundary-fixture',1,'selfplay')


@pytest.mark.parametrize('turn',['w','b'])
@pytest.mark.parametrize('spacing',[pytest.param('  ',id='spaces'),
                                  pytest.param('\t',id='tabs'),
                                  pytest.param(' \t ',id='mixed')])
def test_native_features_match_canonical_fen_without_changing_metadata(turn,spacing):
    import npt_adapter as adapter
    canonical=chess.STARTING_FEN.replace(' w ',f' {turn} ')
    original=canonical.replace(' ',spacing)
    before=row(original)
    reference=adapter.make_batch([row(canonical)],'K32H3','filtered_eval_v1')
    actual=adapter.make_batch([before],'K32H3','filtered_eval_v1')
    assert all(adapter.torch.equal(a,b) for a,b in zip(actual[:8],reference[:8]))
    assert actual[8]['fen']==[original] and before['fen']==original


def test_native_argument_canonicalizes_spacing_and_decimal_clocks(monkeypatch):
    import npt_adapter as adapter
    fen='4k3/8/8/3pP3/8/8/8/4K3\tw\t-\td6\t+000\t+081'
    candidate=row(fen)
    before=deepcopy(candidate)
    captured=[]
    def no_batch(feature,fens,scores,plies,results):
        captured.extend(fens)
        return None
    monkeypatch.setattr(adapter.data_loader,'get_sparse_batch_from_fens',no_batch)
    with pytest.raises(ValueError,match='unavailable'):
        adapter.make_batch([candidate],'K32H3','filtered_eval_v1')
    assert captured==['4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 81']
    assert candidate==before


@pytest.mark.parametrize('turn,halfmove,fullmove',[
    ('w',256,1),('b',256,1),('w',2**31,1),('b',2**63-1,1),
    ('b',0,32768),('w',0,32769),('b',0,32769)])
def test_unrepresentable_native_clocks_rejected_before_allocation(monkeypatch,turn,halfmove,fullmove):
    import npt_adapter as adapter
    fen=' '.join(chess.STARTING_FEN.split()[:1]+[turn,'KQkq','-',str(halfmove),str(fullmove)])
    candidate=row(fen)
    calls=[]
    def refuse(*args):
        calls.append(args)
        raise AssertionError('unrepresentable native FEN reached the C ABI')
    monkeypatch.setattr(adapter.data_loader,'get_sparse_batch_from_fens',refuse)
    with pytest.raises(ValueError,match='native'):
        adapter.make_batch([candidate],'K32H3','filtered_eval_v1')
    assert not calls


@pytest.mark.parametrize('turn,fullmove',[('w',32768),('b',32767)])
def test_maximum_representable_native_clocks_pass_admission(monkeypatch,turn,fullmove):
    import npt_adapter as adapter
    fen=' '.join(chess.STARTING_FEN.split()[:1]+[turn,'KQkq','-','255',str(fullmove)])
    candidate=row(fen)
    captured=[]
    def no_batch(feature,fens,scores,plies,results):
        captured.append((fens,plies))
        return None
    monkeypatch.setattr(adapter.data_loader,'get_sparse_batch_from_fens',no_batch)
    with pytest.raises(ValueError,match='unavailable'):
        adapter.make_batch([candidate],'K32H3','filtered_eval_v1')
    assert captured==[([fen],[candidate['ply']])]


def test_later_invalid_row_prevents_the_whole_native_batch(monkeypatch):
    import npt_adapter as adapter
    good=row(chess.STARTING_FEN)
    invalid=row(chess.STARTING_FEN.rsplit(' ',2)[0]+' 256 1')
    calls=[]
    def refuse(*args):
        calls.append(args)
        raise AssertionError('partially valid batch reached the C ABI')
    monkeypatch.setattr(adapter.data_loader,'get_sparse_batch_from_fens',refuse)
    with pytest.raises(ValueError,match='native'):
        adapter.make_batch([good,invalid],'K32H3','filtered_eval_v1')
    assert not calls
