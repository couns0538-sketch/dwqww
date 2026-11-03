"""Synthetic legal histories only; no production data or engine is read."""
import hashlib
import json

import chess
import pytest


def test_same_row_bytes_have_different_authentic_id_sequences():
    from r14_identity_ambiguity import construct
    proof = construct()
    assert proof.h1 == proof.h2
    assert len(proof.h1.splitlines()) == 2
    assert proof.report['status'] == 'PASS'
    assert proof.report['histories']['H1']['emitted_game_ids'] == ['Y', 'Y']
    assert proof.report['histories']['H2']['emitted_game_ids'] == ['X', 'Y']
    assert proof.report['histories']['H1']['buffered_rows'] == 8
    assert proof.report['histories']['H2']['buffered_rows'] == 16


def test_histories_are_legal_and_stop_at_actual_threefold():
    from r14_identity_ambiguity import construct
    proof = construct()
    for game in proof.report['games'].values():
        board = chess.Board()
        for token in game['moves_uci']:
            assert not board.is_repetition(3)
            move = chess.Move.from_uci(token)
            assert move in board.legal_moves
            board.push(move)
        assert board.ply() == 18
        assert board.is_repetition(3)
        outcome = board.outcome(claim_draw=True)
        assert outcome.termination is chess.Termination.THREEFOLD_REPETITION
        assert outcome.winner is None
        assert game['terminal_fen'] == board.fen(en_passant='fen')
        assert game['result_white'] == 0.5


def test_cross_game_observed_pair_is_an_exact_legal_one_ply_link():
    from r14_identity_ambiguity import construct
    proof = construct()
    a, b = [line.decode().split(' | ') for line in proof.h2.splitlines()]
    assert a[1:] == b[1:] == ['0', '0.5']
    board = chess.Board(a[0])
    move = chess.Move.from_uci('b1c3')
    assert move in board.legal_moves
    board.push(move)
    assert board.fen(en_passant='fen') == b[0]
    assert proof.report['continuation']['legal_exact_full_fen'] is True
    assert proof.report['histories']['H2']['emitted_game_ids'][0] != proof.report['histories']['H2']['emitted_game_ids'][1]


def test_zero_overlap_is_reported_with_complete_three_key_coverage():
    from r14_identity_ambiguity import construct
    for key in construct().report['position_overlap']['keys'].values():
        assert key['rows'] == key['valid_key_rows'] == 2
        assert key['missing_key_rows'] == key['parse_failures'] == 0
        assert key['key_fill_rate'] == 1.0
        assert key['train_val_shared_keys'] == 0


def test_seed_assumption_is_material_and_hash_sets_are_not_reported():
    from r14_identity_ambiguity import construct
    proof = construct()
    assert proof.report['initial_seen'] == {'key_count': 4, 'serialized': False}
    assert proof.report['final_seen'] == {'H1_key_count': 6, 'H2_key_count': 6, 'equal': True, 'serialized': False}
    json.dumps(proof.report)
    without_seed = construct(seed_unwanted=False)
    assert without_seed.h1 != without_seed.h2
    assert without_seed.report['status'] == 'FAIL'


def test_output_hashes_are_of_exact_emitted_bytes():
    from r14_identity_ambiguity import construct
    proof = construct()
    for name, payload in (('H1', proof.h1), ('H2', proof.h2)):
        entry = proof.report['histories'][name]
        assert entry['md5'] == hashlib.md5(payload).hexdigest()
        assert entry['sha256'] == hashlib.sha256(payload).hexdigest()


def test_illegal_synthetic_move_is_refused():
    from r14_identity_ambiguity import replay_game
    with pytest.raises(ValueError):
        replay_game('bad', ('Qh5',))
