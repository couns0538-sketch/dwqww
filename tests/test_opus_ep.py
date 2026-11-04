import pytest

from opus_ep import ep_status, normalize_fen

CASES = [
    # (fen, expected status)
    ('4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 2', 'legal'),                 # plain capture
    ('4k3/8/8/3p4/8/8/8/4K3 w - d6 0 2', 'no_capture'),             # no capturing pawn
    ('4k3/8/8/K2pP2r/8/8/8/8 w - d6 0 2', 'no_capture'),            # both pawns leave the rank: rook hits the king
    ('4k3/6b1/8/3pP3/8/2K5/8/8 w - d6 0 2', 'no_capture'),          # capturer pinned on a diagonal
    ('4k3/6b1/8/2PpP3/8/2K5/8/8 w - d6 0 2', 'legal'),              # one capturer pinned, the other free
    ('8/8/8/3k4/3pP3/8/8/4K3 b - e3 0 1', 'legal'),                 # capture removes the checking pawn
    ('8/8/8/R2k4/3pP3/8/8/4K3 b - e3 0 1', 'no_capture'),           # check from a rook stays
    ('4k3/8/8/pP6/8/8/8/4K3 w - a6 0 2', 'legal'),                  # edge file, one side only
    ('4k3/8/8/6Pp/8/8/8/4K3 w - h6 0 2', 'legal'),                  # other edge file
    ('8/8/8/8/6KP/8/2k5/1q6 b - h3 0 48', 'no_capture'),            # production row: EP written, no capturer
    ('4k3/8/8/3pP3/8/8/8/4K3 w - - 0 2', 'none'),
]
INVALID = [
    '4k3/8/8/4P3/8/8/8/4K3 w - d6 0 2',     # no double-pushed pawn in front of the square
    '4k3/8/8/3pP3/8/8/8/4K3 w - d3 0 2',    # wrong rank for the side to move
    '4k3/3p4/8/3pP3/8/8/8/4K3 w - d6 0 2',  # origin square occupied
    '4k3/8/3n4/3pP3/8/8/8/4K3 w - d6 0 2',  # EP square occupied
]


@pytest.mark.parametrize('fen,expected', CASES)
def test_status(fen, expected):
    f = fen.split()
    assert ep_status(f[0], f[1], f[3]) == expected


@pytest.mark.parametrize('fen,expected', CASES)
def test_normalised_field_matches_the_oracle(fen, expected):
    chess = pytest.importorskip('chess')
    mine = normalize_fen(fen).split()
    assert mine[3] == chess.Board(fen).fen(en_passant='legal').split()[3]
    assert mine[3] == (fen.split()[3] if expected == 'legal' else '-')
    assert mine[:3] + mine[4:] == fen.split()[:3] + fen.split()[4:]   # nothing else changes


@pytest.mark.parametrize('fen', INVALID)
def test_invalid_field_fails_closed(fen):
    f = fen.split()
    assert ep_status(f[0], f[1], f[3]) == 'invalid'
    with pytest.raises(ValueError, match='invalid en-passant'):
        normalize_fen(fen)


def test_malformed_placement_raises():
    with pytest.raises(ValueError):
        ep_status('4k3/8/8/3pP3/8/8/8/4K2', 'w', 'd6')
