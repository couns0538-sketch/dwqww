"""Find a position where the repetition is load-bearing for the ENGINE.

Two conditions, both machine-checked:

  1. python-chess confirms a forced perpetual for the side to move
     (every defender reply keeps a check available), and
  2. the engine scores the position differently with repetition detection
     enabled versus ablated.

Condition 2 is the decisive one: if the two binaries agree, repetition
contributed nothing to that search and the fixture proves nothing.  The
ablated binary is built by `tools/audit72/build_ablation.sh`.

The perpetual verifier is reused from verify_perpetual.py so that "forced"
means what it says: the defender never has a reply that stops the checks.
"""

import subprocess
import sys

import chess

sys.path.insert(0, "tools/audit72")
from verify_perpetual import find_perpetual  # noqa: E402

WITH = "build/forge"
ABLATED = "/tmp/abtest/forge_norep"

VALUES = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
          chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0}


def material(board):
    return sum((VALUES[p.piece_type] if p.color == board.turn else -VALUES[p.piece_type])
               for p in board.piece_map().values())


def engine_score(fen, depth, binary):
    """Score from the probe binary, which drives the real Searcher."""
    out = subprocess.run([binary.replace("forge", "probe_rep").replace("probe_rep_norep", "probe_rep_norep"),
                          fen, str(depth)],
                         capture_output=True, text=True, timeout=60)
    raise SystemExit("unused")


def score_via_uci(fen, depth, binary, moves=()):
    from engine import Probe, UciSession
    session = UciSession(binary)
    probe = Probe(fen, moves=moves, session=session)
    try:
        res = probe.search("depth %d" % depth)
    finally:
        probe.close()
    return res


def candidates():
    """White has Q only; black has Q+R. White king boxed in a corner, black
    king exposed so the checks are available. The extra black material is
    placed where the white queen cannot capture it."""
    out = []
    for wk in ("a1", "h1", "b1"):
        for bk in ("h8", "g8", "h7"):
            for wq in ("e4", "d5", "e5", "c5", "a4", "h5", "b5"):
                for bq in ("h4", "a5", "g1", "b2", "c6", "f2"):
                    for br in ("a8", "b8", "h5", "f6", "a2", "d8"):
                        squares = {wk: (chess.KING, chess.WHITE),
                                   wq: (chess.QUEEN, chess.WHITE),
                                   bk: (chess.KING, chess.BLACK),
                                   bq: (chess.QUEEN, chess.BLACK),
                                   br: (chess.ROOK, chess.BLACK)}
                        if len(squares) != 5:
                            continue
                        board = chess.Board(None)
                        board.turn = chess.WHITE
                        ok = True
                        for sq, (pt, cl) in squares.items():
                            board.set_piece_at(chess.parse_square(sq), chess.Piece(pt, cl))
                        board.castling_rights = chess.BB_EMPTY
                        board.ep_square = None
                        board.halfmove_clock = 0
                        board.fullmove_number = 1
                        if not board.is_valid():
                            continue
                        # white must have no capture available at the root,
                        # otherwise the "save" is a tactic, not a repetition
                        if any(board.is_capture(m) for m in board.legal_moves):
                            continue
                        out.append(board.fen())
    return out


if __name__ == "__main__":
    cands = candidates()
    print("candidates without a root capture: %d" % len(cands))
    for fen in cands:
        mat = material(chess.Board(fen))
        if mat > -400:
            continue
        moves, occ = find_perpetual(fen, max_plies=10)
        if occ < 3:
            continue
        print("\nverified perpetual, material %d: %s" % (mat, fen))
        print("  line: %s" % " ".join(m.uci() for m in moves))
        for depth in (6, 8):
            a = score_via_uci(fen, depth, WITH)
            b = score_via_uci(fen, depth, ABLATED)
            print("  depth %d: with=%s%d ablated=%s%d  %s" % (
                depth, a["score"][0], a["score"][1],
                b["score"][0], b["score"][1],
                "LOAD-BEARING" if a["score"] != b["score"] else "no difference"))
