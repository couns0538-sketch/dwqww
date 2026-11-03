"""Forge's necessary promotion-inventory constraint at data admission."""
import json

import chess
import pytest

from records import board_from_fen, record


CASES = [
    ('4k3/8/8/8/8/QQQ5/PPPPPPPP/4K3 w - - 0 1',
     '4k3/8/8/8/8/QQQ5/PPPPPP2/4K3 w - - 0 1'),
    ('4k3/8/8/8/8/RRR5/PPPPPPPP/4K3 w - - 0 1',
     '4k3/8/8/8/8/RRR5/PPPPPPP1/4K3 w - - 0 1'),
    ('4k3/8/8/8/8/BBB5/PPPPPPPP/4K3 w - - 0 1',
     '4k3/8/8/8/8/BBB5/PPPPPPP1/4K3 w - - 0 1'),
    ('4k3/8/8/8/8/NNN5/PPPPPPPP/4K3 w - - 0 1',
     '4k3/8/8/8/8/NNN5/PPPPPPP1/4K3 w - - 0 1'),
    ('7k/8/8/8/8/QQRRR3/PPPPPPP1/4K3 w - - 0 1',
     '7k/8/8/8/8/QQRRR3/PPPPPP2/4K3 w - - 0 1'),
]


def orient(fen, mirror):
    return chess.Board(fen).mirror().fen(en_passant='fen') if mirror else fen


@pytest.mark.parametrize('bad,good', CASES)
@pytest.mark.parametrize('mirror', [False, True])
def test_impossible_promoted_material_cannot_be_published(tmp_path, bad, good, mirror):
    from filter_positions import run_filter
    row = record(orient(good, mirror), 20, 'cp', 1, 'fixture', 1, 'selfplay')
    row['fen'] = orient(bad, mirror)
    source = tmp_path/'impossible.jsonl'
    source.write_text(json.dumps(row)+'\n', encoding='utf-8')
    with pytest.raises(ValueError, match='material'):
        run_filter(source, tmp_path/'filtered')
    assert not (tmp_path/'filtered').exists()


@pytest.mark.parametrize('bad,good', CASES)
@pytest.mark.parametrize('mirror', [False, True])
def test_exact_missing_pawn_budget_allows_promotions(bad, good, mirror):
    fen = orient(good, mirror)
    assert board_from_fen(fen).is_valid()
    assert record(fen, 20, 'cp', 1, 'fixture', 1, 'selfplay')['fen'] == fen


def test_native_probe_rejects_impossible_material_before_launch(tmp_path, monkeypatch):
    import native_forge_smoke as smoke
    monkeypatch.setattr(smoke, 'sha256', lambda path: smoke.LOCK)
    sample = tmp_path/'sample.jsonl'
    sample.write_text(json.dumps({'fen': CASES[0][0]})+'\n', encoding='utf-8')
    def refuse(*args, **kwargs):
        raise AssertionError('impossible material reached the engine')
    monkeypatch.setattr(smoke.subprocess, 'run', refuse)
    with pytest.raises(ValueError, match='material'):
        smoke.run(tmp_path/'native', sample)
