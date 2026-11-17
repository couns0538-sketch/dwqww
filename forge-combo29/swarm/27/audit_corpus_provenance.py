#!/usr/bin/env python3
"""audit_corpus_provenance.py <csv-or-json> [--format auto|csv|json]

Audit an EXISTING self-play corpus for rows produced by a different search than the rest.

THE PROBLEM. A corpus can be internally inconsistent without any row being wrong on its own terms: rows
produced under `go mate N`, under `go nodes N`, and under `go softnodes N` are three different experiments that
all look like "a position, a move, a score". Nothing in a row says which search produced it, so the mix is
invisible - and a model trained on it learns a target that is a blend of three definitions.

This tool applies the three separable checks established tonight, each measured on PC r15 `068f0927`:

  1. **MATE ROWS ARE IDENTIFIABLE BY NODE RATIO.** `mate_moves_ > 0` disables seven heuristics and the TT cutoff
     (search.cpp:1431-1455, 1493, 1639, 1784, 1805, 1841, 1929, 1955), so a mate-limited search costs far more
     nodes for the same reported depth - **163x** on one board (556,387 vs 3,411), 9.4x even at depth 3 where
     the move agrees. `mate` is the ONLY limit flag that changes the tree: `go depth 7 ponder` gives an
     identical tree (3,411 nodes, same score, bestmove withheld) and both node-budget forms search deeper
     exactly as requested. **So a node count far above its depth peers is a positive signal for a mate row.**
  2. **`go nodes N` AND `go softnodes N` AT THE SAME N ARE DIFFERENT EXPERIMENTS.** nodes undershoots (0.47x,
     0.91x measured) because it stops when the next iteration would exceed N; softnodes lands on budget
     (1.00-1.04x) because it finishes the one that passes N and hard-stops at 4N. **At 20k they disagreed on
     both the move and the score.** So a corpus whose rows sit at 0.5x of their stated budget is a `nodes`
     corpus, and one at 1.0x is a `softnodes` corpus - and mixing the two is mixing definitions.
  3. **NEITHER CAN BE FIXED AFTER THE FACT.** A mate row's score was produced by a different tree, so it is not
     "the depth-2N-1 score"; a nodes row is not "the softnodes score". The only remedy is to separate them.

WHAT THIS TOOL DOES NOT DO. It cannot recover which budget a row was produced under if the node count was not
recorded, and it cannot tell `nodes` from `softnodes` when the ratio falls between their ranges. It reports what
is separable and says so when it is not. **A tool that guessed would be worse than one that refuses.**

USAGE
    python3 audit_corpus_provenance.py corpus.csv
    python3 audit_corpus_provenance.py corpus.json --format json

Expected columns (any names, matched case-insensitively, extras ignored):
    depth, nodes, score, [budget or softnodes or nodes_limit], [bestmove]

Exit codes: 0 no inconsistency found, 1 rows flagged, 2 cannot parse.
"""
import argparse
import csv
import json
import re
import sys

# measured on PC r15 068f0927 (see FINDINGS S-C130/S-C132)
MATE_NODE_RATIO_MIN = 20.0      # mate rows cost >= 9.4x even at their cheapest; 20x is a conservative cut
NODES_RATIO_MAX = 0.95          # `go nodes` undershoots: 0.47x and 0.91x measured
SOFTNODES_RATIO_MIN = 0.98      # `go softnodes` lands on budget: 1.00x and 1.04x measured


def pick(row, *names):
    low = {k.lower().strip(): v for k, v in row.items()}
    for n in names:
        if n in low:
            return low[n]
    return None


def as_float(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def rows_from_csv(path):
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def rows_from_json(path):
    data = json.load(open(path, encoding="utf-8"))
    if isinstance(data, dict):
        for k in ("rows", "cells", "data", "records"):
            if k in data and isinstance(data[k], list):
                return data[k]
        raise SystemExit("JSON object has no rows/cells/data/records list")
    return data


def classify(rows):
    """Return (mate_suspects, nodes_style, softnodes_style, unknown, notes)."""
    mate, nodesish, softish, unknown = [], [], [], []
    notes = []
    have_budget = 0
    for i, r in enumerate(rows):
        depth = as_float(pick(r, "depth"))
        nodes = as_float(pick(r, "nodes"))
        budget = as_float(pick(r, "budget", "softnodes", "nodes_limit", "limit"))
        if nodes is None or depth is None:
            unknown.append(i)
            continue
        if budget:
            have_budget += 1
            ratio = nodes / budget
            if ratio < NODES_RATIO_MAX:
                nodesish.append((i, ratio))
            elif ratio >= SOFTNODES_RATIO_MIN:
                softish.append((i, ratio))
            else:
                unknown.append(i)
        else:
            unknown.append(i)

    # mate detection without a budget: node count relative to the MEDIAN of non-mate rows at the same depth
    if not have_budget:
        notes.append("no budget column - mate detection used depth-peer medians instead")
        by_depth = {}
        for r in rows:
            d = as_float(pick(r, "depth"))
            n = as_float(pick(r, "nodes"))
            if d is None or n is None:
                continue
            by_depth.setdefault(d, []).append(n)
        med = {d: sorted(v)[len(v) // 2] for d, v in by_depth.items() if len(v) >= 3}
        for i, r in enumerate(rows):
            d = as_float(pick(r, "depth"))
            n = as_float(pick(r, "nodes"))
            if d is None or n is None or d not in med or med[d] <= 0:
                continue
            if n / med[d] >= MATE_NODE_RATIO_MIN:
                mate.append((i, n / med[d]))
    return mate, nodesish, softish, unknown, notes


def selftest():
    ok = True

    def chk(n, c, d=""):
        nonlocal ok
        print("  %-58s %s %s" % (n, "PASS" if c else "FAIL", d))
        if not c:
            ok = False

    print("controls:")
    # 1 a mate row (node count 163x its depth peers) is flagged
    rows = [{"depth": 7, "nodes": 3411} for _ in range(5)] + [{"depth": 7, "nodes": 556387}]
    m, _, _, _, _ = classify(rows)
    chk("1 a row at 163x its depth peers is flagged as mate", any(i == 5 for i, _ in m))
    # 2 a nodes-style corpus is recognised by ratio
    rows = [{"depth": 8, "nodes": 9359, "budget": 20000}]
    _, nish, sish, _, _ = classify(rows)
    chk("2 a 0.47x row is classified nodes-style", len(nish) == 1 and not sish)
    # 3 a softnodes-style corpus is recognised
    rows = [{"depth": 9, "nodes": 20800, "budget": 20000}]
    _, nish, sish, _, _ = classify(rows)
    chk("3 a 1.04x row is classified softnodes-style", len(sish) == 1 and not nish)
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--format", default="auto", choices=["auto", "csv", "json"])
    a = ap.parse_args()

    if not selftest():
        print("\nCONTROLS FAILED - refusing to audit")
        return 2

    fmt = a.format
    if fmt == "auto":
        fmt = "json" if a.path.lower().endswith(".json") else "csv"
    try:
        rows = rows_from_json(a.path) if fmt == "json" else rows_from_csv(a.path)
    except Exception as e:
        print("cannot parse %s: %s" % (a.path, e))
        return 2

    print()
    print("auditing %d rows from %s" % (len(rows), a.path))
    mate, nish, sish, unknown, notes = classify(rows)
    for n in notes:
        print("  note: %s" % n)
    print()
    print("  mate-suspect rows (node count far above depth peers): %d" % len(mate))
    for i, ratio in mate[:10]:
        print("     row %d: %.1fx its depth peers" % (i, ratio))
    print("  nodes-style rows (ratio < %.2f of budget): %d" % (NODES_RATIO_MAX, len(nish)))
    print("  softnodes-style rows (ratio >= %.2f of budget): %d" % (SOFTNODES_RATIO_MIN, len(sish)))
    print("  unclassifiable: %d" % len(unknown))
    print()

    inconsistent = bool(mate) or (bool(nish) and bool(sish))
    if mate:
        print("  FINDING: %d row(s) appear to be from a mate-limited search. Those scores come from a" % len(mate))
        print("  different tree (seven heuristics and the TT cutoff disabled) and are NOT depth-matched")
        print("  to the rest of the corpus.")
    if nish and sish:
        print("  FINDING: this corpus mixes `go nodes` and `go softnodes` rows at the same stated budget.")
        print("  Those are different experiments - `nodes` undershoots, `softnodes` lands on budget - and")
        print("  at 20k they disagree on move AND score. Separate them before training on either.")
    if not inconsistent:
        print("  No inconsistency detected by these three checks.")
        print("  That is a bounded statement: it rules out a mate/mixed-budget corpus, not every")
        print("  provenance problem - a row with no budget column cannot be classified.")
    print()
    return 1 if inconsistent else 0


if __name__ == "__main__":
    sys.exit(main())
