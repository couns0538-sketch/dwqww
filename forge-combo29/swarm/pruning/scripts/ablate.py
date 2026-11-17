#!/usr/bin/env python3
"""Attribute each mate defect to a pruning class by removing that class.

For a defect row, re-run with each ablation class switched off:
  * if the row becomes correct with class X off, X is a CANDIDATE CAUSE;
  * if the row stays wrong with X off, X is EXCLUDED for that row;
  * if the row is wrong with EVERY class off, the cause is not in this set
    (or is the depth limit, not pruning) and the row must be reported as
    unattributed rather than blamed on a feature.

Ablation is attribution only. No headline number comes from an ablated build;
the shipped engine is the unablated one. Every reported row names its arm.
"""

from __future__ import annotations

import argparse
import json
import sys

sys.path.insert(0, "scripts")
from ucidrv import Engine, check_fen  # noqa: E402

CLASSES = ["null_move", "razor", "rfp", "futility", "lmr", "singular"]


def get_stats(engine: Engine) -> dict:
    engine.send("probestats")
    line = engine._read_until(lambda l: l.startswith("probestats"))[-1]
    return json.loads(line[len("probestats"):])


def run(engine: Engine, fen: str, depth: int, arm: str) -> dict:
    engine.newgame()
    check_fen(engine, fen)
    engine.send(f"ablate {arm}")
    engine.isready()
    res = engine.go(f"depth {depth}")
    counts = get_stats(engine)
    last = res.last
    return {
        "arm": arm,
        "depth": depth,
        "bestmove": res.bestmove,
        "score_mate": last.score_mate if last else None,
        "score_cp": last.score_cp if last else None,
        "nodes": res.nodes,
        "pv": last.pv if last else [],
        "counts": counts,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", default="evidence/mate_safety_rows.json")
    ap.add_argument("--engine", default="build/probe/forge")
    ap.add_argument("--min-depth", type=int, default=8)
    ap.add_argument("--out", default="evidence/ablation.json")
    args = ap.parse_args()

    with open(args.rows) as fh:
        rows = json.load(fh)
    # Defects that survive a deep search are the only ones worth attributing:
    # a shallow row is explained by depth, not by a pruning bug.
    targets = [r for r in rows if r["defect"] and r["depth"] >= args.min_depth]
    seen: set[tuple[str, int]] = set()
    uniq = []
    for r in targets:
        key = (r["fen"], r["depth"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(r)

    engine = Engine(args.engine, {"Threads": "1", "Hash": "64", "OwnBook": "false"})
    report = []
    try:
        for r in uniq:
            fen, depth = r["fen"], r["depth"]
            mating = set(r["mating_moves"])
            want = r["true_moves"]
            base = run(engine, fen, depth, "none")
            entry = {"fen": fen, "depth": depth, "true_moves": want,
                     "mating_moves": sorted(mating), "base": base, "arms": {}}
            for cls in CLASSES:
                arm = run(engine, fen, depth, cls)
                fixed = arm["bestmove"] in mating and arm["score_mate"] == want
                entry["arms"][cls] = {"result": arm, "fixes": fixed}
            alloff = run(engine, fen, depth, "all")
            entry["all_off"] = {
                "result": alloff,
                "fixes": alloff["bestmove"] in mating and alloff["score_mate"] == want,
            }
            entry["attributed_to"] = [c for c in CLASSES if entry["arms"][c]["fixes"]]
            report.append(entry)
            print(f"{fen} d{depth}: base={base['bestmove']}/m{base['score_mate']} "
                  f"-> fixed_by={entry['attributed_to'] or 'NONE'} "
                  f"all_off={alloff['bestmove']}/m{alloff['score_mate']}", flush=True)
    finally:
        engine.close()

    with open(args.out, "w") as fh:
        json.dump(report, fh, indent=1)

    print()
    for e in report:
        verdict = ("CAUSED BY " + ",".join(e["attributed_to"])) if e["attributed_to"] else (
            "NOT PRUNING (survives every ablation)" if not e["all_off"]["fixes"]
            else "COMBINATION (no single class)")
        print(f"{e['fen']:38s} d{e['depth']:<3d} {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
