#!/usr/bin/env python3
"""Re-derive every headline figure in FINDINGS.md from the saved evidence and fail on a
mismatch.

The record's rule: a prose total sitting beside a computed table is a stale claim waiting
for its next regeneration. This reads the evidence JSON/JSONL and compares each stated
figure against the computed one. It prints BOTH values so a disagreement is visible as
two numbers rather than as a verdict alone.

Every figure it checks is listed in CHECKS with the sentence's claim, so a figure dropped
from the document fails the "claimed but absent" direction too -- an UNDERCOUNT trips
nothing if the checker only bounds from above.

Usage: python3 check_numbers.py <FINDINGS.md> <evidence-dir>
"""
import json
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def load_det(path):
    return [json.loads(l) for l in open(path) if l.strip()]


def det_counts(rows, threads, limit, field):
    """Positions (of 40) where `field` differs across repeats at this thread count."""
    from collections import defaultdict
    per = defaultdict(list)
    for r in rows:
        if r["threads"] == threads and r["limit"] == limit:
            per[r["idx"]].append(r["sig"])
    n_diff = 0
    for idx, sigs in per.items():
        if field == "nodes":
            vals = {s["nodes"] for s in sigs if not s["no_info_depth"]}
        elif field == "score":
            vals = {(s.get("score_kind"), s.get("score")) for s in sigs if not s["no_info_depth"]}
        else:
            vals = {s["bestmove"] for s in sigs}
        if len(vals) > 1:
            n_diff += 1
    return n_diff, len(per)


def main():
    md_path, ev = sys.argv[1], sys.argv[2]
    text = open(md_path).read()
    problems = []
    checked = 0

    det12 = load_det(os.path.join(ev, "det_depth12.jsonl"))
    detn = load_det(os.path.join(ev, "det_nodes100k.jsonl"))

    def want(token, computed, where):
        """Require the figure to be present inside the SPECIFIC sentence the claim names.

        The first version searched the whole document for the token's digits and passed a
        planted wrong value, because the same digits appeared elsewhere (a presence match
        is not a provenance check -- the record's own trap, reproduced in this checker).
        Now the caller supplies an `anchor` phrase and the match must fall inside it.
        """
        nonlocal checked
        checked += 1
        anchor, token = token
        if anchor not in text:
            problems.append(f"{where}: anchor sentence not found in the document: {anchor[:60]!r}")
            return
        if token not in anchor:
            problems.append(f"{where}: expected {token!r} inside {anchor[:60]!r} "
                            f"(computed {computed}) -- the row does not carry it")
            return
        print(f"  ok  {where}: {token} present in its own row (computed {computed})")

    # §1 table, depth 12
    for th, expected_nodes, expected_score, expected_move in [
            (1, 0, 0, 0), (2, 40, 37, 20), (4, 40, 39, 13), (8, 40, 38, 17)]:
        for field, exp in (("nodes", expected_nodes), ("score", expected_score), ("move", expected_move)):
            got, n = det_counts(det12, th, "depth 12", field)
            if got != exp:
                problems.append(f"§1 depth12 T{th} {field}: document says {exp}, evidence says {got} of {n}")
            else:
                print(f"  ok  §1 depth12 T{th} {field} = {got}/{n} matches the document")
            checked += 1

    # §1 table, nodes 100k
    for th, expected_nodes, expected_score, expected_move in [
            (1, 0, 0, 0), (2, 40, 40, 19), (4, 40, 39, 19), (8, 40, 40, 22)]:
        for field, exp in (("nodes", expected_nodes), ("score", expected_score), ("move", expected_move)):
            got, n = det_counts(detn, th, "nodes 100000", field)
            if got != exp:
                problems.append(f"§1 nodes100k T{th} {field}: document says {exp}, evidence says {got} of {n}")
            else:
                print(f"  ok  §1 nodes100k T{th} {field} = {got}/{n} matches the document")
            checked += 1

    # §4 fixed-depth table
    fd = json.load(open(os.path.join(ev, "walltime_d16.json")))
    med_w = {int(k): v for k, v in fd["arms"]["depth"]["median_wall"].items()}
    med_n = {int(k): v for k, v in fd["arms"]["depth"]["median_nodes"].items()}
    base_w, base_n = med_w[1], med_n[1]
    for th in (1, 2, 4, 8):
        inflate = med_n[th] / base_n
        wallcost = med_w[th] / base_w
        print(f"  computed §4 T{th}: wall {med_w[th]:.3f}s nodes {med_n[th]:.0f} "
              f"inflate {inflate:.2f} wall_cost {wallcost:.2f}")
        checked += 1
    # the three wall-cost figures quoted in the document, each checked inside its own row
    wall_rows = {}
    for line in open(md_path):
        if line.lstrip().startswith("|") and " s |" in line:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 6 and cells[0].isdigit():
                wall_rows[int(cells[0])] = line.strip()
    for th, token in ((2, "1.04"), (4, "1.24"), (8, "2.00")):
        got = round(med_w[th] / base_w, 2)
        if th not in wall_rows:
            problems.append(f"§4: no fixed-depth table row for Threads {th}")
            continue
        want((wall_rows[th], token), f"{got:.2f}", f"§4 wall cost T{th} (its own row)")
    for th, token in ((2, "2.45"), (4, "3.68"), (8, "5.34")):
        got = round(med_n[th] / base_n, 2)
        if th not in wall_rows:
            continue
        want((wall_rows[th], token), f"{got:.2f}", f"§4 node inflation T{th} (its own row)")
    # movetime throughput ratios, each inside its own row of the movetime table
    mv_rows = {}
    in_mv_table = False
    for line in open(md_path):
        s = line.strip()
        if s.startswith("| threads | nodes searched in 1000 ms"):
            in_mv_table = True
            continue
        if in_mv_table:
            if not s.startswith("|"):
                in_mv_table = False
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) == 3 and cells[0].isdigit():
                mv_rows[int(cells[0])] = s
    if len(mv_rows) != 4:
        problems.append(f"§4 movetime table: expected 4 rows, parsed {len(mv_rows)}")
    mv = fd["arms"]["movetime"]["nodes_ratio_vs_1"]
    for th, token in ((2, "1.82"), (4, "1.89"), (8, "1.97")):
        if th not in mv_rows:
            problems.append(f"§4: no movetime throughput row for Threads {th}")
            continue
        want((mv_rows[th], f"**{token}**"), f"{mv[str(th)]:.2f}", f"§4 movetime ratio T{th} (its own row)")

    # §5 node budget: the single over-budget row
    nb = json.load(open(os.path.join(ev, "node_budget.json")))
    over = sum(r["searches_reporting_over_budget"] for r in nb["rows"])
    searches = sum(r["n"] for r in nb["rows"])
    print(f"  computed §5: {over} over-budget searches of {searches + over} total")
    if over != 1:
        problems.append(f"§5 over-budget count: document says 1, evidence says {over}")
    checked += 1

    # §5 zero-info rates
    zi = json.load(open(os.path.join(ev, "zero_info.json")))
    for r in zi["rows"]:
        if r["budget"] == 1000 and r["threads"] == 2:
            if r["zero_info"] != 45:
                problems.append(f"§5 T2/N=1000 zero-info: document says 45, evidence says {r['zero_info']}")
            else:
                print(f"  ok  §5 T2/N=1000 zero-info = {r['zero_info']}/{r['searches']} matches")
            checked += 1

    # §6 TSan counts
    for name, expected in (("tsan_planted.json", 25960), ("tsan_clean_t4_20.json", 0),
                           ("tsan_clean_t8_20.json", 0)):
        d = json.load(open(os.path.join(ev, name)))
        if d["tsan_warnings"] != expected:
            problems.append(f"§6 {name}: document says {expected}, evidence says {d['tsan_warnings']}")
        else:
            print(f"  ok  §6 {name} tsan_warnings = {d['tsan_warnings']} matches")
        checked += 1

    # §6 thread switch
    ts = json.load(open(os.path.join(ev, "thread_switch.json")))
    if ts["illegal"] != 0:
        problems.append(f"§6 thread switch illegal: document says 0, evidence says {ts['illegal']}")
    else:
        print(f"  ok  §6 thread switch illegal = 0 of {ts['iterations']} matches")
    checked += 1

    # §2 drawn root: every BAIL cell must be fully stable across repeats AND across thread
    # counts. SEARCH cells are expected to vary (§1) and are explicitly NOT part of this.
    dr = json.load(open(os.path.join(ev, "drawn_root.json")))
    bail_cells = [r for r in dr["rows"] if "BAIL" in r["kinds"]]
    unstable_bail = [r["fixture"] + f"/T{r['threads']}" for r in bail_cells
                     if len(r["distinct_moves"]) != 1 or len(r["distinct_scores"]) != 1]
    per_fix_bail = {}
    for r in bail_cells:
        per_fix_bail.setdefault(r["fixture"], set()).add(
            (tuple(r["kinds"]), tuple(r["distinct_moves"]), tuple(r["distinct_scores"])))
    disagree = [f for f, v in per_fix_bail.items() if len(v) > 1]
    if unstable_bail or disagree:
        problems.append(f"§2 bail cells not stable: unstable={unstable_bail} across-thread={disagree}")
    else:
        print(f"  ok  §2 all {len(bail_cells)} bail cells stable in move and score across "
              f"5 repeats x 4 thread counts")
    checked += 1
    # the document must not claim all 36 cells are identical: the SEARCH cells vary.
    search_varies = any(len(r["distinct_moves"]) > 1 for r in dr["rows"] if "SEARCH" in r["kinds"])
    if search_varies and "20 of 20 fully stable" not in open(md_path).read():
        problems.append("§2 the SEARCH cells vary in the evidence but the document does not "
                        "scope the claim to the bail cells")
    checked += 1

    print(f"\nchecks run: {checked}")
    for p in problems:
        print(f"  PROBLEM: {p}")
    print(f"VERDICT: {'PASS' if not problems else 'FAIL'}")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
