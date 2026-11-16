#!/usr/bin/env python3
"""check_16sf4.py PC_EXE OUTDIR [N]

Independent check of seat 16's S-F4:
  "the depth-10 search is NOT colour-symmetric: 19 of 353 G pairs (5.4%) give an equal score,
   bestmoves mirror on 252/353; the cause is order/depth dependence, not the evaluation."

Their measurement was on the BASE tree. Mine is on the **PC r15 build under PC20**, which is the
path the owner actually plays — so this either extends their claim to the PC build or shows it is
base-tree-specific. Either answer is new information.

Definitions, fixed before the run:
  * mirror = python-chess `Board.mirror()` (colours swapped, board flipped, side to move swapped).
  * a pair "agrees on score" when the two engine scores are one the negation of the other, because
    `eval` and search scores are SIDE-TO-MOVE relative in this engine (07-C9, and seat 16's own C5).
    A checker that forgets this reports a false 2x difference on every position.
  * a pair "agrees on move" when the mirrored move equals the mirror of the other's best move.

Controls, both required before any rate is reported:
  * POSITIVE CONTROL: a pair of positions that are NOT mirrors must be reported as disagreeing, so
    a checker that always says "equal" is caught.
  * SELF CONTROL: a position against itself (same FEN twice) must agree on score and move.
"""
import json
import os
import queue
import re
import subprocess
import sys
import threading

import chess

S14 = [
    "LmrQuietBase value 93", "LmrQuietDivisor value 205", "LmrNoisyBase value 13",
    "LmrNoisyDivisor value 333", "LmrHistoryDivisor value 5643", "NullMoveBase value 5",
    "LmpBase value 8", "HistoryPruneMultiplier value 2220",
    "HistoryBonusQuadratic value 24", "HistoryBonusLinear value 54",
    "HistoryBonusMax value 2212", "SingularDepth value 6", "IirDepth value 2",
    "NonPawnCorrection value true",
]
PC20 = S14 + ["CuckooRep value true", "HistRework value 2", "TtPruneV2 value true",
              "CorrHistV2 value true", "MateAlphaGuard value true", "OwnBook value false"]


class R:
    def __init__(s, st):
        s.q = queue.Queue()
        threading.Thread(target=s._pump, args=(st,), daemon=True).start()

    def _pump(s, st):
        for l in st:
            s.q.put(l)
        s.q.put(None)

    def get(s, t=600):
        try:
            return s.q.get(timeout=t)
        except queue.Empty:
            return None


def search(exe, fen, depth, options):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    r = R(p.stdout)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def drain():
        while True:
            l = r.get()
            if l is None:
                raise RuntimeError("no readyok")
            if l.strip() == "readyok":
                return

    send("uci")
    while True:
        l = r.get(60)
        if l is None or l.strip() == "uciok":
            break
    for o in ["Hash value 16", "Threads value 1"] + options:
        send("setoption name " + o); send("isready"); drain()
    send("ucinewgame"); send("isready"); drain()
    send("position fen " + fen); send("isready"); drain()
    send(f"go depth {depth}")
    score, best = None, None
    while True:
        l = r.get(600)
        if l is None:
            break
        if l.startswith(f"info depth {depth}") and " score " in l:
            m = re.search(r"score (cp|mate) (-?\d+)", l)
            if m:
                score = (m.group(1), int(m.group(2)))
        if l.startswith("bestmove"):
            best = l.split()[1]
            break
    send("quit")
    try: p.wait(timeout=30)
    except subprocess.TimeoutExpired: p.kill()
    return {"score": score, "best": best}


def expected_mirror_score(sc):
    """The score `Board.mirror()` should read if the search were perfectly symmetric.

    python-chess `mirror()` swaps colours AND the side to move. Search scores here are
    side-to-move relative (07-C9, seat 16's own C5), so a +255 advantage for White becomes a
    +255 advantage for Black in the mirror, and Black is the side to move there: the expected
    reading is the SAME NUMBER, not its negation.

    My first version returned the negation and so counted 116 of 120 pairs as disagreeing --
    including pairs whose bestmove mirrored correctly, which was the tell. This is the exact
    trap seat 16's C5 warns about ("a negation-based symmetry checker would report a false
    8422 cp difference per position").
    """
    return sc


def mirror_move(uci):
    """Mirror a UCI move vertically (a1<->a8)."""
    if uci in (None, "0000") or len(uci) < 4:
        return uci
    def flip(sq):
        f = ord(sq[0]) - ord("a")
        r = int(sq[1]) - 1
        return f"{chr(ord('a') + f)}{8 - r}"
    out = flip(uci[0:2]) + flip(uci[2:4])
    if len(uci) == 5:
        out += uci[4]
    return out


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 120
    depth = 10
    os.makedirs(outdir, exist_ok=True)

    # ---- controls first: a checker that cannot fail is worthless ----
    ctrl_fen = "r1bqkbnr/pppppppp/2n5/8/8/2N5/PPPPPPPP/R1BQKBNR w KQkq - 0 1"
    a = search(exe, ctrl_fen, 2, PC20)
    b = search(exe, ctrl_fen, 2, PC20)          # self control: must agree exactly
    self_ok = (a["score"] == b["score"] and a["best"] == b["best"])
    other = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
    c = search(exe, other, 2, PC20)
    neg_ok = (c["score"] != expected_mirror_score(a["score"]))     # a non-mirror must NOT look like a mirror
    print(f"CONTROL self-pair agrees: {self_ok}   (score {a['score']} vs {b['score']})")
    print(f"CONTROL non-mirror pair does NOT agree: {neg_ok}")
    if not self_ok or not neg_ok:
        raise SystemExit("FAIL a control failed; the checker cannot be trusted")

    # ---- the real sample: set G ----
    fens = []
    for line in open("/tmp/set_G.epd", encoding="utf-8"):
        parts = line.split()
        if len(parts) >= 4:
            f = " ".join(parts[:6]) if len(parts) >= 6 else " ".join(parts[:4]) + " 0 1"
            try:
                chess.Board(f)
            except ValueError:
                continue
            fens.append(f)
    fens = fens[:limit]
    print(f"\npositions: {len(fens)}, depth {depth}, PC r15 under PC20, Threads 1, Hash 16\n")

    same_score = same_move = 0
    rows, disagreements = [], []
    for i, fen in enumerate(fens):
        try:
            mir = chess.Board(fen).mirror().fen()
        except ValueError:
            continue
        o = search(exe, fen, depth, PC20)
        m = search(exe, mir, depth, PC20)
        sc_eq = (m["score"] == expected_mirror_score(o["score"]))
        mv_eq = (m["best"] == mirror_move(o["best"]))
        same_score += sc_eq
        same_move += mv_eq
        rows.append({"i": i, "fen": fen, "mirror": mir, "orig": o, "mir": m,
                     "score_equal": sc_eq, "move_mirrors": mv_eq})
        if not sc_eq or not mv_eq:
            disagreements.append(rows[-1])
        if (i + 1) % 40 == 0:
            print(f"  ...{i+1}/{len(fens)}  score-equal {same_score}  move-equal {same_move}",
                  flush=True)

    n = len(rows)
    print()
    print(f"pairs compared: {n}")
    print(f"score symmetric (mirror reads the same score): {same_score}/{n} "
          f"= {100.0 * same_score / n:.1f}%")
    print(f"bestmove mirrors:                              {same_move}/{n} "
          f"= {100.0 * same_move / n:.1f}%")
    print(f"disagreements (score or move): {len(disagreements)}")
    json.dump({"depth": depth, "rows": rows, "score_equal": same_score,
               "move_equal": same_move, "n": n},
              open(os.path.join(outdir, "check_16sf4.json"), "w"), indent=1)
    print()
    print("first 8 disagreements:")
    for r in disagreements[:8]:
        print(f"  #{r['i']:>3} orig {r['orig']['score']}/{r['orig']['best']}  "
              f"mirror {r['mir']['score']}/{r['mir']['best']} "
              f"(mirror of orig move would be {mirror_move(r['orig']['best'])})")


if __name__ == "__main__":
    main()
