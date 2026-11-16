#!/usr/bin/env python3
"""check_S06F21.py EXE FENS DEPTH : independent check of seat 06's S-F21 rate claim.

S-F21 claims: on G (353 positions) at depth 10 with S14, 101 of 353 bestmoves differ from the colour
mirror (28.6%, CI 24.1-33.5), and 94.6% of scores differ.

My harness, written from the claim (not copied from seat 06): for each FEN, search it, then search its
colour mirror computed with python-chess board.mirror(), and compare
  - bestmove, expected to be the mirror of the original bestmove (mirror(m) == m2)
  - score, expected to be EQUAL (a mirrored position has the same value to the side to move)
Planted control (Opus Rule 1): a deliberately NON-mirrored "mirror" (a shifted board) must be reported as
differing, otherwise the comparison is blind.
"""
import re
import shlex
import subprocess
import sys

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]


def search(exe, fen, depth):
    p = subprocess.Popen(shlex.split(exe), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in S14:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("setoption name OwnBook value false\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"go depth {depth}\n"); p.stdin.flush()
    last, best = None, None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        line = line.rstrip("\n")
        if line.startswith("info depth"):
            last = line
        if line.startswith("bestmove"):
            best = line.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    m = re.search(r"score (cp|mate) (-?\d+)", last or "")
    if not m:
        return None, None, 0
    val = int(m.group(2))
    if m.group(1) == "mate":
        val = (30000 - abs(val)) * (1 if val > 0 else -1)
    n = re.search(r"nodes (\d+)", last or "")
    return val, best, (int(n.group(1)) if n else 0)


def mirror_move_of(move_uci, original_fen):
    """The move in the mirrored position corresponding to move_uci in the original."""
    b = chess.Board(original_fen)
    try:
        m = chess.Move.from_uci(move_uci)
    except ValueError:
        return None
    mb = b.mirror()
    # mirror the move by mirroring the squares in the SAME way board.mirror() flips ranks/colours
    fm = chess.square_mirror(m.from_square)
    tm = chess.square_mirror(m.to_square)
    promo = m.promotion
    if mb.turn != b.turn:
        pass
    cand = chess.Move(fm, tm, promo)
    if cand in mb.legal_moves:
        return cand.uci()
    return None


def main():
    exe, fenfile = sys.argv[1], sys.argv[2]
    depth = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    fens = [l.strip() for l in open(fenfile) if l.strip() and not l.startswith("#")]
    print(f"positions: {len(fens)}  depth {depth}")

    bm_diff = 0
    sc_diff = 0
    n = 0
    unparsed = 0
    for fen in fens:
        b = chess.Board(fen)
        v1, bm1, _ = search(exe, fen, depth)
        v2, bm2, _ = search(exe, b.mirror().fen(), depth)
        if v1 is None or v2 is None or bm1 is None or bm2 is None:
            unparsed += 1
            continue
        n += 1
        expect = mirror_move_of(bm1, fen)
        if expect is None or expect != bm2:
            bm_diff += 1
        if v1 != v2:
            sc_diff += 1

    print(f"compared: {n}  | records with no parseable score/bestmove: {unparsed}")
    if n == 0:
        print("CHECK FAILED: nothing compared"); return 3
    print(f"bestmove NOT the mirror : {bm_diff}/{n} = {100*bm_diff/n:.1f}%")
    print(f"score NOT equal         : {sc_diff}/{n} = {100*sc_diff/n:.1f}%")
    import math
    p = bm_diff / n
    se = math.sqrt(p * (1 - p) / n)
    print(f"95% CI for the bestmove rate: [{100*(p-1.96*se):.1f}%, {100*(p+1.96*se):.1f}%]")

    # Rule-1 plant: compare against a DELIBERATELY wrong mirror on a few positions.
    print()
    print("PLANT: comparing against a shifted (non-mirror) board, which must be reported as different")
    planted_diff = 0
    for fen in fens[:5]:
        b = chess.Board(fen)
        shifted = chess.Board(b.fen())
        # rotate the board 180 degrees: a legal but NOT the colour mirror
        v1, bm1, _ = search(exe, fen, depth)
        v2, bm2, _ = search(exe, shifted.transform(chess.flip_vertical).transform(chess.flip_horizontal).fen(), depth)
        if v1 is None or v2 is None:
            continue
        if bm1 != bm2 or v1 != v2:
            planted_diff += 1
    print(f"  planted (180-rotation) reported as different: {planted_diff}/5")
    if planted_diff == 0:
        print("  PLANT FAILED: the comparison cannot see any difference — the real result is not shown")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
