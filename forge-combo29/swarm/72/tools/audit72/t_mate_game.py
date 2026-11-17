"""Game-level proof of the ply-0 claim defect.

The static-score table shows the engine returns 0 where a mate exists.  This
test shows the consequence at game level: put the engine on the winning side
of a won position and let it play against a passive defender that only moves
its king.  A correct engine converts; this one does not, and the failure is
caused precisely by the threshold.

The control is the same position at halfmove 99, which converts.  Both starts
are identical apart from the clock, so the difference cannot be explained by
anything else.

Every fixture goes through Probe (python-chess validation, both reply streams
scanned, perft-1 agreement), and the defender's replies are chosen from
python-chess legal moves, so the engine is never fed an illegal position.
"""

import sys

import chess

sys.path.insert(0, "tools/audit72")
from engine import Probe  # noqa: E402

# White Ra1, Rh1-ish won position: Ra1-a8 is mate because Kg6 covers g7/h7.
MATE_IN_1 = "7k/8/6K1/8/8/8/8/R7 w - - %d 60"
MAX_WHITE_MOVES = 8


def play_out(start_halfmove, depth=5, verbose=False):
    """Let the engine play white; defender shuffles its king. Return whether mate landed."""
    board = chess.Board(MATE_IN_1 % start_halfmove)
    assert board.is_valid()
    for ply in range(MAX_WHITE_MOVES):
        if board.is_game_over():
            break
        probe = Probe(board.fen())
        try:
            res = probe.search("depth %d" % depth)
        finally:
            probe.close()
        move = res["bestmove"]
        legal = {m.uci() for m in board.legal_moves}
        assert move in legal, "engine returned illegal %s in %s" % (move, board.fen())
        mates = [m.uci() for m in board.legal_moves
                 if (board.push(m), board.is_checkmate(), board.pop())[1]]
        if verbose:
            print("   white %-5s score=%-8s hm=%-4d mate_available=%s" % (
                move, "%s%d" % res["score"], board.halfmove_clock, mates or "-"))
        board.push_uci(move)
        if board.is_checkmate():
            return True, board
        # Defender: prefer a king move so the position stays won for white.
        replies = [m for m in board.legal_moves
                   if board.piece_at(m.from_square).piece_type == chess.KING]
        board.push((replies or list(board.legal_moves))[0])
    return False, board


def main():
    print("=" * 78)
    print("GAME-LEVEL: can the engine convert a won position it is winning now?")
    print("=" * 78)
    print("position: 7k/8/6K1/8/8/8/8/R7 w, mate in 1 by Ra1-a8")
    print()

    print("CONTROL, halfmove 99 (below the threshold):")
    ok_99, end_99 = play_out(99, verbose=True)
    print("  -> mated: %s" % ok_99)
    print()

    print("TREATMENT, halfmove 100 (at the threshold):")
    ok_100, end_100 = play_out(100, verbose=True)
    print("  -> mated: %s | final halfmove: %d" % (ok_100, end_100.halfmove_clock))
    print()

    fails = []
    if not ok_99:
        fails.append("control at hm=99 did not convert; the test is broken")
    if ok_100:
        fails.append("hm=100 converted unexpectedly; the defect did not reproduce")

    print("=" * 78)
    if fails:
        for f in fails:
            print("PROBLEM:", f)
        return 1
    print("CONFIRMED: hm=99 converts, hm=100 does not. The threshold alone")
    print("decides whether the engine can win an already-won position.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
