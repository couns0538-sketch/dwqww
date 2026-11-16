#!/usr/bin/env python3
"""budget_moves.py OUTDIR -- how often does the bestmove change between the three budgets the owner uses?

100 positions from G (first 100 of set_G.epd). Each position searched at
  softnodes 20000, softnodes 50000, nodes 250000
PC r15 under PC20, Threads 1, Hash 16, fresh process per (position, budget), read to `bestmove`.

For every position where the moves disagree we also record the scores, and for every pair where the SMALL
budget's move is not the LARGE budget's move we run ONE extra search: the large budget restricted to the
small budget's move (`go nodes 250000 searchmoves <mv>`), so the score gap is the engine's own evaluation
of the two moves at the same budget rather than a comparison across budgets. That is the number that says
whether the small budget made a worse choice, not merely a different one.

Usage: budget_moves.py OUTDIR [N_POSITIONS]
"""
import json
import os
import re
import subprocess
import sys

import chess

PC = os.path.expanduser("~/builds/pc/forge")
OUT = os.path.abspath(sys.argv[1])
NPOS = int(sys.argv[2]) if len(sys.argv) > 2 else 100
os.makedirs(OUT, exist_ok=True)
G = "/agent/repos/dwqww/forge-combo29/swarm/10/pc/raw/sets/set_G.epd"
if not os.path.exists(G):
    G = "/agent/repos/dwqww/forge-combo29/swarm/10/audit/raw/sets/set_G.epd"

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

BUDGETS = ["go softnodes 20000", "go softnodes 50000", "go nodes 250000"]


def one(poscmd, go):
    lines = ["uci", "isready", "setoption name Threads value 1", "setoption name Hash value 16"]
    lines += ["setoption name %s value %s" % kv for kv in PC20]
    lines += ["isready", "ucinewgame", "isready", poscmd, "isready", go]
    p = subprocess.Popen([PC], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    for l in lines:
        p.stdin.write(l + "\n")
        p.stdin.flush()
    out = []
    while True:
        line = p.stdout.readline()
        if not line:
            break
        out.append(line.rstrip())
        if line.startswith("bestmove"):
            break
    p.stdin.write("quit\n")
    try:
        p.stdin.flush()
    except Exception:
        pass
    try:
        p.wait(timeout=180)
    except Exception:
        p.kill()
    last = [l for l in out if l.startswith("info depth")]
    last = last[-1] if last else ""
    nodes = depth = score = None
    if " nodes " in last:
        try:
            nodes = int(last.split(" nodes ")[1].split()[0])
        except (IndexError, ValueError):
            pass
    if last.startswith("info depth"):
        try:
            depth = int(last.split("depth ")[1].split()[0])
        except (IndexError, ValueError):
            pass
    m = re.search(r" score (cp|mate) (-?\d+)", last)
    if m:
        score = (m.group(1), int(m.group(2)))
    best = None
    for l in out:
        if l.startswith("bestmove"):
            best = l.split()[1]
    return {"bestmove": best, "score": score, "depth": depth, "nodes": nodes}


def cp_of(score):
    if not score:
        return None
    if score[0] == "cp":
        return score[1]
    return None            # mates are not comparable as centipawns; reported separately


fens = []
for line in open(G):
    line = line.strip()
    if line:
        fens.append(line.split(";")[0].strip())
fens = fens[:NPOS]

rows = []
for i, fen in enumerate(fens):
    try:
        legal = {m.uci() for m in chess.Board(fen).legal_moves}
    except ValueError:
        continue
    rec = {"i": i, "fen": fen, "runs": {}}
    for b in BUDGETS:
        rec["runs"][b] = one("position fen " + fen, b)
    # legality of every answer
    for b, r in rec["runs"].items():
        r["legal"] = (r["bestmove"] in legal) if r["bestmove"] else None
    b20, b50, b250 = (rec["runs"][x]["bestmove"] for x in BUDGETS)
    rec["agree_all3"] = (b20 == b50 == b250)
    rec["agree_20_250"] = (b20 == b250)
    rec["agree_50_250"] = (b50 == b250)
    rec["agree_20_50"] = (b20 == b50)
    # when the small budget's move differs from the large budget's, score the small move AT the large budget
    if b20 and b250 and b20 != b250:
        rec["small_move_at_large_budget"] = one(
            "position fen " + fen, "go nodes 250000 searchmoves " + b20)
    rows.append(rec)
    if i % 10 == 0:
        print("  %d/%d agree_all3 so far: %d"
              % (i, len(fens), sum(1 for x in rows if x["agree_all3"])), flush=True)
        with open(os.path.join(OUT, "budget_moves.json"), "w") as f:
            json.dump(rows, f, indent=1)
            f.write("\n")

with open(os.path.join(OUT, "budget_moves.json"), "w") as f:
    json.dump(rows, f, indent=1)
    f.write("\n")

n = len(rows)
disagree_all3 = [r for r in rows if not r["agree_all3"]]
d20250 = [r for r in rows if not r["agree_20_250"]]
d50250 = [r for r in rows if not r["agree_50_250"]]
d2050 = [r for r in rows if not r["agree_20_50"]]

# score-gap statistics where 20000 and 250000 differ, using only numeric cp scores
gaps_same_budget = []
for r in d20250:
    sm = r.get("small_move_at_large_budget")
    big = r["runs"][BUDGETS[2]]
    a, b = cp_of(big.get("score")), cp_of(sm.get("score")) if sm else None
    if a is not None and b is not None:
        # the large budget's own choice minus the small budget's move, both at the large budget
        gaps_same_budget.append(abs(a - b))
gaps_cross = []
for r in d20250:
    a = cp_of(r["runs"][BUDGETS[0]].get("score"))
    b = cp_of(r["runs"][BUDGETS[2]].get("score"))
    if a is not None and b is not None:
        gaps_cross.append(abs(a - b))


def med(xs):
    xs = sorted(xs)
    if not xs:
        return None
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2


summary = {
    "positions": n,
    "agree_all_three": sum(1 for r in rows if r["agree_all3"]),
    "disagree_all_three": len(disagree_all3),
    "disagree_20000_vs_250000": len(d20250),
    "disagree_50000_vs_250000": len(d50250),
    "disagree_20000_vs_50000": len(d2050),
    "agree_50000_vs_250000": n - len(d50250),
    "median_cross_budget_score_gap_cp": med(gaps_cross),
    "max_cross_budget_score_gap_cp": max(gaps_cross) if gaps_cross else None,
    "median_same_budget_score_gap_cp": med(gaps_same_budget),
    "max_same_budget_score_gap_cp": max(gaps_same_budget) if gaps_same_budget else None,
    "positions_with_a_200cp_worse_small_choice": sum(1 for g in gaps_same_budget if g >= 200),
    "illegal_bestmoves": sum(1 for r in rows for x in r["runs"].values() if x["legal"] is False),
    "examples": [{"fen": r["fen"], "m20": r["runs"][BUDGETS[0]]["bestmove"],
                  "m50": r["runs"][BUDGETS[1]]["bestmove"],
                  "m250": r["runs"][BUDGETS[2]]["bestmove"],
                  "s20": r["runs"][BUDGETS[0]]["score"], "s250": r["runs"][BUDGETS[2]]["score"]}
                 for r in disagree_all3[:10]],
}
with open(os.path.join(OUT, "budget_moves_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)
    f.write("\n")
print(json.dumps(summary, indent=2))
