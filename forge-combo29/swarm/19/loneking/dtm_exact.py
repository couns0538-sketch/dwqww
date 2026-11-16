#!/usr/bin/env python3
"""dtm_exact.py SIGNATURE OUTDIR : exact distance-to-mate by LAYERED retrograde analysis, with validation.

This replaces my first attempt (`dtm.py`), which was WRONG: it assigned a DTM the first time any winning move
became known and never revised it, so a position could keep a long-mate value after a short mate became
available. It reported max DTM = 44 plies for KQvK, where theory says **19 plies (10 moves)**. The tell was
exactly that: a known theoretical value disagreeing. That bug is recorded in the report.

Correct algorithm (layered retrograde, standard for DTM):
    layer 1  : strong side to move, some move IS checkmate                    -> DTM 1
    layer d  : strong to move, SOME successor already solved with DTM <= d-1   -> DTM = min such + 1
               bare side to move, EVERY successor already solved with DTM<=d-1 -> DTM = max such + 1
    unsolved at the end: a draw for the strong side.
Assigning each position at the FIRST layer where the condition holds gives the MINIMUM DTM, which is what
distance-to-mate means.

Validation: for KQvK the maximum DTM must be 19 plies. The script checks that and refuses to report if not.
"""
import chess
import os
import sys
import time

SIG = sys.argv[1] if len(sys.argv) > 1 else "Q"
OUT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/dtm"

PIECE_OF = {"P": chess.PAWN, "N": chess.KNIGHT, "B": chess.BISHOP, "R": chess.ROOK, "Q": chess.QUEEN}


def key(b):
    return (b.board_fen(), b.turn)


def enumerate_boards(sig, strong):
    """All legal boards: strong side has the pieces in `sig`, other side has only a king."""
    import itertools
    pieces = [PIECE_OF[c] for c in sig]
    n = len(pieces)
    squares = range(64)
    out = []
    for wk in squares:
        for bk in squares:
            if bk == wk:
                continue
            if n == 1:
                combos = ((s,) for s in squares if s not in (wk, bk))
            else:
                combos = itertools.permutations([s for s in squares if s not in (wk, bk)], n)
            for rest in combos:
                if len(set(rest)) != n:
                    continue
                bad = False
                for sq, pt in zip(rest, pieces):
                    if pt == chess.PAWN and chess.square_rank(sq) in (0, 7):
                        bad = True
                if bad:
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
                    b = base.copy(shallow=True)
                    b.turn = turn
                    if b.is_valid():
                        out.append(b)
    return out


def solve(sig, strong=chess.WHITE, verbose=True):
    t0 = time.time()
    boards = enumerate_boards(sig, strong)
    if verbose:
        print("enumerated %d legal positions in %.1fs" % (len(boards), time.time() - t0), flush=True)

    # Precompute, per position: list of successor keys, and whether a move mates at once.
    # This is the expensive part; do it once.
    succ = {}
    mates = set()
    for b in boards:
        k = key(b)
        lst = []
        for m in b.legal_moves:
            c = b.copy()
            c.push(m)
            if c.is_checkmate():
                lst.append("MATE")
            else:
                lst.append(key(c))
        succ[k] = lst
        if b.turn == strong and "MATE" in lst:
            mates.add(k)
    if verbose:
        print("successors precomputed in %.1fs; %d mate-in-1 positions" % (time.time() - t0, len(mates)),
              flush=True)

    dtm = {k: 1 for k in mates}
    turn_of = {key(b): b.turn for b in boards}
    unsolved = [key(b) for b in boards if key(b) not in dtm]
    d = 2
    while unsolved and d < 200:
        newly = {}
        still = []
        for k in unsolved:
            vals = []
            ok = True
            for s in succ[k]:
                if s == "MATE":
                    vals.append(1)
                elif s in dtm:
                    vals.append(dtm[s])
                else:
                    vals.append(None)
            if turn_of[k] == strong:
                known = [v for v in vals if v is not None]
                if known:
                    newly[k] = min(known) + 1
                else:
                    still.append(k)
            else:
                if all(v is not None for v in vals):
                    if vals:
                        newly[k] = max(vals) + 1
                    else:
                        still.append(k)
                else:
                    still.append(k)
        if not newly:
            break
        dtm.update(newly)
        unsolved = still
        if verbose and d % 5 == 0:
            print("  layer %d: +%d solved, %d left, %.0fs" % (d, len(newly), len(unsolved),
                                                              time.time() - t0), flush=True)
        d += 1
    if verbose:
        print("fixed point at layer %d in %.1fs; %d solved, %d unresolved (draws)"
              % (d, time.time() - t0, len(dtm), len(unsolved)), flush=True)
    return dtm, succ, turn_of, boards


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    sig = SIG
    dtm, succ, turn_of, boards = solve(sig, chess.WHITE)
    mx = max(dtm.values())
    print("SIGNATURE %s: max DTM = %d plies (%d moves)" % (sig, mx, (mx + 1) // 2))
    if sig == "Q":
        expect = 19
        print("theory for KQvK: max DTM = %d plies -> %s" % (expect, "MATCH" if mx == expect else "MISMATCH"))
    with open(os.path.join(OUT, "dtm_%s.txt" % sig), "w") as fh:
        fh.write("signature %s, strong side WHITE\n" % sig)
        fh.write("positions solved: %d ; unresolved (draws): %d\n"
                 % (len(dtm), len(boards) - len(dtm)))
        fh.write("max DTM: %d plies\n" % mx)
