"""Do not let the PGN library invent or repair original FEN state."""
import io

import chess
import pytest

from records import read_pgn_game, read_records
from filter_positions import run_filter
from test_integrity_regressions import converter, pgn_fixture


BASE = '4k3/8/8/8/8/8/4P3/4K3 w - -'
BAD_FENS = [
    BASE,
    BASE + ' 0',
    BASE + ' 0 0',
    BASE + ' 1_0 81',
    BASE + ' 0 \uff11',
    BASE.replace(' w ', '\u00a0w ') + ' 0 1',
    BASE + ' 0 9223372036854775808',
    '4k3/8/8/8/8/8/4P~3/4K3 w - - 0 1',
]


def text(fen):
    return f'[SetUp "1"]\n[FEN "{fen}"]\n[Result "1-0"]\n\n1. e4 {{+0.20/12}} 1-0\n'


@pytest.mark.parametrize('fen', BAD_FENS)
def test_raw_fen_header_rejected_before_normalization(fen):
    with pytest.raises(ValueError, match='original .*FEN'):
        read_pgn_game(io.StringIO(text(fen)))


@pytest.mark.parametrize('consumer', ['reader', 'filter', 'result_converter'])
def test_missing_header_counters_never_publish(tmp_path, monkeypatch, consumer):
    source = tmp_path / 'missing-clocks.pgn'
    source.write_text(text(BASE), encoding='utf-8')
    output = tmp_path / 'output'
    with pytest.raises(ValueError, match='original .*FEN'):
        if consumer == 'reader':
            list(read_records(source, 'pgn'))
        elif consumer == 'filter':
            run_filter(source, output, kind='pgn')
        else:
            converter(source, output, monkeypatch)
    assert not output.exists()


@pytest.mark.parametrize('consumer', ['reader', 'filter', 'result_converter'])
def test_setup_requires_the_declared_initial_position(tmp_path, monkeypatch, consumer):
    source = tmp_path / 'missing-position.pgn'
    source.write_text('[SetUp "1"]\n[Result "1-0"]\n\n1. e4 {+0.20/12} 1-0\n',
                      encoding='utf-8')
    output = tmp_path / 'output'
    with pytest.raises(ValueError, match='original .*FEN'):
        if consumer == 'reader':
            list(read_records(source, 'pgn'))
        elif consumer == 'filter':
            run_filter(source, output, kind='pgn')
        else:
            converter(source, output, monkeypatch)
    assert not output.exists()


def test_setup_zero_without_fen_is_normal_start():
    game = read_pgn_game(io.StringIO('[SetUp "0"]\n[Result "*"]\n\n1. e4 *\n'))
    assert game.board().fen() == chess.STARTING_FEN


@pytest.mark.parametrize('fen', [None, BASE + ' 17 81', BASE + '\t+17\t+81'])
def test_genuinely_known_initial_state_preserved(tmp_path, fen):
    source = tmp_path / 'valid.pgn'
    source.write_text(text(fen) if fen else '[Result "1-0"]\n\n1. e4 {+0.20/12} 1-0\n',
                      encoding='utf-8')
    rows = list(read_records(source, 'pgn'))
    expected = chess.Board(fen).fen(en_passant='fen') if fen else chess.STARTING_FEN
    assert len(rows) == 1 and rows[0]['fen'] == expected
    assert rows[0]['ply'] == (160 if fen else 0)
    report = run_filter(source, tmp_path / 'valid-output', kind='pgn')
    assert report['kept'] == 1


def test_later_game_raw_header_is_checked(tmp_path):
    source = tmp_path / 'later.pgn'
    source.write_text('[Result "1-0"]\n\n1. e4 {+0.20/12} 1-0\n\n' + text(BASE),
                      encoding='utf-8')
    rows = read_records(source, 'pgn')
    assert next(rows)['fen'] == chess.STARTING_FEN
    with pytest.raises(ValueError, match='original .*FEN'):
        next(rows)


def test_legacy_converter_does_not_enter_result_header_validation(tmp_path, monkeypatch):
    import records
    source = pgn_fixture(tmp_path / 'legacy.pgn')
    def reject(_):
        raise AssertionError('result-aware validator must not run in legacy mode')
    monkeypatch.setattr(records, 'read_pgn_game', reject)
    converter(source, tmp_path / 'legacy-output', monkeypatch, keep_result=False)
    assert (tmp_path / 'legacy-output/train.bin').exists()
