"""Training input must not silently recover another variant or damaged PGN."""
import io
import random

import chess
import chess.pgn
import pytest

from records import read_pgn_game, read_records


@pytest.mark.parametrize('variant', ['Chess960', 'Atomic', 'Suicide', 'Three-check', 'Crazyhouse'])
def test_nonstandard_pgn_rejected(variant):
    text = f'[Variant "{variant}"]\n[Result "1-0"]\n\n1. e4 {{+0.20/12}} 1-0\n'
    with pytest.raises(ValueError, match='standard chess'):
        read_pgn_game(io.StringIO(text))


@pytest.mark.parametrize('header', [
    '[Result "0-1"]\n[Result "1-0"]',
    '[Variant "Atomic"]\n[Variant "Standard"]',
    '[SetUp "0"]\n[SetUp "1"]',
    f'[FEN "{chess.STARTING_FEN}"]\n[FEN "4k3/8/8/8/8/8/8/4K3 w - - 0 1"]',
])
def test_conflicting_semantic_headers_rejected(header):
    with pytest.raises(ValueError, match='conflicting PGN header'):
        read_pgn_game(io.StringIO(header + '\n\n1. e4 {+0.20/12} 1-0\n'))


@pytest.mark.parametrize('movetext', [
    '1. e4 {+0.20/12',
    '1. e4 {+0.20/12} totally_broken 1-0',
    '1. e4 {+0.20/12} (1. d4 1-0',
    '1. e4 {+0.20/12} ) 1-0',
    '1. e4 {+0.20/12} } 1-0',
    '1. e4 {+0.20/12}',
    '1. e4 {+0.20/12} 1-0 e5',
    '1. e4 {+0.20/12} -- 1-0',
    '1. e44 {+0.20/12} 1-0',
    '1. ed4 {+0.20/12} 1-0',
])
def test_structurally_damaged_pgn_rejected(movetext):
    with pytest.raises(ValueError, match='PGN'):
        read_pgn_game(io.StringIO('[Result "1-0"]\n\n' + movetext + '\n'))


@pytest.mark.parametrize('header', [
    '[Result "1-0"', '[Result "1-0"] trailing', '[Result 1-0]',
])
def test_malformed_header_rejected(header):
    with pytest.raises(ValueError, match='PGN'):
        read_pgn_game(io.StringIO(header + '\n\n1. e4 {+0.20/12} 1-0\n'))


def test_multiline_comments_variations_annotations_and_multiple_games():
    text = ('\ufeff% export note\n[Event "quote \\\"name\\\""]\n[Variant "Standard"]\n'
            '[Result "1/2-1/2"]\n\n1.e4! {+0.20/12\nother notes}\n'
            '(1.d4 d5 $1) 1...e5?! ; line note\n2.Nf3 Nc6 1/2-1/2\n\n'
            '[Result "*"]\n\n1.d4 {+0.20/12} *\n')
    fh = io.StringIO(text)
    first = read_pgn_game(fh)
    second = read_pgn_game(fh)
    assert first.headers['Result'] == '1/2-1/2'
    assert list(first.mainline_moves()) == [chess.Move.from_uci(s) for s in ('e2e4', 'e7e5', 'g1f3', 'b8c6')]
    assert second.headers['Result'] == '*'
    assert read_pgn_game(fh) is None


def test_bad_later_game_does_not_hide_an_earlier_label(tmp_path):
    source = tmp_path / 'two.pgn'
    source.write_text('[Result "1-0"]\n\n1.e4 {+0.20/12} 1-0\n\n'
                      '[Result "0-1"]\n\n1.d4 {+0.20/12} broken 0-1\n')
    rows = read_records(source, 'pgn')
    assert next(rows)['result_white'] == 1
    with pytest.raises(ValueError, match='PGN'):
        list(rows)


def test_legal_export_roundtrip_including_variations():
    rng = random.Random(5108)
    for index in range(32):
        game = chess.pgn.Game()
        game.headers['Result'] = '*'
        board = game.board()
        node = game
        expected = []
        for ply in range(64):
            if board.is_game_over():
                break
            legal = list(board.legal_moves)
            move = rng.choice(legal)
            parent = node
            node = parent.add_main_variation(move)
            node.comment = f'+0.20/12 synthetic fixture {index}:{ply}'
            if ply % 16 == 0 and len(legal) > 1:
                alternative = next(m for m in legal if m != move)
                parent.add_variation(alternative).comment = 'variation note'
            expected.append(move)
            board.push(move)
        parsed = read_pgn_game(io.StringIO(str(game) + '\n'))
        assert list(parsed.mainline_moves()) == expected
        assert parsed.end().board().fen(en_passant='fen') == board.fen(en_passant='fen')


@pytest.mark.parametrize('fen,move', [
    ('r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1', 'e1g1'),
    ('r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1', 'e8c8'),
    ('4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 81', 'e5d6'),
    ('4k3/P7/8/8/8/8/8/4K3 w - - 0 81', 'a7a8q'),
    ('4k3/P7/8/8/8/8/8/4K3 w - - 0 81', 'a7a8n'),
])
def test_standard_special_moves_preserved(fen, move):
    board = chess.Board(fen)
    game = chess.pgn.Game.from_board(board)
    game.add_main_variation(chess.Move.from_uci(move))
    parsed = read_pgn_game(io.StringIO(str(game) + '\n'))
    assert parsed.board().fen(en_passant='fen') == fen
    assert next(iter(parsed.mainline_moves())).uci() == move


def test_result_converter_rejects_invalid_utf8(tmp_path, monkeypatch):
    from test_integrity_regressions import pgn_fixture, converter
    source = pgn_fixture(tmp_path / 'damaged.pgn')
    source.write_bytes(source.read_bytes().replace(b'/12}', b'/12\xff}', 1))
    with pytest.raises(UnicodeDecodeError):
        converter(source, tmp_path / 'out', monkeypatch)
    assert not (tmp_path / 'out').exists()
