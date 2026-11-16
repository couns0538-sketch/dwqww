#!/usr/bin/env python3
"""sum_delta.py BASE_S14_JSON PC20_JSON OUTDIR

Reports the per-position difference between base-under-S14 and PC-under-PC20 for the same set, so a
reader can see WHICH positions changed and by how much — the coordinator's point: one aggregate tells
you the totals moved, a per-position table tells you whether the PC's search changes are broad or narrow.

Inputs are the two sum_*.json files this seat already produced:
  job9/raw/sum_d12.json           base tree, S14,  depth 12, 200 positions  (07-C3)
  job30/raw/sum_PC20_d12.json     PC r15, PC20, depth 12, 200 positions     (07-C26)

Caveat stated up front and repeated in the output: the two runs differ in BOTH build and settings, so
a per-position difference cannot be attributed to the PC's search changes alone. This is a
characterisation of the pair of configurations the owner actually uses, not a controlled experiment.
"""
import json
import os
import statistics
import sys


def normalise(row):
    """Two of this seat's own runs used slightly different row schemas; accept either."""
    return {
        "i": row.get("i", row.get("index")),
        "fen": row["fen"],
        "nodes": row["nodes"],
        "best": row.get("best"),
        "score": row.get("score", row.get("last_score_line")),
    }


def load(path, key="rows"):
    d = json.load(open(path))
    return [normalise(r) for r in d.get(key, d)], d.get("sum")


def main():
    base_path, pc_path, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(outdir, exist_ok=True)
    base, base_sum = load(base_path)
    pc, pc_sum = load(pc_path)
    if len(base) != len(pc):
        raise SystemExit(f"FAIL position counts differ: {len(base)} vs {len(pc)}")

    rows = []
    for b, p in zip(base, pc):
        if b["fen"] != p["fen"]:
            raise SystemExit(f"FAIL fen mismatch at {b['i']}: {b['fen']} vs {p['fen']}")
        delta = p["nodes"] - b["nodes"]
        rows.append({"i": b["i"], "fen": b["fen"], "base_nodes": b["nodes"], "pc_nodes": p["nodes"],
                     "delta": delta, "base_best": b["best"], "pc_best": p["best"],
                     "base_score": b["score"], "pc_score": p["score"],
                     "same_bestmove": b["best"] == p["best"],
                     "same_score": b["score"] == p["score"]})

    deltas = [r["delta"] for r in rows]
    absd = [abs(d) for d in deltas]
    sign_same = sum(1 for d in deltas if d > 0)
    changed_move = [r for r in rows if not r["same_bestmove"]]
    changed_score = [r for r in rows if not r["same_score"]]
    changed_nodes = [r for r in rows if r["delta"] != 0]

    out = []
    out.append("BASE-S14 vs PC-PC20, set O, depth 12, 200 positions")
    out.append(f"base sum {base_sum}   pc sum {pc_sum}   difference {pc_sum - base_sum}")
    out.append("")
    out.append("CAVEAT: the two runs differ in BOTH build and settings (base+S14 vs PC+PC20), so a")
    out.append("per-position difference is a property of the PAIR, not of the PC's search alone.")
    out.append("")
    out.append(f"positions where the node count changed : {len(changed_nodes)} of {len(rows)}")
    out.append(f"  node count increased on PC           : {sign_same}")
    out.append(f"  node count decreased on PC           : {len([d for d in deltas if d < 0])}")
    out.append(f"  identical node count                 : {len(rows) - len(changed_nodes)}")
    out.append(f"positions where the BESTMOVE changed   : {len(changed_move)}")
    out.append(f"positions where the SCORE changed      : {len(changed_score)}")
    out.append("")
    if deltas:
        out.append(f"delta nodes: min {min(deltas)}  median {int(statistics.median(deltas))}  "
                   f"max {max(deltas)}  mean {statistics.mean(deltas):.1f}")
        out.append(f"|delta| nodes: median {int(statistics.median(absd))}  "
                   f"90th pct {sorted(absd)[int(0.9 * len(absd)) - 1]}  max {max(absd)}")
    out.append("")
    out.append("HOW BROAD IS IT?")
    n_all = len(rows)
    for label, count in [("node count changed", len(changed_nodes)),
                         ("bestmove changed", len(changed_move)),
                         ("score changed", len(changed_score))]:
        out.append(f"  {label:20s} {count:3d}/{n_all} = {100.0 * count / n_all:5.1f}%")
    out.append("")
    out.append("Largest 15 changes by |delta| (fen, base nodes -> pc nodes, delta, bestmove change):")
    for r in sorted(rows, key=lambda x: -abs(x["delta"]))[:15]:
        bm = "" if r["same_bestmove"] else f"   bestmove {r['base_best']} -> {r['pc_best']}"
        out.append(f"  {r['i']:3d} {r['fen'][:52]:54s} {r['base_nodes']:8d} -> {r['pc_nodes']:8d} "
                   f"({r['delta']:+8d}){bm}")
    out.append("")
    out.append("Positions where the bestmove changed (all of them):")
    if not changed_move:
        out.append("  none")
    for r in changed_move:
        out.append(f"  {r['i']:3d} {r['fen'][:52]:54s} {r['base_best']} -> {r['pc_best']}   "
                   f"score {r['base_score']} -> {r['pc_score']}")

    text = "\n".join(out) + "\n"
    open(os.path.join(outdir, "sum_delta.txt"), "w").write(text)
    json.dump(rows, open(os.path.join(outdir, "sum_delta.json"), "w"), indent=1)
    print(text)


if __name__ == "__main__":
    main()
