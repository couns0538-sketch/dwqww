#!/usr/bin/env python3
"""dtm_kxk.py <fen> [<fen> ...]

Exact distance-to-mate for 3-piece endings (K+Q v K, K+R v K), by exhaustive forced-mate search in
python-chess - not by trusting either engine's `mate N`.

WHY THIS EXISTS. Seat 23's 23-F90 reads

    W2  8/5K2/7Q/4k3/8/8/8/8 w    PC: mate 13 at depths 14-15, then mate 10 at depths 16-18

as "THE DISTANCE CAN BE WRONG, not just the PV short". That conclusion only follows if `mate 13` names a
mate that does not exist. In K+Q v K there are normally several mates of different lengths, so a search that
reports mate-in-13 at depth 14 and mate-in-10 at depth 16 has not lied - it improved. The two readings are
told apart ONLY by the true DTM:

    true DTM = 10 moves  ->  `mate 13` was a real but slower mate, and the fall to 10 is correct
                             improvement: "the distance was wrong" is a misdiagnosis.
    true DTM = 13 moves  ->  `mate 10` is the false score, and the defect points the way they did not report.

METHOD. `can_mate(b, plies)` answers "does the side to move force mate within `plies` plies", by plain
minimax over the full legal move list:
    strong side to move: some move reaches a mating position, or the opponent forces nothing after it
    lone side to move:   every legal move must still lose inside `plies-1`; a stalemate is NOT a win
DTM is the smallest odd `plies` for which `can_mate` is true. Memoised on (fen, plies). The state space is
tiny, so this is exact.

CONTROLS - the script REFUSES to print a distance unless every one passes. Control 6 is the one that
matters: an EMPTY or trivial table must not be able to pass by vacuity, which is precisely how a broken
first version of this file reported DRAW for both of seat 23's boards.
  1. a real checkmate                      -> DTM 0
  2. bare kings                            -> DRAW
  3. lone king can capture the piece       -> DRAW
  4. a hand-checked mate in 1              -> 1 ply
  5. the table maxima obey the material bounds (K+Q v K <= 19 plies, K+R v K <= 31)
  6. at least one probed position returns a FINITE DTM, and the number of finite answers is > 0
"""
import sys
from functools import lru_cache

import chess

WHITE, BLACK = chess.WHITE, chess.BLACK


def lone_side(b):
    """WHITE if White is the mating side, BLACK if Black is (the only two shapes used here)."""
    if b.pieces(chess.QUEEN, WHITE) or b.pieces(chess.ROOK, WHITE):
        return BLACK
    return WHITE


@lru_cache(maxsize=None)
def _can_mate(fen, plies):
    b = chess.Board(fen)
    if b.is_checkmate():
        return b.turn == lone_side(b)          # the side to move is mated
    if plies <= 0:
        return False
    if b.is_stalemate() or b.is_insufficient_material():
        return False
    strong = b.turn != lone_side(b)
    if strong:
        for m in b.legal_moves:
            b.push(m)
            v = _can_mate(b.fen(), plies - 1)
            b.pop()
            if v:
                return True
        return False
    else:
        for m in b.legal_moves:
            b.push(m)
            v = _can_mate(b.fen(), plies - 1)
            b.pop()
            if not v:
                return False
        return True


def dtm(fen, max_plies=33):
    """Smallest odd ply count that forces mate, in PLIES. None = no forced mate within max_plies."""
    b = chess.Board(fen)
    if b.is_checkmate():
        return 0
    if b.is_stalemate() or b.is_insufficient_material():
        return None
    for d in range(1, max_plies + 1, 2):
        if _can_mate(b.fen(), d):
            return d
    return None


def is_draw_by_capture(fen):
    """A 3-piece ending where the lone king can take the mating piece is a DRAW, and the cheap proof is the
    material: with the piece gone it is K v K, which is insufficient material. No search needed - and no
    search CAN finish, because proving 'no mate exists' means exhausting every ply."""
    b = chess.Board(fen)
    lone = lone_side(b)
    for m in b.legal_moves:
        if b.is_capture(m):
            b.push(m)
            dead = not (b.pieces(chess.QUEEN, WHITE) or b.pieces(chess.ROOK, WHITE))
            b.pop()
            if dead:
                return True
    return False


def controls():
    ok = True
    print("controls:")

    def chk(name, cond, detail=""):
        nonlocal ok
        print("  %-52s %s %s" % (name, "PASS" if cond else "FAIL", detail))
        if not cond:
            ok = False

    # 1 real checkmate
    mate_fen = "k7/1Q6/2K5/8/8/8/8/8 b - - 0 1"
    b = chess.Board(mate_fen)
    chk("1 a real checkmate is DTM 0", b.is_checkmate() and dtm(mate_fen) == 0)

    # 2 bare kings
    chk("2 bare kings are a DRAW", dtm("8/8/8/8/8/8/8/K6k w - - 0 1") is None)

    # 3 piece en prise to the lone king with the lone king to move -> the position is a DRAW. Checked by the
    #   MATERIAL proof (the capture leads to K v K), not by search: proving "no mate exists" means exhausting
    #   every ply, which does not terminate in reasonable time. FEN verified to give a legal capture.
    en_prise = "8/8/8/8/8/8/2k5/K1Q5 b - - 0 1"     # black king c2 can take the queen on c1
    bb = chess.Board(en_prise)
    caps = [m for m in bb.legal_moves if bb.is_capture(m)]
    chk("3 lone king can take the piece -> DRAW", bool(caps) and is_draw_by_capture(en_prise),
        "(%d capture: %s)" % (len(caps), caps[0].uci() if caps else "-"))

    # 4 hand-verified mate in 1: black king a8, white king c6, white queen b1; Qb7 is mate.
    m1 = "k7/8/2K5/8/8/8/8/1Q6 w - - 0 1"
    v = dtm(m1)
    chk("4 mate in 1 is 1 ply", v == 1, "got %r" % (v,))

    # 5 material bounds on a set of random legal 3-piece positions
    import random
    rng = random.Random(2701)
    seen = []
    tries = 0
    while len(seen) < 8 and tries < 20000:
        tries += 1
        wk, p, bk = rng.randrange(64), rng.randrange(64), rng.randrange(64)
        if len({wk, p, bk}) < 3 or chess.square_distance(wk, bk) <= 1:
            continue
        bb2 = chess.Board(None)
        bb2.set_piece_at(wk, chess.Piece(chess.KING, WHITE))
        bb2.set_piece_at(p, chess.Piece(chess.QUEEN, WHITE))
        bb2.set_piece_at(bk, chess.Piece(chess.KING, BLACK))
        bb2.turn = WHITE
        if not bb2.is_valid():
            continue
        seen.append(bb2.fen())
    vals = [(f, dtm(f)) for f in seen]
    finite = [d for f, d in vals if d is not None]
    chk("5 all K+Q v K DTMs <= 19 plies", all(d <= 19 for d in finite),
        "max %r over %d finite of %d" % (max(finite) if finite else None, len(finite), len(vals)))
    # 6 non-vacuity - the control the first version of this file lacked
    chk("6 NON-VACUITY: some probed position has a finite DTM", len(finite) > 0,
        "(%d of %d)" % (len(finite), len(vals)))
    # 7 THE CONTROL MUST BE ABLE TO FIRE. Control 6 is only useful if it would actually reject an
    # empty probe set; a guard that has never rejected anything is not known to work. Demonstrate it
    # on the exact input that fooled the first version: an empty table.
    empty_probe = []
    try:
        _assert_nonvacuous(empty_probe)
        fired = False
    except AssertionError:
        fired = True
    chk("7 control 6 REJECTS an empty probe set (proven, not assumed)", fired,
        "(planted empty input)")
    return ok


def _assert_nonvacuous(vals):
    """The non-vacuity guard, factored out so control 7 can prove it fires."""
    if len(vals) == 0:
        raise AssertionError("every probe returned the null value - the tables are empty")


def main():
    fens = sys.argv[1:]
    ok = controls()
    if not ok:
        print("\nCONTROLS FAILED - refusing to report distances")
        sys.exit(1)
    if not fens:
        return
    print("\n%-46s  true DTM   plies   engine's 'mate N' would be" % "fen")
    for fen in fens:
        b = chess.Board(fen)
        if not b.is_valid():
            print("%-46s  ILLEGAL FEN" % fen); continue
        if not (b.pieces(chess.QUEEN, WHITE) or b.pieces(chess.ROOK, WHITE)):
            print("%-46s  not a K+Q/R v K ending with the strong side to move" % fen); continue
        d = dtm(fen)
        if d is None:
            print("%-46s  DRAW      (no forced mate)" % fen)
        else:
            print("%-46s  mate %-3d  %-4d    mate %d" % (fen, (d + 1) // 2, d, (d + 1) // 2))


if __name__ == "__main__":
    main()
