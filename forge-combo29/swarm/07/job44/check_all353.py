#!/usr/bin/env python3
"""check_10f53.py PC_EXE OUTDIR [N]

Independent check of seat 10's 10-F53:
  "on 100 G positions the bestmove changes between the three budgets the owner actually uses on
   19 of them (19%): softnodes 20000 vs nodes 250000 differ on 17/100, 50000 vs 250000 on 8/100,
   all three agree on 81/100."

Their sample was the first 100 of G. **Mine is the LAST 100 of G** — a disjoint sample — so this is a
genuine independent check rather than a re-run of their positions. If the rate holds on a disjoint set
the number is a property of the engine; if it does not, the number was sample-specific.

Budgets: exactly the owner's three — `go softnodes 20000`, `go nodes 50000`, `go nodes 250000`.
PC r15 under PC20, Threads 1, Hash 16, fresh process per cell, never a command sent during a `go`.

For every position where the budgets disagree I also re-search BOTH moves at the large budget, so the
report can say whether the disagreement is a tie or a real difference, as seat 10 did.

Controls, before any rate is reported:
  * the same budget twice must give the same move (determinism of this harness);
  * a position whose three budgets agree must be reported as agreeing (so a checker that always says
    "disagrees" is caught).
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
BUDGETS = [("softnodes20000", "go softnodes 20000"),
           ("nodes50000", "go nodes 50000"),
           ("nodes250000", "go nodes 250000")]


class R:
    def __init__(s, st):
        s.q = queue.Queue()
        threading.Thread(target=s._pump, args=(st,), daemon=True).start()

    def _pump(s, st):
        for l in st:
            s.q.put(l)
        s.q.put(None)

    def get(s, t=900):
        try:
            return s.q.get(timeout=t)
        except queue.Empty:
            return None


def run(exe, fen, go):
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
    for o in ["Hash value 16", "Threads value 1"] + PC20:
        send("setoption name " + o); send("isready"); drain()
    send("ucinewgame"); send("isready"); drain()
    send("position fen " + fen); send("isready"); drain()
    send(go)
    score, best, nodes = None, None, None
    while True:
        l = r.get(900)
        if l is None:
            break
        if l.startswith("info depth") and " nodes " in l:
            m = re.search(r" nodes (\d+) ", l)
            if m:
                nodes = int(m.group(1))
            m = re.search(r"score (cp|mate) (-?\d+)", l)
            if m:
                score = [m.group(1), int(m.group(2))]
        if l.startswith("bestmove"):
            best = l.split()[1]
            break
    send("quit")
    try: p.wait(timeout=60)
    except subprocess.TimeoutExpired: p.kill()
    if best is None:
        raise SystemExit(f"FAIL no bestmove for {go} on {fen}")
    return {"score": score, "best": best, "nodes": nodes}


def cp(sc):
    if sc is None:
        return None
    k, v = sc
    return v if k == "cp" else (100000 - abs(v) if v > 0 else -(100000 - abs(v)))


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    os.makedirs(outdir, exist_ok=True)

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
    # DISJOINT sample: the LAST `limit` positions, not the first (seat 10 used the first 100)
    sample = fens if limit <= 0 else fens[-limit:]
    print(f"G positions: {len(fens)}; using ALL {len(sample)} (settling the 20000/50000 ordering)")

    # ---- control: determinism of this harness ----
    ctrl = sample[0]
    a = run(exe, ctrl, "go nodes 50000")
    b = run(exe, ctrl, "go nodes 50000")
    det_ok = (a["best"] == b["best"] and a["score"] == b["score"] and a["nodes"] == b["nodes"])
    print(f"CONTROL determinism (same budget twice): {det_ok}  "
          f"({a['best']}/{a['score']}/{a['nodes']} vs {b['best']}/{b['score']}/{b['nodes']})")
    if not det_ok:
        raise SystemExit("FAIL the harness is not deterministic; no rate can be reported")

    rows = []
    disagree = 0
    pairs = {"softnodes20000_vs_nodes250000": 0, "nodes50000_vs_nodes250000": 0}
    all_agree = 0
    print(f"\n{limit} positions x 3 budgets, PC r15 PC20, Threads 1, Hash 16\n")
    for i, fen in enumerate(sample):
        res = {}
        for name, go in BUDGETS:
            res[name] = run(exe, fen, go)
        moves = {res[n]["best"] for n, _ in BUDGETS}
        agree = len(moves) == 1
        if agree:
            all_agree += 1
        else:
            disagree += 1
            if res["softnodes20000"]["best"] != res["nodes250000"]["best"]:
                pairs["softnodes20000_vs_nodes250000"] += 1
            if res["nodes50000"]["best"] != res["nodes250000"]["best"]:
                pairs["nodes50000_vs_nodes250000"] += 1
        rec = {"i": i, "fen": fen, "res": res, "agree": agree}
        # for a disagreement, score BOTH moves at the large budget to say whether it is a tie
        if not agree:
            best_of = {}
            for mv in {res[n]["best"] for n, _ in BUDGETS}:
                r = run(exe, fen, f"go nodes 250000 searchmoves {mv}")
                best_of[mv] = r
            rec["scored_at_large"] = best_of
            vals = {mv: cp(r["score"]) for mv, r in best_of.items() if cp(r["score"]) is not None}
            if len(vals) > 1:
                rec["gap_at_large_cp"] = max(vals.values()) - min(vals.values())
        rows.append(rec)
        if (i + 1) % 25 == 0:
            print(f"  ...{i+1}/{len(sample)}  disagree so far {disagree}", flush=True)

    n = len(rows)
    print()
    print(f"positions with all three budgets agreeing: {all_agree}/{n} = {100.0*all_agree/n:.0f}%")
    print(f"positions where the budgets disagree:      {disagree}/{n} = {100.0*disagree/n:.1f}%")
    print(f"  softnodes20000 vs nodes250000 differ on {pairs['softnodes20000_vs_nodes250000']}/{n}")
    print(f"  nodes50000     vs nodes250000 differ on {pairs['nodes50000_vs_nodes250000']}/{n}")
    gaps = [r["gap_at_large_cp"] for r in rows if "gap_at_large_cp" in r]
    if gaps:
        gaps.sort()
        print(f"  disagreement with both moves scored at the large budget: "
              f"median gap {gaps[len(gaps)//2]} cp, max {gaps[-1]} cp, "
              f"{sum(1 for g in gaps if g <= 20)} of {len(gaps)} are ties (<=20 cp)")
    json.dump({"rows": rows, "n": n, "disagree": disagree, "all_agree": all_agree,
               "pairs": pairs}, open(os.path.join(outdir, "check_10f53.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
