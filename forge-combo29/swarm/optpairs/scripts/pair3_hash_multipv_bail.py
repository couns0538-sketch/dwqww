"""Pair 3: Hash x drawn-root bail, and MultiPV x bail.

Two questions, one grid, because both are "does a setting change what the bail
returns":

  Hash x bail   -- the bail returns from Worker::search BEFORE the iterative
                   deepening loop (search.cpp:2249-2271) so the table can only
                   matter through the emergency/ponder TT lookup, which the bail
                   does not take. Prediction: identical at every Hash.
                   A bigger table also cannot create a bail: the trigger is
                   `is_repetition() || halfmove >= 100 || insufficient_material`
                   on the ROOT board, with no search involved.
  MultiPV x bail -- the audit already measured 10 of 10 bailing cells identical at
                   MPV 1/2/3 (empty pv, 0 nodes). Re-run as a citation check with
                   the searching control alongside.

The searching control is what makes the nulls mean something: if the grid only
contained bailing roots, every cell would be identical no matter what the options
did (trap 10).

Fields recorded per cell: bestmove, score, depth, nodes, number of `info depth`
lines, and whether the pv is empty (the caller-side bail signature from §1b).
"""
import json
import os
import sys

import grid
import uci

BAIL_POS = grid.BAIL + grid.BAIL_MOVES
GO = "go depth 8"


def cell_row(run):
    return {"bestmove": run["bestmove"], "score_kind": run["score_kind"], "score": run["score"],
            "depth": run["depth"], "nodes": run["nodes"], "infos": run["infos"],
            "pv_empty": len(run["pv"]) == 0, "book": run["book"]}


def main():
    base = [("OwnBook", "false")]
    arm = [
        ("H1_MPV1", {"Hash": "1", "MultiPV": "1"}),
        ("H8_MPV1", {"Hash": "8", "MultiPV": "1"}),
        ("H64_MPV1", {"Hash": "64", "MultiPV": "1"}),
        ("H256_MPV1", {"Hash": "256", "MultiPV": "1"}),
        ("H64_MPV2", {"Hash": "64", "MultiPV": "2"}),
        ("H64_MPV3", {"Hash": "64", "MultiPV": "3"}),
    ]
    r = grid.grid("pair3-hash-multipv-bail", arm, BAIL_POS, GO, repeats=2, base=base)
    out = {"grid": r["grid"], "go": GO, "acceptance_failures": grid.acceptance(r), "rows": {}}
    for label in r["cells"]:
        out["rows"][label] = {p: cell_row(row["runs"][0]) for p, row in r["rows"][label].items()}

    # The criterion: same four fields. Separately record the bail signature so a
    # cell that changed nothing in the four fields but gained an info line shows up.
    comparisons = []
    for left, right in [("H1_MPV1", "H8_MPV1"), ("H1_MPV1", "H64_MPV1"), ("H1_MPV1", "H256_MPV1"),
                        ("H64_MPV1", "H64_MPV2"), ("H64_MPV1", "H64_MPV3"),
                        ("H8_MPV1", "H64_MPV3"), ("H256_MPV1", "H64_MPV3")]:
        rows = []
        for p in out["rows"][left]:
            a, b = out["rows"][left][p], out["rows"][right][p]
            fields = [f for f, x, y in (("bestmove", a["bestmove"], b["bestmove"]),
                                        ("score", (a["score_kind"], a["score"]), (b["score_kind"], b["score"])),
                                        ("depth", a["depth"], b["depth"]), ("nodes", a["nodes"], b["nodes"]))
                      if x != y]
            rows.append({"position": p, "fields": fields, "info_lines": (a["infos"], b["infos"]),
                         "pv_empty": (a["pv_empty"], b["pv_empty"])})
        comparisons.append({"left": left, "right": right,
                            "differing": sum(1 for x in rows if x["fields"]),
                            "info_line_changed": sum(1 for x in rows if x["info_lines"][0] != x["info_lines"][1]),
                            "rows": rows})
    out["comparisons"] = comparisons
    with open(os.path.join(grid.EVID, "pair3-analysis.json"), "w") as fh:
        json.dump(out, fh, indent=1)

    print(f"grid pair3, {GO}, {len(BAIL_POS)} positions x 2 repeats")
    print("acceptance failures:", out["acceptance_failures"] or "none")
    print("  bail signature per cell (bailing roots only):")
    for label in r["cells"]:
        vals = [(p, v) for p, v in out["rows"][label].items() if p.startswith("b0")]
        nodes = sorted({v["nodes"] for _, v in vals})
        empt = sorted({v["pv_empty"] for _, v in vals})
        print(f"    {label:9s} nodes={nodes} pv_empty={empt}")
    for c in comparisons:
        print(f"  {c['left']:9s} vs {c['right']:9s} differ {c['differing']}/{len(BAIL_POS)}"
              f"  info-line changed {c['info_line_changed']}/{len(BAIL_POS)}")


if __name__ == "__main__":
    sys.exit(main())
