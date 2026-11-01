import json
import sys
from pathlib import Path
import chess
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from records import record, dumps

def fixture(fen, move=None, score=0, kind='cp'):
    return record(fen, score, kind, None, 'fixture', 1, 'selfplay', move)

def test_rules_and_boundary():
    from filter_positions import matches
    quiet = fixture(chess.STARTING_FEN, 'e2e4')
    check = fixture('4k3/8/8/8/8/8/4r3/4K3 w - - 0 1', 'e1e2')
    ep = fixture('4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 81', 'e5d6')
    promo = fixture('4k3/P7/8/8/8/8/8/4K3 w - - 0 81', 'a7a8q')
    assert matches(quiet, 160) == (False, False, False, False)
    assert matches(check, 160)[:2] == (True, True)
    assert matches(ep, 160) == (False, True, False, False)
    assert matches(promo, 159) == (False, True, False, True)
    assert matches(fixture(chess.STARTING_FEN, 'e2e4', 31872), 160)[2]
    assert not matches(fixture(chess.STARTING_FEN, 'e2e4', 31871), 160)[2]
    assert matches(fixture(chess.STARTING_FEN, 'e2e4', 1, 'mate'), 160)[2]

def test_all_off_and_failure_publication(tmp_path):
    from filter_positions import run_filter
    inp = tmp_path / 'in.jsonl'
    rows = [fixture(chess.STARTING_FEN)] * 3
    inp.write_bytes(('\n'.join(map(dumps, rows)) + '\n').encode())
    out = tmp_path / 'out'
    stats = run_filter(inp, out)
    assert stats['kept'] == 3
    assert (out / 'records.jsonl').read_bytes() == inp.read_bytes()
    with pytest.raises(ValueError, match='best.move'):
        run_filter(inp, tmp_path / 'missing', drop_capture_bestmove=True)
    assert not (tmp_path / 'missing').exists()
    with pytest.raises(ValueError, match='unsupported'):
        run_filter(inp, tmp_path / 'qs', drop_qs_unquiet=20)
    assert not (tmp_path / 'qs').exists()
    with pytest.raises(FileExistsError):
        run_filter(inp, out)

def test_overlap_accounting(tmp_path):
    from filter_positions import run_filter
    inp = tmp_path / 'in.jsonl'
    r = fixture('4k3/8/8/8/8/8/4r3/4K3 w - - 0 1', 'e1e2', 32000)
    inp.write_text(dumps(r) + '\n')
    stats = run_filter(inp, tmp_path / 'out', drop_in_check=True, drop_mate_scores=True)
    assert stats['independent']['check'] == stats['independent']['mate'] == 1
    assert stats['first_drop']['check'] == 1 and stats['first_drop']['mate'] == 0
    assert stats['overlap']['check+mate'] == 1

def test_storage_preflight_before_output(tmp_path, monkeypatch):
    import filter_positions as f
    inp = tmp_path / 'in.jsonl'; inp.write_text(dumps(fixture(chess.STARTING_FEN))+'\n')
    def fail(*args, **kwargs):
        raise OSError('disk reserve')
    monkeypatch.setattr(f, 'storage_guard', fail)
    with pytest.raises(OSError, match='reserve'):
        f.run_filter(inp, tmp_path/'out')
    assert not (tmp_path/'out.partial').exists()

@pytest.mark.parametrize('fen,move,score,options', [
    ('4k3/8/8/8/8/8/4r3/4K3 w - - 0 1','e1e2',0,{'drop_in_check':True}),
    ('4k3/8/8/8/8/8/4r3/4K3 w - - 0 1','e1e2',0,{'drop_capture_bestmove':True}),
    ('4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 81','e5d6',0,{'drop_capture_bestmove':True}),
    ('4k3/P7/8/8/8/8/8/4K3 w - - 0 81','a7a8q',0,{'drop_capture_bestmove':True}),
    (chess.STARTING_FEN,'e2e4',31872,{'drop_mate_scores':True}),
    (chess.STARTING_FEN.replace(' 0 1',' 0 81'),'e2e4',0,{'max_ply_from_start':159}),
])
def test_enabled_rule_drops_fixture_and_keeps_quiet(tmp_path,fen,move,score,options):
    from filter_positions import run_filter
    data=[fixture(fen,move,score),fixture(chess.STARTING_FEN,'e2e4')]
    inp=tmp_path/'fixtures.jsonl'; inp.write_text('\n'.join(map(dumps,data))+'\n')
    off=run_filter(inp,tmp_path/'off')
    assert off['kept']==2
    on=run_filter(inp,tmp_path/'on',**options)
    assert on['input']==2 and on['kept']==1 and on['dropped']==1
    assert json.loads((tmp_path/'on/records.jsonl').read_text())['fen']==chess.STARTING_FEN

def test_malformed_later_row_never_publishes(tmp_path):
    from filter_positions import run_filter
    p=tmp_path/'bad.jsonl'; p.write_text(dumps(fixture(chess.STARTING_FEN))+'\n{"fen":"broken"}\n')
    with pytest.raises(ValueError):
        run_filter(p,tmp_path/'out')
    assert not (tmp_path/'out').exists()
