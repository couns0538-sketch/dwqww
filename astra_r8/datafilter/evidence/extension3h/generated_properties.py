"""Original bounded exploratory properties; no installed runtime or dataset writes."""
import io
import json
from pathlib import Path
import sys
import time

ROOT = Path('C:/astra8_data/extension3h_20261103')
HERE = Path('D:/grok-pc-data/dwqww/astra-r8-datafilter/astra_r8/datafilter')
sys.path[:0] = [str(ROOT/'python_tools'), str(HERE)]
import chess
from hypothesis import given, settings, strategies as st
from records import record, validate_record, dumps, board_from_fen, read_pgn_game
from result_codec import encode_result, decode_result
from filter_positions import low_priority, matches, sha256
from resource_policy import storage_guard

SETTINGS = settings(max_examples=400, deadline=None, derandomize=True, database=None)
COUNTS = {}


def counted(name):
    COUNTS[name] = COUNTS.get(name, 0) + 1


@SETTINGS
@given(st.lists(st.integers(0, 4095), min_size=0, max_size=96),
       st.integers(-32000, 32000), st.sampled_from([None, -1, 0, 1]))
def chess_mirror_and_codec(choices, score, result):
    board = chess.Board()
    for choice in choices:
        moves = list(board.legal_moves)
        if not moves:
            break
        board.push(moves[choice % len(moves)])
    moves = list(board.legal_moves)
    move = moves[0] if moves else None
    opposite = board.mirror()
    mirrored_move = (chess.Move(chess.square_mirror(move.from_square),
                               chess.square_mirror(move.to_square), promotion=move.promotion)
                     if move else None)
    row = record(board.fen(en_passant='fen'), score, 'cp', result, 'generated', 1,
                 'selfplay', move.uci() if move else None)
    mirror = record(opposite.fen(en_passant='fen'), score, 'cp',
                    None if result is None else -result, 'generated-mirror', 1,
                    'selfplay', mirrored_move.uci() if mirrored_move else None)
    assert row['result_stm'] == mirror['result_stm']
    assert matches(row)[:3] == matches(mirror)[:3]
    assert validate_record(json.loads(dumps(row))) == row
    assert board_from_fen(row['fen']) == board
    assert decode_result(encode_result(row['has_result'], row['result_stm']),
                         0 if board.turn else 1) == row['result_stm']
    counted('chess_mirror_and_codec')


SCALARS = st.one_of(st.none(), st.booleans(), st.integers(),
                   st.floats(allow_nan=True, allow_infinity=True), st.text(max_size=80),
                   st.lists(st.integers(), max_size=3),
                   st.dictionaries(st.text(max_size=3), st.integers(), max_size=3))


@SETTINGS
@given(st.sampled_from(['has_result', 'result_stm', 'score_stm', 'depth', 'ply']), SCALARS)
def malformed_numeric_metadata(field, value):
    row = record(chess.STARTING_FEN, 0, 'cp', 1, 'generated', 1, 'selfplay')
    row[field] = value
    try:
        validated = validate_record(row)
    except (ValueError, TypeError):
        counted('malformed_numeric_metadata')
        return
    if field == 'has_result':
        assert type(validated[field]) is bool and validated[field] is True
    elif field == 'result_stm':
        assert type(validated[field]) is int and validated[field] == 1
    elif field == 'score_stm':
        assert type(validated[field]) is int
    elif field == 'depth':
        assert validated[field] is None or type(validated[field]) is int and validated[field] >= 0
    elif field == 'ply':
        assert type(validated[field]) is int and validated[field] == 0
    counted('malformed_numeric_metadata')


@SETTINGS
@given(st.lists(st.sampled_from([' ', '\t', '\n', '\r\n']), min_size=9, max_size=9),
       st.sampled_from(['1-0', '0-1', '1/2-1/2', '*']))
def pgn_whitespace_preserves_moves(spaces, result):
    tokens = ['1.', 'e4', '{+0.20/12}', 'e5', '2.', 'Nf3', 'Nc6', result, '']
    text = '[Result "'+result+'"]\n\n' + ''.join(t+s for t,s in zip(tokens, spaces))
    game = read_pgn_game(io.StringIO(text))
    assert game is not None and game.headers['Result'] == result
    assert [m.uci() for m in game.mainline_moves()] == ['e2e4', 'e7e5', 'g1f3', 'b8c6']
    counted('pgn_whitespace_preserves_moves')


if __name__ == '__main__':
    low_priority()
    output = ROOT/'generated_initial.json'
    storage_guard(output, allowance=2_000_000)
    started = time.perf_counter()
    identities = {p.name: sha256(p) for p in HERE.glob('*.py')}
    outcomes = {}
    for check in (chess_mirror_and_codec, malformed_numeric_metadata, pgn_whitespace_preserves_moves):
        try:
            check()
        except Exception as error:
            outcomes[check.__name__] = {'status': 'FAIL', 'exception': repr(error)}
            print(check.__name__, repr(error), flush=True)
        else:
            outcomes[check.__name__] = {'status': 'PASS'}
    if identities != {p.name: sha256(p) for p in HERE.glob('*.py')}:
        raise ValueError('source changed during generated tests')
    with output.open('x', encoding='utf-8') as stream:
        json.dump({'checks': outcomes, 'executed_examples': COUNTS,
                   'seconds': time.perf_counter()-started, 'source_files': identities}, stream, indent=2)
    print(json.dumps({'checks': outcomes, 'executed_examples': COUNTS}), flush=True)
