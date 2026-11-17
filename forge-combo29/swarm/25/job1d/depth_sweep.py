#!/usr/bin/env python3
"""depth_sweep.py EXE FENS OUTJSONL DEPTH : one depth, fresh process per position.
Prints nothing but progress; one JSON record per position with the final score, PV and PV length.
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


def search(exe, fen, depth):
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
    p.stdin.write(f"go depth {depth}\n"); p.stdin.flush()
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
        p.wait(timeout=120)
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
    return {"score": (f"{kind} {val}" if kind else "?"), "kind": kind, "value": val,
            "pv": pv, "bestmove": best, "final": last}


def main():
    exe, fenfile, outfile, depth = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    fens = [l.strip() for l in open(fenfile) if l.strip() and not l.startswith("#")]
    print(f"positions {len(fens)} at depth {depth}", flush=True)
    with open(outfile, "w") as out:
        for i, fen in enumerate(fens):
            r = search(exe, fen, depth)
            out.write(json.dumps({"i": i, "fen": fen, "depth": depth, **r}) + "\n")
            out.flush()
            if i % 25 == 0:
                print(f"  {i}/{len(fens)}", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
