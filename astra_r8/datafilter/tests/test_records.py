import sys
from pathlib import Path
import chess
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def test_result_orientation_and_unknown():
    from records import selfplay_record
    for turn in ('w', 'b'):
        fen = chess.STARTING_FEN.replace(' w ', f' {turn} ')
        for raw, white in [('0', -1), ('0.5', 0), ('1', 1), ('?', None)]:
            r = selfplay_record(f'{fen} | 42 | {raw}', 'fixture', 7)
            assert r['result_stm'] == (None if white is None else white * (1 if turn == 'w' else -1))
            assert r['has_result'] == (white is not None)
            assert r['fen'] == fen
            assert r['ply'] == (turn == 'b')
            assert r['score_stm'] == 42
            assert r['source_row'] == 7

def test_bad_result_fails():
    from records import selfplay_record
    with pytest.raises(ValueError, match='result'):
        selfplay_record(f'{chess.STARTING_FEN} | 0 | 0.7', 'fixture', 1)

def test_lichess_result_is_unknown():
    from records import lichess_record
    r = lichess_record({'fen': chess.STARTING_FEN, 'evals': [{'pvs': [{'cp': 22, 'line': 'e2e4 e7e5'}]}]}, 'fixture', 1)
    assert r['has_result'] is False and r['result_stm'] is None
    assert r['best_move'] == 'e2e4'

@pytest.mark.parametrize('kind,score', [('forge-typo', 32000), ('selfplay', True), ('selfplay', 0.5)])
def test_invalid_source_score(kind, score):
    from records import record
    with pytest.raises(ValueError):
        record(chess.STARTING_FEN, score, 'cp', None, 'fixture', 1, kind)

def test_invalid_pgn_result(tmp_path):
    from records import read_records
    p = tmp_path / 'bad.pgn'
    p.write_text('[Result "nonsense"]\n\n1. e4 {+0.1/12} *\n')
    with pytest.raises(ValueError, match='result'):
        list(read_records(p, 'pgn'))
