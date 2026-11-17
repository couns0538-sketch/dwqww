"""Find positions with a KNOWN, independently computed DTM (no engine involved).

Why this exists: an aspiration window around a mate score is the dangerous case,
so the mate corpus needs real mates at genuinely different distances. Labelling
positions by eye produced eight "mate in 2/3/4" FENs that were all mate in 1 --
exactly the kind of fabricated label the shared brief warns about. So the labels
here come from a depth-limited AND/OR proof (no engine involved), and the
generator stops as soon as it has what it needs.

DTM convention: plies for the side to move to deliver mate.
  mate in 1 = 1 ply, mate in 2 = 3 plies, mate in 3 = 5 plies, mate in 4 = 7.

`mate_within(bd, d)` is a proof, not an estimate: it is true only if the side to
move can force mate against every defence inside `d` plies. Results are memoised
on (position, d) with the clocks stripped, so the search is exhaustive rather
than heuristic.
"""
import json
import random
import sys

import chess


def key_of(bd):
    """Position identity for memoisation: clocks are irrelevant to a mate proof."""
    return bd.board_fen() + (" w" if bd.turn == chess.WHITE else " b") + \
        " " + (bd.castling_xfen().replace("-", "") or "-") + \
        " " + (chess.square_name(bd.ep_square) if bd.ep_square is not None else "-")


def mate_within(bd, d, memo):
    """True iff the side to move forces mate within `d` plies."""
    if d <= 0:
        return False
    if not any(bd.legal_moves):
        return bd.is_checkmate()
    k = (key_of(bd), d)
    hit = memo.get(k)
    if hit is not None:
        return hit
    result = False
    for mv in bd.legal_moves:
        bd.push(mv)
        if bd.is_checkmate():
            bd.pop()
            result = True
            break
        # Opponent to move: they must have replies, and EVERY reply must still
        # be a mate for us inside the remaining budget.
        if d >= 3 and any(bd.legal_moves):
            ok = True
            for reply in list(bd.legal_moves):
                bd.push(reply)
                sub = mate_within(bd, d - 2, memo)
                bd.pop()
                if not sub:
                    ok = False
                    break
            if ok:
                bd.pop()
                result = True
                break
        bd.pop()
    memo[k] = result
    return result


def exact_dtm(bd, limit=9):
    """Smallest odd/even ply count at which mate is forced, or None."""
    memo = {}
    for d in range(1, limit + 1):
        if mate_within(bd, d, memo):
            return d
    return None


def random_position(rng, rook_only):
    while True:
        wk, bk, big = rng.sample(range(64), 3)
        if chess.square_distance(wk, bk) <= 1:
            continue
        bd = chess.Board(None)
        bd.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        bd.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        bd.set_piece_at(big, chess.Piece(chess.ROOK if rook_only else chess.QUEEN,
                                         chess.WHITE))
        bd.turn = chess.WHITE
        if bd.castling_rights or bd.ep_square is not None:
            continue
        if bd.status() != chess.STATUS_VALID:
            continue
        if bd.is_checkmate() or bd.is_stalemate():
            continue
        return bd.fen()


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/asp/evidence/mates_verified.json"
    rng = random.Random(20261117)
    want = {1: 2, 3: 2, 5: 2, 7: 2}
    found = {k: [] for k in want}
    tried = 0
    while not all(len(found[k]) >= want[k] for k in want) and tried < 300:
        fen = random_position(rng, rook_only=(rng.random() < 0.5))
        tried += 1
        bd = chess.Board(fen)
        # Cheap pre-filter: a position that cannot mate in 1 does not need the
        # full budget; walk the ladder from the bottom so most candidates die at d=1.
        d = exact_dtm(bd, limit=7)
        if d in want and len(found[d]) < want[d] and fen not in sum(found.values(), []):
            found[d].append(fen)
            print(f"dtm {d} plies: {fen}", flush=True)

    rows = []
    for plies in sorted(found):
        for i, fen in enumerate(found[plies]):
            rows.append({
                "fen": fen,
                "dtm_plies": plies,
                "mate_in": (plies + 1) // 2,
                "label": f"verified-mate-in-{(plies + 1) // 2}",
                "index": i,
            })
    with open(out_path, "w") as fh:
        json.dump({"convention": "plies for side to move; mate in N = 2N-1 plies",
                   "positions_tried": tried, "rows": rows}, fh, indent=2)
        fh.write("\n")
    missing = [k for k in want if len(found[k]) < want[k]]
    print(f"tried {tried}; wrote {len(rows)} rows to {out_path}; short on {missing}")


if __name__ == "__main__":
    main()
