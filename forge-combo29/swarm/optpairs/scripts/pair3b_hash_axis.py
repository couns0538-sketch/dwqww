"""Pair 3b: the Hash axis LIVENESS control for the bail grid.

Pair 3 compared Hash 1 / 8 / 64 / 256 on bailing roots and got 0 of 9 differing.
That is only a null if the Hash axis can move a cell in the same harness, on the
same positions, at the same command -- otherwise "Hash does not change a bail" is
indistinguishable from "Hash never reached the engine".

Two controls, both required:

  1. AXIS CONTROL -- the same grid on SEARCHING roots at a budget where Hash is
     known to matter (pair 1c measured Hash 1 vs 256 differing on 2 of 8
     positions at `go nodes 400000`). If this control moves, the axis is live.
  2. FAULT CONTROL -- an option name that does not exist must be reported
     `unknown option`, so the acceptance checker is shown to fire.

Then the bail cells again at the same budget, so the comparison is like for like:
the only difference between a control row and a bail row is the root.
"""
import json
import os
import sys

import grid
import uci

SEARCH_GO = "go nodes 400000"
BAIL_GO = "go depth 8"
SEARCH_POS = grid.POSITIONS[:8]
BAIL_POS = grid.BAIL + grid.BAIL_MOVES
HASHES = ["1", "8", "64", "256"]
BASE = [("OwnBook", "false")]


def main():
    out = {"search_go": SEARCH_GO, "bail_go": BAIL_GO}

    # 1. axis control: searching roots, Hash 1 vs 256
    arm = [(f"H{h}", {"Hash": h}) for h in HASHES]
    rs = grid.grid("pair3b-axis-search", arm, SEARCH_POS, SEARCH_GO, repeats=2, base=BASE)
    axis = {}
    for h in HASHES:
        per = {}
        for p, row in rs["rows"][f"H{h}"].items():
            per[p] = {"signature": list(uci.sig(row["runs"][0])),
                      "deterministic": not row["self_differs"]}
        axis[h] = per
    diffs = {p: uci.moved({"bestmove": axis["1"][p]["signature"][0],
                           "score_kind": axis["1"][p]["signature"][1],
                           "score": axis["1"][p]["signature"][2],
                           "depth": axis["1"][p]["signature"][3],
                           "nodes": axis["1"][p]["signature"][4]},
                          {"bestmove": axis["256"][p]["signature"][0],
                           "score_kind": axis["256"][p]["signature"][1],
                           "score": axis["256"][p]["signature"][2],
                           "depth": axis["256"][p]["signature"][3],
                           "nodes": axis["256"][p]["signature"][4]})
             for p in axis["1"]}
    out["axis_control"] = {"rows": axis, "hash1_vs_256": diffs,
                           "differing": sum(1 for v in diffs.values() if v),
                           "positions": len(diffs)}

    # 2. fault control: a name that does not exist
    fault = uci.run(options=[("Bogus Option", "1")], position=SEARCH_POS[0][1], go="go depth 6")
    out["fault_control"] = {"accepted": fault["accepted"], "rejected": fault["rejected"],
                            "bestmove": fault["bestmove"],
                            "fired": not fault["accepted"]}

    # 3. bails at the same Hash values
    rb = grid.grid("pair3b-axis-bail", arm, BAIL_POS, BAIL_GO, repeats=2, base=BASE)
    bail = {}
    for h in HASHES:
        bail[h] = {p: {"signature": list(uci.sig(row["runs"][0])), "nodes": row["runs"][0]["nodes"],
                       "pv_empty": len(row["runs"][0]["pv"]) == 0,
                       "infos": row["runs"][0]["infos"]}
                   for p, row in rb["rows"][f"H{h}"].items()}
    bail_diffs = {}
    for h in HASHES[1:]:
        bail_diffs[f"1_vs_{h}"] = sum(
            1 for p in bail["1"] if bail["1"][p]["signature"] != bail[h][p]["signature"])
    out["bail"] = {"rows": bail, "differing_vs_hash1": bail_diffs,
                   "acceptance_failures": grid.acceptance(rb) + grid.acceptance(rs)}

    with open(os.path.join(grid.EVID, "pair3b-analysis.json"), "w") as fh:
        json.dump(out, fh, indent=1)

    print("Hash axis liveness control")
    print(f"  axis control (searching roots, {SEARCH_GO}): Hash 1 vs 256 differ"
          f" {out['axis_control']['differing']}/{out['axis_control']['positions']}"
          f"  {diffs}")
    print(f"  fault control: 'Bogus Option' rejected = {out['fault_control']['fired']}"
          f"  {out['fault_control']['rejected']}")
    print(f"  bails ({BAIL_GO}), differing vs Hash 1: {bail_diffs} of {len(BAIL_POS)}")
    print("  bailing-root signature at each Hash:", {h: sorted({(v['nodes'], v['pv_empty']) for k, v in bail[h].items() if k.startswith('b0')}) for h in HASHES})


if __name__ == "__main__":
    sys.exit(main())
