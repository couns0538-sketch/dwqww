#!/usr/bin/env python3
"""mpv_compare.py EXE FENS OUTJSONL DEPTH : for each position, free search at MultiPV 1 and MultiPV 3.

Records the best move, the score, and the PV length for both, plus for every mate report whether the PV replays
legally and ends in checkmate. The question this answers: at ONE depth with everything else fixed, does asking for
three lines change the mate number the engine reports as best?

Fresh process per search per setting; no state shared between the two configurations.
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


def search(exe, fen, depth, mpv):
    p = subprocess.Popen(shlex.split(exe), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    if mpv > 1:
        p.stdin.write(f"setoption name MultiPV value {mpv}\n")
    for n, v in S14:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"go depth {depth}\n"); p.stdin.flush()
    lines, best = [], None
    for line in p.stdout:
        s = line.rstrip("\n")
        if s.startswith("info depth"):
            lines.append(s)
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=180)
    except subprocess.TimeoutExpired:
        p.kill()
    by = {}
    for l in lines:
        t = l.split()
        m = re.search(r"score (cp|mate) (-?\d+)", l)
        idx = int(t[t.index("multipv") + 1]) if "multipv" in t else 1
        pv = t[t.index("pv") + 1:] if "pv" in t else []
        by[idx] = {"kind": m.group(1) if m else None,
                   "value": int(m.group(2)) if m else None,
                   "pv": pv}
    return {"bestmove": best, "lines": by}


def pv_ok(fen, kind, value, pv):
    if kind != "mate" or not pv:
        return None
    b = chess.Board(fen)
    for u in pv:
        try:
            m = chess.Move.from_uci(u)
        except ValueError:
            return False
        if m not in b.legal_moves:
            return False
        b.push(m)
    need = 2 * value - 1 if value > 0 else 2 * abs(value)
    return b.is_checkmate() and len(pv) == need


def main():
    exe, fenfile, outfile, depth = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    fens = [l.strip() for l in open(fenfile) if l.strip() and not l.startswith("#")]
    print(f"{len(fens)} positions, MultiPV 1 vs 3 at depth {depth}", flush=True)
    with open(outfile, "w") as out:
        for i, fen in enumerate(fens):
            a = search(exe, fen, depth, 1)
            c = search(exe, fen, depth, 3)
            rec = {"i": i, "fen": fen, "mpv1": a, "mpv3": c}
            for tag, r in (("mpv1", a), ("mpv3", c)):
                top = r["lines"].get(1)
                if top:
                    rec[tag + "_pv_ok"] = pv_ok(fen, top["kind"], top["value"], top["pv"])
            out.write(json.dumps(rec) + "\n")
            out.flush()
            if i % 20 == 0:
                print(f"  {i}/{len(fens)}", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
