import hashlib
import importlib.util
import random
from dataclasses import replace
from pathlib import Path
import sys

import chess
import pytest

TOOLS = Path('D:/a14/tools')
sys.path.insert(0, str(TOOLS))


@pytest.fixture(scope='module')
def module():
    spec = importlib.util.spec_from_file_location('r14_boundary', TOOLS / 'r14_boundary.py')
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


def endpoint(module, board, line=1, source=12, result='0.5'):
    return module.parse_endpoint((board.fen(en_passant='fen') + ' | 0 | ' + result).encode(), source, line)


def collect(module, left, right):
    left, right = module.Population(left), module.Population(right)
    counts = {}
    pairs = []
    for chunk in module.candidate_chunks(left, right, counts):
        pairs.extend((chunk.left.line, right.valid[int(index)].line) for index in chunk.right_indices)
    return pairs, counts


def scalar_conditions(a, b):
    """Set-based expression of the documented necessary conditions."""
    if a.result != b.result:
        return False
    depth = b.ply - a.ply
    if not 1 <= depth <= 8:
        return False
    if b.halfmove != a.halfmove + depth and b.halfmove >= depth:
        return False
    if set(b.fen.split()[2].replace('-', '')) - set(a.fen.split()[2].replace('-', '')):
        return False
    start, target = chess.Board(a.fen), chess.Board(b.fen)
    for color in (chess.WHITE, chess.BLACK):
        turns = sum((start.turn if turn % 2 == 0 else not start.turn) == color for turn in range(depth))
        opposite_turns = depth - turns
        old = {(piece.piece_type, square) for square, piece in start.piece_map().items() if piece.color == color}
        new = {(piece.piece_type, square) for square, piece in target.piece_map().items() if piece.color == color}
        loss = len(old) - len(new)
        if loss < 0 or loss > opposite_turns:
            return False
        castle = turns > 0 and bool(start.castling_rights & start.occupied_co[color])
        if len(old.symmetric_difference(new)) > 2 * turns + loss + 2 * castle:
            return False
    return True


def test_small_cartesian_population_matches_scalar_enumeration(module):
    rng = random.Random(140501)
    board = chess.Board()
    boards = [board.copy()]
    for _ in range(18):
        board.push(rng.choice(list(board.legal_moves)))
        boards.append(board.copy())
    left = [endpoint(module, b, i+1, 12, str((i % 3)/2)) for i, b in enumerate(boards)]
    right = [endpoint(module, b, i+1, 13, str((i % 3)/2)) for i, b in enumerate(reversed(boards))]
    actual, counts = collect(module, left, right)
    expected = [(a.line, b.line) for a in left for b in right if scalar_conditions(a, b)]
    assert sorted(actual) == sorted(expected)
    assert len(actual) == len(set(actual))
    assert counts['complete'] and counts['total_pairs'] == len(left)*len(right)
    assert sum(counts[name] for name in module.ACCOUNTING_FIELDS) == counts['total_pairs']


def test_invalid_union_and_duplicate_multiplicity(module):
    start = chess.Board()
    target = start.copy()
    target.push_uci('e2e4')
    left = [endpoint(module, start, 1), None, endpoint(module, start, 3), None]
    right = [endpoint(module, target, i+1, 13) for i in range(3)] + [None]
    pairs, counts = collect(module, left, right)
    assert len(pairs) == 6
    assert counts['invalid_endpoint_pairs'] == 10
    assert counts['survivors'] == 6
    assert sum(counts[name] for name in module.ACCOUNTING_FIELDS) == 16


def test_unsigned_material_subtraction_cannot_wrap(module):
    source = chess.Board()
    for token in ('e2e4', 'd7d5', 'e4d5'):
        source.push_uci(token)
    target = chess.Board()
    target.fullmove_number = 3
    pairs, counts = collect(module, [endpoint(module, source)], [endpoint(module, target, source=13)])
    assert not pairs
    assert counts['excluded_material'] == 1


def test_population_rejects_ply_overflow_before_array_conversion(module):
    original = endpoint(module, chess.Board())
    with pytest.raises(ValueError, match='ply'):
        module.Population([replace(original, ply=2**32)])


@pytest.mark.parametrize('fen,tokens', [
    ('r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 7 15', ['e1g1','e8c8']),
    ('r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 7 15', ['e8g8','e1c1']),
    ('4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 2', ['e5d6','e8f7']),
    ('4k3/8/8/8/3Pp3/8/8/4K3 b - d3 0 2', ['e4d3','e1f2']),
    ('1r2k3/P7/8/8/8/8/7p/4K3 w - - 0 10', ['a7b8q','e8f7']),
    ('4k3/8/8/8/8/8/7p/4K3 b - - 0 10', ['h2h1n','e1d2']),
])
def test_legal_special_paths_are_never_filtered(module, fen, tokens):
    source = chess.Board(fen)
    target = source.copy()
    for token in tokens:
        move = chess.Move.from_uci(token)
        assert move in target.legal_moves
        target.push(move)
        pairs, counts = collect(module, [endpoint(module, source)], [endpoint(module, target, source=13)])
        assert pairs == [(1,1)]
        assert counts['survivors'] == 1


def test_random_legal_paths_survive_all_filters(module):
    rng = random.Random(140503)
    source = chess.Board()
    compared = 0
    for sample in range(128):
        if source.is_game_over() or source.ply() > 180:
            source = chess.Board()
        source.push(rng.choice(list(source.legal_moves)))
        target = source.copy()
        for depth in range(1,9):
            moves = list(target.legal_moves)
            if not moves:
                break
            target.push(rng.choice(moves))
            pairs, _ = collect(module, [endpoint(module, source)], [endpoint(module, target, source=13)])
            assert pairs == [(1,1)], (source.fen(), target.fen(), depth)
            compared += 1
    assert compared >= 900


def test_popcount_matches_scalar_64bit_values(module):
    rng = random.Random(140507)
    values = [0, 2**64-1, 2**63, 1] + [rng.getrandbits(64) for _ in range(1000)]
    observed = module.np.bitwise_count(module.np.array(values, dtype=module.np.uint64)).tolist()
    assert observed == [value.bit_count() for value in values]


@pytest.mark.parametrize('side,wanted', [('first',[1,2]),('last',[4,5])])
def test_window_reader_hashes_all_bytes_and_tracks_physical_rows(module, tmp_path, side, wanted):
    row = (chess.STARTING_FEN + ' | 0 | 0.5').encode()
    payload = b'\n'.join([row]*5)
    path = tmp_path / 'source.txt'
    path.write_bytes(payload)
    records, receipt = module.read_window(path, hashlib.md5(payload).hexdigest(), side, 2, 12)
    assert [record.line for record in records] == wanted
    assert receipt['complete'] and receipt['rows'] == 5
    assert receipt['actual_md5'] == hashlib.md5(payload).hexdigest()
    assert receipt['endpoint_key_fill_rate'] == receipt['endpoint_legal_state_fill_rate'] == 1.0


def test_window_reader_preserves_invalid_selected_rows(module, tmp_path):
    row = (chess.STARTING_FEN + ' | 0 | 0.5\n').encode()
    payload = row + b'broken\n' + b'x'*5000+b'\n' + row
    path = tmp_path / 'source.txt'
    path.write_bytes(payload)
    records, receipt = module.read_window(path, hashlib.md5(payload).hexdigest(), 'last', 3, 12)
    assert len(records) == 3 and records[:2] == [None,None]
    assert records[2].line == 4
    assert receipt['endpoint_key_fill_rate'] == receipt['endpoint_legal_state_fill_rate'] == 1/3


def test_window_reader_pin_mismatch_fails_closed(module, tmp_path):
    path = tmp_path / 'source.txt'
    path.write_bytes((chess.STARTING_FEN+' | 0 | 0.5\n').encode())
    with pytest.raises(ValueError, match='hash mismatch'):
        module.read_window(path, '0'*32, 'first', 1, 12)


def test_empty_window_has_no_full_coverage_claim(module, tmp_path):
    path = tmp_path / 'source.txt'
    path.write_bytes(b'')
    records, receipt = module.read_window(path, hashlib.md5(b'').hexdigest(), 'last', 50000, 12)
    assert not records and receipt['endpoint_legal_state_fill_rate'] is None


def test_enumeration_interruption_keeps_complete_false(module):
    source = chess.Board()
    target = source.copy()
    target.push_uci('e2e4')
    counts = {}
    def stop():
        raise TimeoutError('fixture stop')
    with pytest.raises(TimeoutError):
        list(module.candidate_chunks(module.Population([endpoint(module, source)]),
                                     module.Population([endpoint(module, target, source=13)]), counts, stop))
    assert counts['complete'] is False


def test_endpoint_fill_does_not_claim_full_source_parse_coverage(module,tmp_path):
    row = (chess.STARTING_FEN+' | 0 | 0.5\n').encode()
    payload = row+b'not a chess row\n'
    path = tmp_path/'source.txt'
    path.write_bytes(payload)
    records,receipt = module.read_window(path,hashlib.md5(payload).hexdigest(),'first',1,12)
    assert len(records) == 1 and receipt['rows'] == 2
    assert receipt['full_source_byte_hash_verified'] is True
    assert receipt['parse_scope'] == 'retained_endpoints_only'
    assert receipt['full_source_parse_verified'] is False
    assert receipt['endpoint_key_fill_rate'] == receipt['endpoint_legal_state_fill_rate'] == 1.0
    assert 'key_fill_rate' not in receipt and 'legal_state_fill_rate' not in receipt
