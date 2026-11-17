"""Grid runner for option-pair interactions.

Design rules this enforces (from the brief):
  - fresh process per cell (every `uci.run` is a new process);
  - the same fixtures for every cell in a grid;
  - the audit's difference criterion: a cell differs only if bestmove, score,
    depth or nodes differ, and the report names which field moved;
  - every cell records whether its options were ACCEPTED (`unknown option` /
    `invalid value` would otherwise make every cell identical for free);
  - repeats inside a cell, so a "difference" across cells can be compared with
    the same-cell noise floor. Without this a Threads-4 comparison would report
    thread noise as an effect of Hash.
"""
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor

import uci

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(os.path.dirname(HERE), "evidence")
SPEC = json.load(open(os.path.join(HERE, "positions.json")))
POSITIONS = SPEC["positions"]
BAIL = SPEC["draw_bail"]
BAIL_MOVES = SPEC["draw_bail_movelist"]

# The option block every non-pair cell shares, so a row is comparable to any other
# row: reproducibility pins from the audit (OwnBook off unless the book is the
# subject, Book Variety 0 wherever the book can fire, Threads 1 unless Threads is
# the subject).
BASE = [("OwnBook", "false")]


def cells_of(base, overrides):
    """Merge a per-cell override onto the base block, preserving order."""
    merged = dict(base)
    merged.update(overrides)
    return sorted(merged.items())


def one(position, options, go, repeats, note=""):
    row = {"position": position, "options": options, "go": go, "note": note, "runs": []}
    for _ in range(repeats):
        t0 = time.monotonic()
        r = uci.run(options=options, position=position, go=go)
        r["wall_ms"] = int((time.monotonic() - t0) * 1000)
        r["process_ms"] = r["wall_ms"]
        row["runs"].append(r)
    first = row["runs"][0]
    row["cell"] = {
        "bestmove": first["bestmove"], "score_kind": first["score_kind"], "score": first["score"],
        "depth": first["depth"], "nodes": first["nodes"],
        "infos": first["infos"], "pv": first["pv"], "book": first["book"],
    }
    row["accepted"] = all(r["accepted"] for r in row["runs"])
    row["rejected"] = sorted({d for r in row["runs"] for d in r["rejected"]})
    # Spread inside the cell over repeats. All-zero means the cell is a label.
    row["self_differs"] = any(uci.moved(first, r) for r in row["runs"][1:])
    row["self_fields"] = sorted({f for r in row["runs"][1:] for f in uci.moved(first, r)})
    return row


def grid(name, cell_defs, positions, go, repeats=1, base=BASE, workers=4):
    """cell_defs: list of (label, overrides dict). Returns a result dict."""
    jobs = []
    for label, overrides in cell_defs:
        options = cells_of(base, overrides)
        for pos_name, pos in positions:
            jobs.append((label, options, pos_name, pos))
    out = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(one, pos, options, go, repeats, label): (label, pos_name)
            for label, options, pos_name, pos in jobs
        }
        for fut, (label, pos_name) in futures.items():
            out.setdefault(label, {})[pos_name] = fut.result()
    result = {"grid": name, "go": go, "repeats": repeats, "base": sorted(base),
              "cells": [label for label, _ in cell_defs], "rows": out}
    os.makedirs(EVID, exist_ok=True)
    with open(os.path.join(EVID, f"{name}.json"), "w") as fh:
        json.dump(result, fh, indent=1)
    return result


def compare(result, left, right):
    """Per-position field differences between two cells of one grid."""
    rows = []
    for pos_name in result["rows"][left]:
        a = result["rows"][left][pos_name]["cell"]
        b = result["rows"][right][pos_name]["cell"]
        fields = uci.moved(a, b)
        rows.append({"position": pos_name, "fields": fields,
                     "left": [a["bestmove"], a["score_kind"], a["score"], a["depth"], a["nodes"]],
                     "right": [b["bestmove"], b["score_kind"], b["score"], b["depth"], b["nodes"]]})
    n = len(rows)
    differing = sum(1 for r in rows if r["fields"])
    field_counts = {}
    for r in rows:
        for f in r["fields"]:
            field_counts[f] = field_counts.get(f, 0) + 1
    return {"left": left, "right": right, "positions": n, "differing": differing,
            "field_counts": field_counts, "rows": rows}


def noise(result, label):
    """Within-cell repeat spread for one cell across every position."""
    differing = 0
    for pos_name, row in result["rows"][label].items():
        if row["self_differs"]:
            differing += 1
    return {"cell": label, "positions": len(result["rows"][label]), "self_differing": differing}


def acceptance(result):
    bad = []
    for label, per_pos in result["rows"].items():
        for pos_name, row in per_pos.items():
            if not row["accepted"]:
                bad.append({"cell": label, "position": pos_name, "rejected": row["rejected"]})
    return bad


def summarise(result, pairs):
    summary = {"grid": result["grid"], "go": result["go"], "repeats": result["repeats"],
               "acceptance_failures": acceptance(result), "comparisons": [], "noise": []}
    for label in result["cells"]:
        if result["repeats"] > 1:
            summary["noise"].append(noise(result, label))
    for left, right in pairs:
        summary["comparisons"].append(compare(result, left, right))
    with open(os.path.join(EVID, f"{result['grid']}-summary.json"), "w") as fh:
        json.dump(summary, fh, indent=1)
    return summary


def print_summary(summary):
    print(f"== {summary['grid']} ({summary['go']}, {summary['repeats']} repeat(s))")
    if summary["acceptance_failures"]:
        print("   ACCEPTANCE FAILURES:", summary["acceptance_failures"])
    else:
        print("   every cell's options accepted")
    for n in summary["noise"]:
        print(f"   noise {n['cell']:38s} self-differs {n['self_differing']}/{n['positions']}")
    for c in summary["comparisons"]:
        print(f"   {c['left']:34s} vs {c['right']:34s} differ {c['differing']}/{c['positions']}"
              f"  fields={c['field_counts']}")
