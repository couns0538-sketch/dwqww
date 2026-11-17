"""Between-cell vs within-cell analysis.

A threaded cell is not a label: its own repeats differ (12/12 in pair 1). So a
between-cell "12/12 differ" says nothing about the option if the two cells'
answer SETS overlap. This module separates the two:

  - set_overlap: does cell A's set of signatures across repeats intersect cell B's?
    If yes on a position, that position carries no evidence of a difference.
  - disjoint: positions where the sets do not intersect. Only these are evidence.
  - field union over the disjoint positions, so the report names which field moved.

For a deterministic cell (Threads 1) each set is a singleton and this reduces to
the plain criterion.
"""
import json
import os

import uci

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(os.path.dirname(HERE), "evidence")


def load(name):
    with open(os.path.join(EVID, f"{name}.json")) as fh:
        return json.load(fh)


def sigs(row):
    return [uci.sig(r) for r in row["runs"]]


def analyse(result, left, right):
    rows = []
    for pos_name in result["rows"][left]:
        a, b = result["rows"][left][pos_name], result["rows"][right][pos_name]
        sa, sb = set(sigs(a)), set(sigs(b))
        overlap = bool(sa & sb)
        # Field differences are measured against the *nearest* pair: the smallest
        # field set over every (runA, runB) combination, so a position is only
        # called differing if no run of one cell matches a run of the other in
        # bestmove/score/depth/nodes.
        best = None
        for ra in a["runs"]:
            for rb in b["runs"]:
                f = uci.moved(ra, rb)
                if best is None or len(f) < len(best):
                    best = f
        rows.append({"position": pos_name, "overlap": overlap, "min_field_set": best,
                     "left_sigs": sorted(sa), "right_sigs": sorted(sb),
                     "left_runs": len(a["runs"]), "right_runs": len(b["runs"])})
    disjoint = [r for r in rows if not r["overlap"]]
    fields = {}
    for r in disjoint:
        for f in r["min_field_set"]:
            fields[f] = fields.get(f, 0) + 1
    return {"left": left, "right": right, "positions": len(rows),
            "overlapping": len(rows) - len(disjoint), "disjoint": len(disjoint),
            "fields_on_disjoint": fields, "rows": rows}


def report(names, pairs):
    out = {"source": names, "comparisons": []}
    for name, left, right in pairs:
        out["comparisons"].append(analyse(load(name), left, right))
    return out
