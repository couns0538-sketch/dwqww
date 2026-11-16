#!/usr/bin/env python3
"""seat 17: does the BESTMOVE change across the match path's three budgets?

File 6 says the owner's matches use `go nodes` 20000, 50000 and 250000. If the answer changes with the
budget, the three are different players at the same position. Ten real-game positions (set G), PC r15,
PC20, Threads 1, Hash 16, fresh process per (position, budget), read to bestmove.

Independent check of another seat's 100-position run; deliberately small.

usage: budget_move.py <exe> <epd> <outdir> [count]
"""
import json
import os
import sys

sys.path.insert(0, "/agent/repos/dwqww/forge-combo29/swarm/17/job1")
from uci_driver import run_one

S14 = [
    ("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
    ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
    ("IirDepth", "2"), ("NonPawnCorrection", "true"),
]
PC20_EXTRA = [
    ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
    ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false"),
]
PC20 = S14 + PC20_EXTRA
BUDGETS = (20000, 50000, 250000)


def opts():
    out = []
    for name, value in PC20:
        out += ["setoption name %s value %s" % (name, value), "isready"]
    return out


def main():
    exe, epd, outdir = sys.argv[1:4]
    count = int(sys.argv[4]) if len(sys.argv) > 4 else 10
    os.makedirs(outdir, exist_ok=True)
    fens = [line.split(";")[0].strip() for line in open(epd) if line.strip()][:count]
    rows = []
    for index, fen in enumerate(fens):
        moves = {}
        scores = {}
        for budget in BUDGETS:
            log = os.path.join(outdir, "p%d_%d.log" % (index, budget))
            info = run_one(exe, ["uci", "isready"] + opts() + ["position fen " + fen, "isready",
                                                               "go nodes %d" % budget], 240, log)
            text = open(log).read()
            depth_lines = [l for l in text.splitlines() if l.startswith("info depth")]
            last = depth_lines[-1] if depth_lines else ""
            score = None
            if " score " in last:
                score = last.split(" score ")[1].split(" pv")[0]
            moves[budget] = info["bestmove"]
            scores[budget] = score
        distinct = len({m for m in moves.values() if m})
        row = {"index": index, "fen": fen, "moves": moves, "scores": scores,
               "distinct_bestmoves": distinct}
        rows.append(row)
        print(json.dumps(row), flush=True)
    agree = sum(1 for r in rows if r["distinct_bestmoves"] == 1)
    summary = {
        "positions": len(rows),
        "all_three_budgets_same_move": agree,
        "positions_where_budget_changes_the_move": len(rows) - agree,
        "budgets": list(BUDGETS),
        "note": "move strings include the 'bestmove ' prefix as the driver returns it",
    }
    json.dump({"summary": summary, "rows": rows}, open(os.path.join(outdir, "budget_move.json"), "w"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
