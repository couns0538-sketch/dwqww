#!/usr/bin/env python3
"""resolve_disagreements.py EXE MPVJSONL OUTJSONL REFDEPTH : for every board where MultiPV 1 and MultiPV 3 chose
different best moves, score BOTH moves at a deeper reference depth with each pinned by `searchmoves`.

This answers the question the disagreement count raises and cannot answer: when the two settings disagree, is
either move actually better? Pinning both candidates removes the "which one does the free search prefer" confound -
each move is judged on its own, at a depth above both settings, from a position with identical history.

Verdict per board:
  mpv1_better   the move MultiPV 1 chose scores higher
  mpv3_better   the move MultiPV 3 chose scores higher
  equal         identical score at the reference depth (the disagreement was harmless)
  mate_*        both are mates; the shorter forced mate is better (a longer mate is a mistake in a won position)
"""
import json
import re
import shlex
import subprocess
import sys

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]


def score_move(exe, fen, depth, move):
    p = subprocess.Popen(shlex.split(exe), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in S14:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"go depth {depth} searchmoves {move}\n"); p.stdin.flush()
    last, best = None, None
    for line in p.stdout:
        s = line.rstrip("\n")
        if s.startswith("info depth"):
            last = s
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=300)
    except subprocess.TimeoutExpired:
        p.kill()
    kind = val = None
    pv = []
    if last:
        m = re.search(r"score (cp|mate) (-?\d+)", last)
        if m:
            kind, val = m.group(1), int(m.group(2))
        t = last.split()
        pv = t[t.index("pv") + 1:] if "pv" in t else []
    return {"kind": kind, "value": val, "pv": pv, "bestmove": best}


def verdict(a, b):
    """a = score of mpv1's move, b = score of mpv3's move, both at the reference depth, from the same position."""
    if a["kind"] is None or b["kind"] is None:
        return "unscored", 0
    if a["kind"] == "mate" and b["kind"] == "mate":
        # for the side to move, a SMALLER positive mate number is better: abs comparison in both directions
        if abs(a["value"]) < abs(b["value"]):
            return "mpv1_better", 1
        if abs(b["value"]) < abs(a["value"]):
            return "mpv3_better", -1
        return "equal", 0
    if a["kind"] == "mate" and b["kind"] == "cp":
        # a mate is better if it is a mate FOR the side to move
        return ("mpv1_better", 1) if a["value"] > 0 else ("mpv3_better", -1)
    if b["kind"] == "mate" and a["kind"] == "cp":
        return ("mpv3_better", -1) if b["value"] > 0 else ("mpv1_better", 1)
    if a["value"] > b["value"]:
        return "mpv1_better", 1
    if b["value"] > a["value"]:
        return "mpv3_better", -1
    return "equal", 0


def main():
    exe, mpvfile, outfile, refdepth = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    recs = [json.loads(l) for l in open(mpvfile)]
    dis = [r for r in recs if r["mpv1"]["bestmove"] != r["mpv3"]["bestmove"]]
    print(f"disagreements: {len(dis)}; reference depth {refdepth}", flush=True)
    tally = {}
    with open(outfile, "w") as out:
        for n, r in enumerate(dis):
            m1, m3 = r["mpv1"]["bestmove"], r["mpv3"]["bestmove"]
            a = score_move(exe, r["fen"], refdepth, m1)
            b = score_move(exe, r["fen"], refdepth, m3)
            v, sign = verdict(a, b)
            tally[v] = tally.get(v, 0) + 1
            out.write(json.dumps({"i": r["i"], "fen": r["fen"], "mpv1_move": m1, "mpv3_move": m3,
                                  "score_mpv1_move": a, "score_mpv3_move": b, "verdict": v}) + "\n")
            out.flush()
            if n % 10 == 0:
                print(f"  {n}/{len(dis)} {tally}", flush=True)
    print("TALLY", tally, flush=True)


if __name__ == "__main__":
    main()
