"""Q5, footprint-guided: only compare scores where the branch actually ran.

The previous attempts had the order backwards. They compared scores on
positions chosen by intuition and then hoped the repetition branch fired.
199 opening positions returned a zero that proved the branch never executed,
so the comparison was empty.

This inverts it. For every candidate the instrumented build reports how many
times the repetition branch fired below the root (`in_tree`). Only positions
with `in_tree > 0` are then compared against the ablated build. A position
where the branch never fires cannot inform the question, so it is discarded
rather than counted as a null.

The candidates are endgames where a repetition is *plausibly* the best line:
the side to move is materially worse, so trading into a repetition is
attractive. Each root is placed on occurrence #2 by a reversible cycle so the
third occurrence is 4 plies away, and the cycle is verified by comparing
placement, side, castling and ep before use.

Output: for each position with a footprint, stock score vs ablated score. A
difference is proof that in-tree repetition changes the verdict.
"""

import itertools
import subprocess
import sys

import chess

sys.path.insert(0, "tools/audit72")
from engine import Probe, UciSession  # noqa: E402

INSTRUMENTED = "/tmp/instr/probe_rep"
WITH = "build/forge"
ABLATED = "/tmp/abtest/forge_norep"

VALUE = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
         chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0}


def material(board):
    """White-relative material, so the sign is comparable across plies."""
    return sum((VALUE[p.piece_type] if p.color == chess.WHITE else -VALUE[p.piece_type])
               for p in board.piece_map().values())


def state_key(board):
    return (board.board_fen(), board.turn, board.castling_xfen(),
            chess.square_name(board.ep_square) if board.ep_square is not None else "-")


def find_cycle(board):
    """A 4-ply reversible shuttle returning to the same state, or None."""
    start = state_key(board)

    def shuttle_ok(move, brd):
        piece = brd.piece_at(move.from_square)
        if piece is None or piece.piece_type == chess.PAWN:
            return False
        if brd.is_capture(move) or brd.gives_check(move) or brd.is_castling(move):
            return False
        return True

    for m1 in board.legal_moves:
        if not shuttle_ok(m1, board):
            continue
        board.push(m1)
        for m2 in board.legal_moves:
            if not shuttle_ok(m2, board):
                continue
            board.push(m2)
            back1 = chess.Move(m1.to_square, m1.from_square)
            if back1 in set(board.legal_moves):
                board.push(back1)
                back2 = chess.Move(m2.to_square, m2.from_square)
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


def footprint(fen, moves, depth):
    """(in_tree, root, score, nodes) from the instrumented build."""
    out = subprocess.run([INSTRUMENTED, fen, str(depth), *moves],
                         capture_output=True, text=True, timeout=120)
    in_tree = root = None
    for line in out.stderr.splitlines():
        if line.startswith("REPCOUNT"):
            parts = dict(t.split("=") for t in line.split()[1:])
            in_tree, root = int(parts["in_tree"]), int(parts["root"])
    result = None
    for line in out.stdout.splitlines():
        if line.startswith("RESULT"):
            result = dict(t.split("=", 1) for t in line.split()[1:])
    if in_tree is None:
        return None
    return in_tree, root, result


def score_uci(fen, moves, depth, binary):
    session = UciSession(binary)
    try:
        probe = Probe(fen, moves=moves, session=session)
        res = probe.search("depth %d" % depth)
        return (res["score"][0], res["score"][1]), res["nodes"]
    finally:
        session.close()


def build_candidates():
    """Endgames where a repetition could be the best line for a worse side."""
    out = []

    def add(pieces, turn=chess.WHITE):
        board = chess.Board(None)
        board.turn = turn
        for sq, (pt, cl) in pieces.items():
            board.set_piece_at(chess.parse_square(sq), chess.Piece(pt, cl))
        board.castling_rights = chess.BB_EMPTY
        board.ep_square = None
        board.halfmove_clock = 0
        board.fullmove_number = 1
        if board.is_valid() and len(board.piece_map()) == len(pieces):
            out.append(board.fen())

    K, Q, R, B, N, P = (chess.KING, chess.QUEEN, chess.ROOK,
                        chess.BISHOP, chess.KNIGHT, chess.PAWN)
    W, Bk = chess.WHITE, chess.BLACK

    # Rook vs rook: repetition is often the drawing method for the weaker king.
    for wk in ("a1", "h1", "b1"):
        for wrsq in ("b2", "c1", "e1", "g2"):
            for bksq in ("h8", "g8", "a8"):
                for brsq in ("h4", "a5", "f6", "b8"):
                    if len({wk, wrsq, bksq, brsq}) != 4:
                        continue
                    add({wk: (K, W), wrsq: (R, W), bksq: (K, Bk), brsq: (R, Bk)})

    # Queen vs queen+rook (side to move materially down).
    for wk in ("a1", "b1", "h1"):
        for wq in ("e4", "d5", "h5"):
            for bksq in ("h8", "g8"):
                for bq in ("h4", "a5", "f2"):
                    for brsq in ("a8", "d8", "f6", "h6"):
                        sq = {wk: (K, W), wq: (Q, W), bksq: (K, Bk),
                              bq: (Q, Bk), brsq: (R, Bk)}
                        if len(sq) != 5:
                            continue
                        add(sq)

    # Bishop vs bishop with pawns, where a repetition saves a bad ending.
    for wk in ("a1", "h1"):
        for wb in ("e4", "d3", "h5"):
            for bksq in ("h8", "a8"):
                for bb in ("d5", "a3", "f6"):
                    for wp in ("a2", "c3"):
                        for bp in ("h7", "f7"):
                            sq = {wk: (K, W), wb: (B, W), bksq: (K, Bk),
                                  bb: (B, Bk), wp: (P, W), bp: (P, Bk)}
                            if len(sq) != 6:
                                continue
                            add(sq)
    return out


def main(depth=7, limit=600):
    cands = build_candidates()
    print("candidate endgames: %d" % len(cands))
    tested = 0
    footprints = []
    for fen in cands[:limit]:
        board = chess.Board(fen)
        cycle = find_cycle(board)
        if cycle is None:
            continue
        root = chess.Board(fen)
        for mv in cycle:
            root.push_uci(mv)
        # Root must sit on occurrence #2 for the third to be 4 plies away.
        n = 1
        while root.is_repetition(n + 1):
            n += 1
        if n != 2:
            continue
        fp = footprint(fen, cycle, depth)
        if fp is None:
            continue
        in_tree, root_hits, _ = fp
        tested += 1
        if in_tree > 0:
            footprints.append((fen, cycle, in_tree, material(board)))
        if tested >= limit:
            break

    print("positions where the cycle was playable: %d" % tested)
    print("positions WITH a repetition footprint below the root: %d" % len(footprints))
    print()

    diffs = []
    print("%-46s %-7s %-10s %-10s %s" % ("root", "in_tree", "stock", "ablated", "verdict"))
    for fen, cycle, in_tree, mat in footprints[:40]:
        a, na = score_uci(fen, cycle, depth, WITH)
        b, nb = score_uci(fen, cycle, depth, ABLATED)
        changed = a != b
        if changed:
            diffs.append((fen, cycle, in_tree, a, b, na, nb))
        print("%-46s %-7d %-10s %-10s %s" % (
            fen[:46], in_tree, "%s%d" % a, "%s%d" % b,
            "SCORE CHANGED" if changed else "same"))

    print()
    print("=== positions with a footprint AND a verdict change: %d ===" % len(diffs))
    for fen, cycle, in_tree, a, b, na, nb in diffs:
        print("  %s" % fen)
        print("    cycle: %s" % " ".join(cycle))
        print("    in_tree=%d  stock=%s%d (%d nodes)  ablated=%s%d (%d nodes)" % (
            in_tree, a[0], a[1], na, b[0], b[1], nb))
    return len(footprints), len(diffs)


if __name__ == "__main__":
    depth = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    main(depth)
