#!/usr/bin/env python3
"""How BIG is the threaded score instability? Computed from the saved determinism runs.

An owner who trains on threaded output or reads a threaded score needs the magnitude,
not just the rate. For each position and thread count this reports the spread across
repeats (max - min) of the score, and the spread of the node count as a RATIO
(max/min), because a node count has no natural zero and an absolute difference across
positions of different size is not comparable.

Also reported: the spread at Threads 1, which must be exactly 0 -- that is the
control, and a nonzero value there would mean the harness, not the engine.

Usage: python3 score_spread.py <determinism.jsonl> [more.jsonl...]
"""
import json
import statistics
import sys
from collections import defaultdict


def summarise(path):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    by_key = defaultdict(list)
    for r in rows:
        by_key[(r["threads"], r["idx"])].append(r["sig"])
    per_thread = defaultdict(lambda: {"score_spreads": [], "node_ratios": [], "n": 0})
    for (th, idx), sigs in by_key.items():
        usable = [s for s in sigs if not s["no_info_depth"]]
        if len(usable) < 2:
            continue
        per_thread[th]["n"] += 1
        scores = [s["score"] for s in usable if s.get("score") is not None]
        nodes = [s["nodes"] for s in usable if s.get("nodes")]
        if len(scores) >= 2:
            per_thread[th]["score_spreads"].append(max(scores) - min(scores))
        if len(nodes) >= 2 and min(nodes) > 0:
            per_thread[th]["node_ratios"].append(max(nodes) / min(nodes))
    return per_thread


def main():
    for path in sys.argv[1:]:
        per_thread = summarise(path)
        print(f"=== {path} ===")
        print(f"{'thr':>4} {'pos':>4} {'score spread cp':>16} {'':>8} {'node ratio max/min':>19} {'':>8}")
        for th in sorted(per_thread):
            d = per_thread[th]
            ss = d["score_spreads"]
            nr = d["node_ratios"]
            print(f"{th:>4} {d['n']:>4} median={statistics.median(ss):>5.0f} max={max(ss):>4.0f}"
                  f"{'':>8} median={statistics.median(nr):>6.2f} max={max(nr):>5.2f}")
        print()


if __name__ == "__main__":
    main()
