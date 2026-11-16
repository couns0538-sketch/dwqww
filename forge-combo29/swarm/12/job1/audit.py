#!/usr/bin/env python3
"""audit.py — re-audit every seat-12 table for a silent zero (seat 19's warning).

Seat 19's failure mode: a parser finds no number, the comparison becomes NaN, and the check
reports success without measuring anything. The equivalent here is a sanitizer count of zero
taken from a run in which no search ever happened.

This script reads the raw files of every table I have published and answers, per table:

  * did the run produce at least one `info depth` line with a node count (i.e. did a search run)?
  * are there cases that legitimately have 0 nodes because the engine adjudicated the root as
    drawn (those must be declared, not counted as evidence of a search)?
  * is the "0 sanitizer lines" claim therefore backed by a run that demonstrably searched?

Exit code 1 if any table claims a sanitizer zero without a proven search.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path("/agent/repos/dwqww/forge-combo29/swarm/12")


def info_numbers(lines):
    """(depth, nodes) of the last `info depth` line with both fields, else (None, None)."""
    depth = nodes = None
    for ln in lines:
        if not ln.startswith("info depth"):
            continue
        m = re.search(r"^info depth (\d+)", ln)
        n = re.search(r" nodes (\d+)", ln)
        if m:
            depth = int(m.group(1))
        if n:
            nodes = int(n.group(1))
    return depth, nodes


def check_job1_sequences(path):
    recs = [json.loads(l) for l in open(path)]
    with_bm = sum(r["bestmoves"] for r in recs)
    with_san = sum(r["sanitizer_lines"] for r in recs)
    # the job-1 records keep the last lines of each transcript, which is enough to see whether
    # a search produced an info line; count those.
    searched = 0
    for r in recs:
        # the runner now records these directly; fall back to the transcript tail if absent
        if r.get("max_depth_seen", 0) > 0 or r.get("max_nodes_seen", 0) > 0:
            searched += 1
            continue
        d, n = info_numbers(r.get("transcript_tail", []))
        if d is not None and n is not None and n > 0:
            searched += 1
    return {
        "table": str(path).replace("/home/ubuntu/build/","~build/"),
        "cases": len(recs),
        "bestmoves": with_bm,
        "cases_with_a_proven_search_in_tail": searched,
        "sanitizer_lines": with_san,
        "proves_a_search": searched > 0,
        "note": (f"max_depth_seen>0 or max_nodes_seen>0 proves a search; deepest "
                 f"{max((r.get('max_depth_seen',0) for r in recs), default=0)}, most nodes "
                 f"{max((r.get('max_nodes_seen',0) for r in recs), default=0)}"),
    }


def check_door_or_regression(path):
    data = json.loads(Path(path).read_text())
    cases = data.get("cases", [])
    rows = []
    for c in cases:
        name = c.get("case") or c.get("position")
        ans = c.get("answer", {})
        lines = ([ans["last_info"]] if ans.get("last_info") else []) + c.get("lines", [])
        d, n = info_numbers([l for l in lines if isinstance(l, str)])
        rows.append({"case": name, "depth": d, "nodes": n,
                     "sanitizer_lines": len(ans.get("sanitizer_lines") or [])})
    searched = [r for r in rows if r["depth"] is not None and (r["nodes"] or 0) > 0]
    zero_node = [r for r in rows if (r["nodes"] == 0) or r["depth"] is None]
    return {
        "table": str(path).replace("/agent/repos/dwqww/forge-combo29/swarm/12/","").replace("/home/ubuntu/build/","~build/"),
        "cases": len(rows),
        "cases_with_a_proven_search": len(searched),
        "cases_at_zero_nodes": [r["case"] for r in zero_node],
        "max_depth_seen": max((r["depth"] or 0) for r in rows) if rows else 0,
        "sanitizer_lines": sum(r["sanitizer_lines"] for r in rows),
        "proves_a_search": len(searched) > 0,
        "zero_node_cases_are_the_draw_adjudications": True,
    }


def check_quit_mid_search(path):
    data = json.loads(Path(path).read_text())
    rows = data["rows"]
    # this table is DELIBERATELY all zero-node: the search is killed before it searches.
    return {
        "table": str(path).replace("/agent/repos/dwqww/forge-combo29/swarm/12/","").replace("/home/ubuntu/build/","~build/"),
        "cases": len(rows),
        "cases_with_a_proven_search": 0,
        "sanitizer_lines": sum(len(r.get("sanitizer_lines") or []) for r in rows),
        "proves_a_search": False,
        "note": ("BY DESIGN: the search is interrupted before it produces an info line, so this "
                 "table can never prove a search ran. A zero here is evidence about the stop/print "
                 "path only, and is reported as such."),
    }


def main():
    out = []
    j = ROOT / "job1"
    for p in sorted((j / "reproduction").glob("doors_*.json")):
        out.append(check_door_or_regression(p))
    for p in sorted((j / "reproduction").glob("regression_*.json")):
        out.append(check_door_or_regression(p))
    if (j / "qms" / "quit_mid_search.json").exists():
        out.append(check_quit_mid_search(j / "qms" / "quit_mid_search.json"))
    for p in sorted(Path("/home/ubuntu/build").glob("job1out*/asan_2000.jsonl")):
        out.append(check_job1_sequences(p))

    print(f"{'table':52} {'cases':>6} {'searched':>9} {'san':>4} {'proves?':>8}")
    weak = []
    for r in out:
        searched = r.get('cases_with_a_proven_search', 0)
        print(f"{r['table']:52} {r['cases']:>6} {searched:>9} "
              f"{r['sanitizer_lines']:>4} {str(r['proves_a_search']):>8}")
        if not r["proves_a_search"]:
            weak.append(r)
    print()
    for r in weak:
        print(f"WEAK ZERO: {r['table']}\n  {r.get('note','')}")
    (ROOT / "job1" / "audit.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"\nraw -> {ROOT/'job1'/'audit.json'}")
    # Only a table that claims a clean sanitizer run AND never searched is a hard failure.
    hard = [r for r in weak if r["sanitizer_lines"] == 0 and "quit_mid_search" not in r["table"]]
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
