"""Widen the Q5 evidence: many positions, not ten hand-picked ones.

The earlier result ("no measurable effect") rested on 10 fixtures, which is
too thin to state as a general finding.  This builds a larger corpus the right
way for the question being asked:

  * take positions from the shipped opening corpus,
  * find a genuine 4-ply reversible cycle in each (a move by each side and its
    exact reversal, restoring placement, castling rights AND ep state),
  * play that cycle once, so the search root sits on occurrence #2 and the
    third occurrence is exactly 4 plies below it,
  * search the root with the stock binary and with the repetition-ablated
    binary, and compare.

Why occurrence #2 and not a plain opening position: in a fresh opening there is
no repetition history at all, so the two binaries cannot differ by
construction and the test would be vacuous.  Putting the root on occurrence #2
is the weakest position where in-tree detection has something to detect.

A cycle is verified by comparing the board FEN *including* halfmove-irrelevant
fields: placement, side, castling, ep.  The halfmove clock necessarily differs
after 4 reversible plies, which is expected and is why the comparison drops it.
"""

import subprocess
import sys

import chess

sys.path.insert(0, "tools/audit72")
from engine import Probe, UciSession  # noqa: E402

WITH = "build/forge"
ABLATED = "/tmp/abtest/forge_norep"


def state_key(board):
    """Identity for cycle detection: placement, side, castling, ep.

    The halfmove clock is excluded because a 4-ply reversible cycle always
    advances it; including it would reject every real cycle.
    """
    return (board.board_fen(), board.turn, board.castling_xfen(),
            chess.square_name(board.ep_square) if board.ep_square is not None else "-")


def find_cycle(fen):
    """Find a 4-ply cycle returning to the same state, in O(M^2) not O(M^4).

    Shape: white plays X->Y, black plays U->V, white plays Y->X, black plays
    V->U.  Restoration then only depends on both individual moves being
    undoable, which is checked directly instead of enumerating all 4-ply
    combinations.

    Restrictions that keep the cycle a true repetition under FIDE:
      * no captures (would change material forever),
      * no pawn moves and no castling (irreversible for the rule-50 clock and
        for castling rights),
      * no checks (a check may permit a different reply structure, and we want
        a quiet shuffle),
      * no en-passant and no promotion,
      * the resulting state must match placement, side, castling and ep.
    """
    board = chess.Board(fen)
    start = state_key(board)

    def reversible(move, brd):
        """True when this is a quiet shuttle move whose reversal restores state."""
        if brd.is_capture(move) or brd.gives_check(move):
            return False
        if brd.is_castling(move) or brd.is_en_passant(move):
            return False
        piece = brd.piece_at(move.from_square)
        if piece is None or piece.piece_type == chess.PAWN:
            return False
        if move.promotion is not None:
            return False
        return True

    for m1 in board.legal_moves:
        if not reversible(m1, board):
            continue
        board.push(m1)
        for m2 in board.legal_moves:
            if not reversible(m2, board):
                continue
            board.push(m2)
            # Close the cycle with the exact reversals.
            back1 = chess.Move(m1.to_square, m1.from_square)
            back2 = chess.Move(m2.to_square, m2.from_square)
            legal = set(board.legal_moves)
            if back1 in legal:
                board.push(back1)
                if back2 in set(board.legal_moves):
                    board.push(back2)
                    restored = state_key(board) == start
                    board.pop()
                    if restored:
                        board.pop()
                        board.pop()
                        board.pop()
                        return [m1.uci(), m2.uci(), back1.uci(), back2.uci()]
                board.pop()
            board.pop()
        board.pop()
    return None


def occurrences(board):
    n = 1
    while board.is_repetition(n + 1):
        n += 1
    return n


def load_epd(limit):
    fens = []
    with open("tools/openings/forge-10000.epd") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            fields = line.split(" id ")[0].split()
            fens.append(" ".join(fields[:4]) + " 0 1")
            if len(fens) >= limit:
                break
    return fens


def score(session, fen, depth):
    probe = Probe(fen, session=session)
    res = probe.search("depth %d" % depth)
    return (res["score"][0], res["score"][1]), res["nodes"]


def main(limit=200, depth=8, out_path="/tmp/abtest/diffscan.txt"):
    fens = load_epd(limit)
    print("opening positions loaded: %d" % len(fens))
    rows, diffs, skipped = [], [], 0
    session_with = UciSession(WITH)
    session_abl = UciSession(ABLATED)
    try:
        for i, fen in enumerate(fens):
            board = chess.Board(fen)
            assert board.is_valid(), fen
            cycle = find_cycle(fen)
            if cycle is None:
                skipped += 1
                continue
            # Root sits on occurrence #2.
            root = chess.Board(fen)
            for mv in cycle:
                root.push_uci(mv)
            occ = occurrences(root)
            if occ != 2:
                skipped += 1
                continue
            a, na = score(session_with, fen, depth)
            b, nb = score(session_abl, fen, depth)
            rows.append((fen, cycle, a, b, na, nb))
            if a != b:
                diffs.append(rows[-1])
            if (i + 1) % 25 == 0:
                print("  %d/%d  diffs=%d" % (i + 1, len(fens), len(diffs)))
    finally:
        session_with.close()
        session_abl.close()

    with open(out_path, "w") as handle:
        handle.write("# differential scan: stock vs repetition-ablated\n")
        handle.write("# depth %d, roots on occurrence #2 via a verified 4-ply cycle\n" % depth)
        handle.write("# positions=%d skipped=%d diffs=%d\n" % (len(rows), skipped, len(diffs)))
        for fen, cycle, a, b, na, nb in rows:
            handle.write("%s\t%s\t%s%d\t%s%d\t%d\t%d\n" % (
                fen, " ".join(cycle),
                a[0], a[1], b[0], b[1], na, nb))

    print()
    print("scanned=%d skipped=%d diffs=%d" % (len(rows), skipped, len(diffs)))
    for fen, cycle, a, b, na, nb in diffs[:10]:
        print("  DIFF %s  with=%s%d ablated=%s%d" % (fen, a[0], a[1], b[0], b[1]))
    return len(rows), len(diffs)


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    main(limit)
