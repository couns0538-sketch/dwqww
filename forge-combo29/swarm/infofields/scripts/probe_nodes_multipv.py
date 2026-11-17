"""`nodes` under MultiPV: how many distinct totals does one search put on the wire?

Three candidate quantities exist in search.cpp:

  * `total_nodes()`       -- local_nodes_ plus every other worker's atomic
  * `node_override`       -- shown_nodes: cumulative across the lines of ONE depth
  * `result.nodes`        -- total_nodes() + extra_nodes_, where extra_nodes_
                             accumulates the alternate workers' nodes for EVERY
                             depth already completed

`emit` uses node_override on the MultiPV path and `total_nodes()` otherwise; the
`info string softnodes` line prints `result.nodes`. If these disagree the client
gets two different node totals for one search.

Controls: MultiPV 1 must agree between the two reports, and every number must be
compared against the Threads-1 MultiPV 1 reference for the same depth.
"""

import json
import os
import re

import uci

ENGINE = os.environ.get("FORGE_BIN", "/agent/repos/work-infofields/build/forge")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evidence")
SET = {"build": "g++ -DFORGE_MARCH=x86-64-v4 Release NDEBUG", "base_commit": "6b98f217",
       "threads": 1, "own_book": False, "fen": "startpos"}


def num(pattern, line):
    m = re.search(pattern, line)
    return int(m.group(1)) if m else None


def one(mp, go):
    e = uci.Engine(ENGINE)
    e.handshake()
    e.setoption("OwnBook", "false")
    e.setoption("MultiPV", str(mp))
    e.position()
    lines, bm = e.search(go, timeout=300)
    e.quit()
    depth_lines = [l for l in lines if l.startswith("info depth")]
    soft = [l for l in lines if l.startswith("info string softnodes")]
    by_depth = {}
    for l in depth_lines:
        d = num(r"^info depth (\d+)", l)
        by_depth.setdefault(d, []).append({
            "multipv": num(r"multipv (\d+)", l),
            "nodes": num(r"nodes (\d+)", l),
            "line": l})
    return {
        "multipv_setting": mp, "go": go, "bestmove": bm,
        "last_depth_line": depth_lines[-1] if depth_lines else None,
        "last_depth_nodes": num(r"nodes (\d+)", depth_lines[-1]) if depth_lines else None,
        "softnodes_line": soft[-1] if soft else None,
        "softnodes_nodes": num(r"nodes (\d+)", soft[-1]) if soft else None,
        "per_depth_nodes": {str(k): [x["nodes"] for x in v] for k, v in sorted(by_depth.items())},
        "n_depth_levels": len(by_depth),
    }


def main():
    depth = 12
    out = {"reference": one(1, "depth %d" % depth), "cases": []}
    ref_nodes = out["reference"]["last_depth_nodes"]

    # MultiPV 1 control with softnodes: the two reports must agree.
    out["multipv1_softnodes"] = one(1, "softnodes 2000000")

    for mp in (2, 3, 4):
        a = one(mp, "depth %d" % depth)
        a["vs_multipv1_reference"] = {
            "ref_nodes": ref_nodes,
            "ratio": round(a["last_depth_nodes"] / ref_nodes, 3) if ref_nodes else None,
            "less_than_reference": a["last_depth_nodes"] < ref_nodes,
        }
        b = one(mp, "softnodes 2000000")
        b["disagreement"] = {
            "last_depth_nodes": b["last_depth_nodes"],
            "softnodes_nodes": b["softnodes_nodes"],
            "delta": (b["softnodes_nodes"] - b["last_depth_nodes"]
                      if b["softnodes_nodes"] is not None and b["last_depth_nodes"] is not None
                      else None),
        }
        out["cases"].append({"fixed_depth": a, "softnodes": b})

    with open(os.path.join(OUT, "nodes_multipv.json"), "w") as fh:
        json.dump({"settings": SET, **out}, fh, indent=1, sort_keys=True)

    print("MultiPV 1 reference at depth %d: %d nodes" % (depth, ref_nodes))
    print("MultiPV 1 softnodes: last-depth %s vs softnodes %s -> delta %s" % (
        out["multipv1_softnodes"]["last_depth_nodes"],
        out["multipv1_softnodes"]["softnodes_nodes"],
        (out["multipv1_softnodes"]["softnodes_nodes"] or 0)
        - (out["multipv1_softnodes"]["last_depth_nodes"] or 0)))
    for c in out["cases"]:
        a, b = c["fixed_depth"], c["softnodes"]
        print("\nMultiPV %d:" % a["multipv_setting"])
        print("  fixed-depth final nodes %d (%.2fx the MultiPV 1 reference: %s)" % (
            a["last_depth_nodes"], a["vs_multipv1_reference"]["ratio"],
            "LESS WORK THAN MULTIPV 1" if a["vs_multipv1_reference"]["less_than_reference"] else "more"))
        print("  softnodes: last-depth %s vs softnodes %s -> delta %s" % (
            b["last_depth_nodes"], b["softnodes_nodes"], b["disagreement"]["delta"]))
        print("  per-depth node lists:", b["per_depth_nodes"])


if __name__ == "__main__":
    main()
