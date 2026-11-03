"""Malformed provenance and optional fields must not become trusted labels."""
import json

import chess
import pytest

from records import record, validate_record, read_records


def row():
    return record(chess.STARTING_FEN, 20, 'cp', 1, 'fixture', 1, 'selfplay')


@pytest.mark.parametrize('field,value', [
    ('depth', True), ('depth', -1), ('depth', '12'), ('depth', 1.5),
    ('raw_score', True), ('raw_score', {}), ('raw_score', []), ('raw_score', ''),
    ('raw_score', '  '), ('raw_score', None), ('source', '  '),
    ('source_row', ' '), ('source_row', '0'), ('source_row', '0:2'),
    ('source_row', '1:-1'), ('source_row', 'garbage'),
    ('fen', None), ('fen', []), ('best_move', 123),
    ('fen', chess.STARTING_FEN.replace(' w ', '\nw ')),
    ('fen', chess.STARTING_FEN.replace(' w ', '\rw ')),
    ('fen', chess.STARTING_FEN.replace(' w ', '\r\nw ')),
])
def test_malformed_normalized_metadata_rejected(field, value):
    candidate = row()
    candidate[field] = value
    with pytest.raises(ValueError):
        validate_record(candidate)


def test_lichess_eval_cannot_claim_game_result():
    candidate = row()
    candidate['source_kind'] = 'lichess'
    with pytest.raises(ValueError, match='result'):
        validate_record(candidate)


@pytest.mark.parametrize('source_row', [1, '1', '1:0', '2:128', '0001:0000'])
def test_valid_provenance_and_optional_depth_preserved(source_row):
    candidate = record(chess.STARTING_FEN, 20, 'cp', None, 'fixture', source_row,
                       'pgn', raw_score='+0.20/12 note', depth=12)
    assert validate_record(candidate) is candidate
    assert candidate['source_row'] == source_row and candidate['depth'] == 12


def test_unknown_input_kind_refused(tmp_path):
    source = tmp_path/'rows.jsonl'
    source.write_text(json.dumps(row())+'\n')
    with pytest.raises(ValueError, match='kind'):
        list(read_records(source, 'typo'))


def test_type_error_includes_source_line(tmp_path):
    candidate = row()
    candidate['fen'] = []
    source = tmp_path/'rows.jsonl'
    source.write_text(json.dumps(candidate)+'\n')
    with pytest.raises(ValueError, match='rows.jsonl:1:'):
        list(read_records(source))


def test_multiline_fen_never_becomes_a_published_filter_output(tmp_path):
    from filter_positions import run_filter
    candidate = row()
    candidate['fen'] = candidate['fen'].replace(' w ', '\nw ')
    source = tmp_path/'multiline.jsonl'
    source.write_text(json.dumps(candidate)+'\n')
    with pytest.raises(ValueError, match='multiline.jsonl:1:'):
        run_filter(source, tmp_path/'filtered')
    assert not (tmp_path/'filtered').exists()


def test_multiline_lichess_fen_cannot_reach_native_consumer():
    from records import lichess_record
    candidate = {'fen': chess.STARTING_FEN.replace(' w ', '\nw '),
                 'evals': [{'pvs': [{'cp': 20}]}]}
    with pytest.raises(ValueError):
        lichess_record(candidate, 'fixture', 1)


@pytest.mark.parametrize('fen', [
    chess.STARTING_FEN.replace(' w ', '\u00a0w '),
    chess.STARTING_FEN.replace(' w ', '\u2003w '),
    chess.STARTING_FEN.replace(' w ', '\x1fw '),
    chess.STARTING_FEN[:-1] + '\u0661',
    chess.STARTING_FEN.replace('KQkq', 'HAha'),
    '8/8/8/8/8/6k1/8/KR~6 w - - 0 1',
    chess.STARTING_FEN[:-1] + '1_0',
    chess.STARTING_FEN[:-1] + str(2**63),
    chess.STARTING_FEN.rsplit(' ', 2)[0] + ' ' + str(2**63) + ' 1',
])
def test_non_uci_fen_text_never_becomes_published_data(tmp_path, fen):
    from filter_positions import run_filter
    candidate = row()
    candidate['fen'] = fen
    board = chess.Board(fen)
    candidate['ply'] = 2 * (board.fullmove_number - 1) + (not board.turn)
    source = tmp_path/'non_uci.jsonl'
    source.write_text(json.dumps(candidate)+'\n', encoding='utf-8')
    with pytest.raises(ValueError, match='non_uci.jsonl:1:'):
        run_filter(source, tmp_path/'filtered')
    assert not (tmp_path/'filtered').exists()


def test_ascii_spacing_preserved_at_admission():
    fen = chess.STARTING_FEN.replace(' w ', '  w\t')
    assert record(fen, 20, 'cp', 1, 'fixture', 1, 'selfplay')['fen'] == fen


@pytest.mark.parametrize('rights', ['KK', 'QQ', 'kk', 'qq'])
def test_duplicate_castling_letters_rejected(rights):
    fen = 'r3k2r/8/8/8/8/8/8/R3K2R w ' + rights + ' - 0 1'
    with pytest.raises(ValueError):
        record(fen, 20, 'cp', 1, 'fixture', 1, 'selfplay')
