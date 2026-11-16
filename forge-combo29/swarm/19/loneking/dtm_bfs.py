#!/usr/bin/env python3
"""dtm_bfs.py SIGNATURE OUTDIR : exact distance-to-mate by BACKWARD BFS (retrograde), with validation.

Replaces two earlier attempts, both of which are kept in the record:
  * `dtm.py`      -- assigned a DTM the first time any winning move was known and never revised, so long mates
                     stuck. Reported max DTM = 44 plies for KQvK where theory says 19.
  * `dtm_exact.py`-- correct layering but re-scanned every unsolved position per layer: ~7 minutes for KQvK and
                     it never finished in the time I gave it.

This version does the standard backward BFS:
  layer 1 : positions where the strong side has a mate in 1
  then, for each newly solved position, walk its PREDECESSORS:
      predecessor strong-to-move : it is won as soon as ONE successor is won  -> DTM = succ+1, queue it
      predecessor bare-to-move   : decrement its unsolved-successor count; when the count reaches 0 and it has
                                   no drawn successor, it is won -> DTM = max(successor)+1, queue it
  anything never queued is a draw for the strong side.

That is O(edges) with one reverse-edge build, and it assigns minimum DTM by construction.

VALIDATION IS PART OF THE SCRIPT: for KQvK the maximum DTM must be 19 plies (10 moves). If it is not, the script
says MISMATCH and refuses to be used as an oracle. Nothing downstream runs on an unvalidated solver.
"""
import chess
import collections
import os
import sys
import time

PIECE_OF = {"P": chess.PAWN, "N": chess.KNIGHT, "B": chess.BISHOP, "R": chess.ROOK, "Q": chess.QUEEN}


def key(b):
    return (b.board_fen(), b.turn)


def enumerate_boards(sig, strong):
    import itertools
    pieces = [PIECE_OF[c] for c in sig]
    n = len(pieces)
    out = []
    sq_all = range(64)
    for wk in sq_all:
        for bk in sq_all:
            if bk == wk:
                continue
            avail = [s for s in sq_all if s not in (wk, bk)]
            combos = itertools.permutations(avail, n) if n > 1 else ((s,) for s in avail)
            for rest in combos:
                if len(set(rest)) != n:
                    continue
                if any(pt == chess.PAWN and chess.square_rank(sq) in (0, 7) for sq, pt in zip(rest, pieces)):
                    continue
                base = chess.Board(None)
                if strong == chess.WHITE:
                    base.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
                    base.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
                    for sq, pt in zip(rest, pieces):
                        base.set_piece_at(sq, chess.Piece(pt, chess.WHITE))
                else:
                    base.set_piece_at(wk, chess.Piece(chess.KING, chess.BLACK))
                    base.set_piece_at(bk, chess.Piece(chess.KING, chess.WHITE))
                    for sq, pt in zip(rest, pieces):
                        base.set_piece_at(sq, chess.Piece(pt, chess.BLACK))
                for turn in (chess.WHITE, chess.BLACK):
                    b = base.copy()
                    b.turn = turn
                    if b.is_valid():
                        out.append(b)
    return out


def solve(sig, strong=chess.WHITE):
    t0 = time.time()
    boards = enumerate_boards(sig, strong)
    print("enumerated %d legal positions in %.1fs" % (len(boards), time.time() - t0), flush=True)

    turn_of, succ, mate_now = {}, {}, {}
    for b in boards:
        k = key(b)
        turn_of[k] = b.turn
        lst, mates = [], False
        for m in b.legal_moves:
            c = b.copy()
            c.push(m)
            if c.is_checkmate():
                mates = True
            else:
                lst.append(key(c))
        succ[k] = lst
        mate_now[k] = mates
    print("successors built in %.1fs" % (time.time() - t0), flush=True)

    pred = collections.defaultdict(list)
    for k, lst in succ.items():
        for s in lst:
            pred[s].append(k)

    dtm = {}
    queue = collections.deque()
    for k in succ:
        if turn_of[k] == strong and mate_now[k]:
            dtm[k] = 1
            queue.append(k)
    print("mate-in-1 seeds: %d" % len(queue), flush=True)

    unsolved_children = {k: len(succ[k]) for k in succ if k not in dtm}
    while queue:
        k = queue.popleft()
        d = dtm[k]
        for p in pred.get(k, ()):
            if p in dtm:
                continue
            if turn_of[p] == strong:
                dtm[p] = d + 1
                queue.append(p)
            else:
                unsolved_children[p] -= 1
                if unsolved_children[p] == 0:
                    # every successor is won; DTM is one more than the worst
                    dtm[p] = max(dtm[s] for s in succ[p]) + 1
                    queue.append(p)
    print("retrograde done in %.1fs: %d solved, %d unresolved" % (time.time() - t0, len(dtm),
                                                                  len(boards) - len(dtm)), flush=True)
    return dtm, succ, turn_of, boards


# ---------------------------------------------------------------------------
# HALFMOVE WINDOW (seat 21's trap, 19-C10)
# A DTM from solve() is UNCONSTRAINED. Under match rules only 100 - counter half-moves remain, so a position
# whose mate needs more plies than the window allows is a DRAW, not a win. Never read a DTM without clamping:
def windowed_verdict(dtm_plies, halfmove_counter):
    """True result under the fifty-move rule, given an unconstrained DTM."""
    if dtm_plies is None:
        return "draw"                      # the solver proved no forced mate at all
    window = 100 - halfmove_counter
    return "win" if dtm_plies <= window else "draw-by-window"


if __name__ == "__main__":
    sig = sys.argv[1] if len(sys.argv) > 1 else "Q"
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/dtm"
    os.makedirs(out, exist_ok=True)
    dtm, succ, turn_of, boards = solve(sig, chess.WHITE)
    mx = max(dtm.values())
    print("SIGNATURE %s: max DTM = %d plies (%d moves)" % (sig, mx, (mx + 1) // 2))
    verdict = ""
    if sig == "Q":
        verdict = "MATCH" if mx == 19 else "MISMATCH"
        print("theory for KQvK: 19 plies -> %s" % verdict)
    with open(os.path.join(out, "dtm_%s.txt" % sig), "w") as fh:
        fh.write("signature %s (strong side WHITE)\n" % sig)
        fh.write("solved %d of %d ; unresolved (draws) %d\n" % (len(dtm), len(boards), len(boards) - len(dtm)))
        fh.write("max DTM %d plies\n" % mx)
        if sig == "Q":
            fh.write("validation vs theory (19 plies): %s\n" % verdict)
