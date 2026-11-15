#!/usr/bin/env python3
"""Job 7: retrograde WDL + distance-to-mate for KQvK and KRvK.

Extends the job 6 solver: instead of only W/D/L it computes, for every legal state,
  * the WDL result,
  * for wins, the number of PLIES the winning side needs with both sides optimal
    (the loser maximises the distance, the winner minimises it).
This is the standard retrograde "mate in N" labelling:
  * a state where the mover can deliver immediate mate has dtm = 1;
  * a state is a WIN with dtm = 1 + min over moves of the child's dtm (child is a LOSS);
  * a LOSS with dtm = 1 + max over moves of the child's dtm (child is a WIN);
It is computed by iterating to a fixpoint over the state graph, which for these two
classes converges quickly.

Output: {"KQvK": {key: [wdl, dtm]}, ...} where wdl is "W"/"D"/"L" for the side to move
and dtm is the plies to mate with dtm>0 meaning the side to move wins, dtm<0 meaning the
side to move is mated in |dtm| plies, and null for draws.

Usage: dtm.py <out.json>
"""
import json
import sys

import chess

INF = 10 ** 6


def build(kind):
    strong = chess.QUEEN if kind == "KQvK" else chess.ROOK
    index_of = {}
    boards = []
    for wk in range(64):
        for bk in range(64):
            if wk == bk or chess.square_distance(wk, bk) < 2:
                continue
            for s in range(64):
                if s in (wk, bk):
                    continue
                for turn_white in (True, False):
                    b = chess.Board(None)
                    b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
                    b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
                    b.set_piece_at(s, chess.Piece(strong, chess.WHITE))
                    b.castling_rights = 0
                    b.turn = chess.WHITE if turn_white else chess.BLACK
                    if not b.is_valid():
                        continue
                    index_of[b.board_fen() + (" w" if turn_white else " b")] = len(boards)
                    boards.append(b.copy())
    return index_of, boards


def solve(kind):
    index_of, boards = build(kind)
    n = len(boards)
    print(f"{kind}: {n} states", flush=True)
    moves_of = [None] * n
    wdl = [None] * n
    dtm = [None] * n
    for i, b in enumerate(boards):
        mv = []
        mate = False
        for m in b.legal_moves:
            b.push(m)
            if b.is_checkmate():
                mate = True
                b.pop()
                break
            if b.is_stalemate() or b.is_insufficient_material():
                mv.append(("D", None))
                b.pop()
                continue
            ci = index_of.get(b.board_fen() + (" w" if b.turn else " b"))
            if ci is not None:
                mv.append(("S", ci))
            b.pop()
        if mate:
            wdl[i] = "W"
            dtm[i] = 1
            moves_of[i] = []
        else:
            moves_of[i] = mv

    # Full relaxation each pass: recompute what is determinable and overwrite when it
    # differs. An earlier version froze a win at the first distance it found, which left
    # 509 of 2,000 sampled distances too large.
    changed = True
    passes = 0
    while changed:
        changed = False
        passes += 1
        for i in range(n):
            mv = moves_of[i]
            if mv is None:
                continue
            best_win = None
            all_decided = True
            all_children_win = True
            max_child = 0
            for how, c in mv:
                if how == "D":
                    all_children_win = False
                    continue
                cw = wdl[c]
                if cw is None:
                    all_decided = False
                    all_children_win = False
                    continue
                if cw == "L" and dtm[c] is not None:
                    d = 1 + abs(dtm[c])
                    if best_win is None or d < best_win:
                        best_win = d
                if cw == "W":
                    if dtm[c] is not None and 1 + abs(dtm[c]) > max_child:
                        max_child = 1 + abs(dtm[c])
                else:
                    all_children_win = False
            if best_win is not None:
                if wdl[i] != "W" or dtm[i] != best_win:
                    wdl[i] = "W"
                    dtm[i] = best_win
                    changed = True
            elif wdl[i] == "W":
                pass                      # keep; a shorter win may appear later
            elif mv and all_decided and all_children_win:
                want = -(max_child if max_child else 1)
                if wdl[i] != "L" or dtm[i] != want:
                    wdl[i] = "L"
                    dtm[i] = want
                    changed = True
            elif mv and all_decided:
                if wdl[i] != "D":
                    wdl[i] = "D"
                    dtm[i] = None
                    changed = True

    # Unresolved states sit in cycles with no forced win and no forced loss: WDL draw.
    remaining = [i for i in range(n) if moves_of[i] and wdl[i] is None]
    for i in remaining:
        wdl[i] = "D"
        dtm[i] = None
    print(f"  passes {passes}, resolved {len(remaining)} undecided as draws", flush=True)
    from collections import Counter
    c = Counter()
    result = {}
    for i, b in enumerate(boards):
        c[wdl[i]] += 1
        result[b.board_fen() + (" w" if b.turn else " b")] = [wdl[i], dtm[i]]
    print(f"  counts {dict(c)}", flush=True)
    return result


def main():
    out_path = sys.argv[1]
    res = {}
    for kind in ("KQvK", "KRvK"):
        res[kind] = solve(kind)
    with open(out_path, "w") as f:
        json.dump(res, f)


if __name__ == "__main__":
    main()
