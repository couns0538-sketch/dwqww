#!/usr/bin/env python3
"""run_mates.py EXE FENS OUTJSONL : depth-12 and depth-20 mate comparison for S5/S6.

For each position: search at depth 12 and at depth 20 with S14/PC20-style settings (Threads 1, Hash 16), record the
score and whether it is a mate, and the PV length. Fresh process per search. PVs are sliced from the engine line and
replayed with python-chess - never typed.
"""
import json
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


def run(exe, fen, depth):
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
    lines, best = [], None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth"):
            lines.append(s)
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=60)
    except subprocess.TimeoutExpired:
        p.kill()
    last = lines[-1] if lines else None
    score, pv = "?", []
    kind = val = None
    if last:
        m = re.search(r"score (cp|mate) (-?\d+)", last)
        if m:
            kind, val = m.group(1), int(m.group(2))
            score = m.group(0)
        toks = last.split()
        pv = toks[toks.index("pv") + 1:] if "pv" in toks else []
    return {"score": score, "kind": kind, "value": val, "bestmove": best, "pv": pv,
            "lines": lines}


def pv_is_mate(fen, val, pv):
    b = chess.Board(fen)
    for mv in pv:
        try:
            mm = chess.Move.from_uci(mv)
        except ValueError:
            return False
        if mm not in b.legal_moves:
            return False
        b.push(mm)
    need = 2 * val - 1 if val > 0 else 2 * abs(val)
    return b.is_checkmate() and len(pv) == need


def main():
    exe, fenfile, outfile = sys.argv[1], sys.argv[2], sys.argv[3]
    fens = [l.strip() for l in open(fenfile) if l.strip() and not l.startswith("#")]
    print(f"positions: {len(fens)}", flush=True)
    with open(outfile, "w") as out:
        for i, fen in enumerate(fens):
            r12 = run(exe, fen, 12)
            rec = {"i": i, "fen": fen, "d12": r12}
            if r12["kind"] == "mate":
                r20 = run(exe, fen, 20)
                rec["d20"] = r20
                rec["pv12_mate"] = pv_is_mate(fen, r12["value"], r12["pv"])
                if r20["kind"] == "mate":
                    rec["pv20_mate"] = pv_is_mate(fen, r20["value"], r20["pv"])
            out.write(json.dumps(rec) + "\n")
            out.flush()
            if i % 25 == 0:
                print(f"  {i}/{len(fens)}", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
