"""Targeted probes: hashfull under MultiPV, nps at time 0, tiny movetime.

Each measurement has a matched control at MultiPV 1 so the effect can be
attributed to the setting and not to the position or the depth.

The hashfull question is not "is it in range" (it is) but "does the number
describe the engine's table". Under MultiPV > 1 the alternate lines carry
`alt_shared->tt.hashfull()` -- a SEPARATE table that is cleared before every
alternate line. A client that reads the last info line therefore reads the
alternate worker's table, not the engine's.
"""

import json
import os

import uci

ENGINE = os.environ.get("FORGE_BIN", "/agent/repos/work-infofields/build/forge")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evidence")
SET = {"build": "g++ -DFORGE_MARCH=x86-64-v4 Release NDEBUG", "base_commit": "6b98f217",
       "threads": 1, "own_book": False}


def parse(lines):
    out = []
    for l in lines:
        f, pv = uci.parse_info(l)
        if f and "depth" in f:
            out.append({**f, "pv_moves": pv, "_line": l})
    return out


def engine(**opts):
    e = uci.Engine(ENGINE)
    e.handshake()
    e.setoption("OwnBook", "false")
    for k, v in opts.items():
        e.setoption(k.replace("_", " "), v)
    return e


def probe_hashfull_multipv():
    """Same position, same depth, MultiPV 1 vs 2 vs 3: which table is reported?"""
    depth = 18
    rows = {}
    for mp in (1, 2, 3, 4):
        e = engine(MultiPV=mp)
        e.position()
        lines, bm = e.search("depth %d" % depth, timeout=300)
        e.quit()
        parsed = parse(lines)
        at_depth = [r for r in parsed if int(r["depth"]) == depth]
        rows[mp] = {
            "per_line_hashfull": [int(r["hashfull"]) for r in at_depth],
            "first_line_hashfull": int(at_depth[0]["hashfull"]) if at_depth else None,
            "last_line_hashfull": int(at_depth[-1]["hashfull"]) if at_depth else None,
            "lines": [r["_line"] for r in at_depth],
        }

    control = rows[1]["last_line_hashfull"]
    out = {
        "depth": depth,
        "multipv1_reference_hashfull": control,
        "by_multipv": rows,
        "last_line_disagrees_with_multipv1": {
            mp: (rows[mp]["last_line_hashfull"] != control) for mp in rows},
    }
    with open(os.path.join(OUT, "hashfull_multipv.json"), "w") as fh:
        json.dump({"settings": SET, "fen": "startpos", **out}, fh, indent=1, sort_keys=True)
    print("MultiPV 1 reference hashfull at final line:", control)
    for mp in (1, 2, 3, 4):
        r = rows[mp]
        print("  MultiPV %d: per-line %s  last=%s  %s" % (
            mp, r["per_line_hashfull"], r["last_line_hashfull"],
            "SAME AS REF" if r["last_line_hashfull"] == control else "DIFFERENT TABLE"))


def probe_nps_zero():
    """nps at time 0: is it nodes/time, or a sentinel?"""
    e = engine()
    e.position()
    lines, bm = e.search("depth 8", timeout=120)
    parsed = parse(lines)
    zeros = [r for r in parsed if int(r["time"]) == 0]
    out = {
        "lines": len(parsed),
        "zero_time_lines": [{"nodes": int(r["nodes"]), "time": 0, "nps": int(r["nps"]),
                             "line": r["_line"]} for r in zeros],
        "zero_time_count": len(zeros),
        "max_nodes_reported_with_nps_0": max([int(r["nodes"]) for r in zeros], default=0),
        # what the arithmetic would give if it were not a sentinel
        "nps_would_be_undefined": "division by zero",
    }
    with open(os.path.join(OUT, "nps_zero.json"), "w") as fh:
        json.dump({"settings": SET, "fen": "startpos", **out}, fh, indent=1, sort_keys=True)
    print("zero-time lines:", out["zero_time_count"],
          "max nodes on such a line:", out["max_nodes_reported_with_nps_0"])


def probe_time_small():
    """tiny movetime: does `time` ever exceed the budget, and is it ever 0?"""
    e = engine()
    cases = []
    for mv in (1, 5, 20, 50):
        e.position()
        lines, bm = e.search("movetime %d" % mv, timeout=60)
        parsed = parse(lines)
        cases.append({"movetime": mv, "budget_ms": max(1, mv - 10),
                      "n_lines": len(parsed),
                      "last_time": int(parsed[-1]["time"]) if parsed else None,
                      "last_line": parsed[-1]["_line"] if parsed else None,
                      "bestmove": bm})
    e.quit()

    # go depth: the origin is worker entry, not the `go` receipt, so time can be
    # less than the wall clock the client measured.
    e = engine()
    e.position()
    import time as _t
    t0 = _t.monotonic()
    lines, bm = e.search("depth 5", timeout=60)
    wall = (_t.monotonic() - t0) * 1000
    parsed = parse(lines)
    depthcase = {"wall_ms": round(wall, 1), "last_time": int(parsed[-1]["time"]),
                 "last_line": parsed[-1]["_line"]}
    e.quit()
    with open(os.path.join(OUT, "time_small.json"), "w") as fh:
        json.dump({"settings": SET, "movetime_cases": cases, "depth5": depthcase},
                  fh, indent=1, sort_keys=True)
    for c in cases:
        print("movetime %-3d (budget %-3d): lines=%-2d last time=%s" % (
            c["movetime"], c["budget_ms"], c["n_lines"], c["last_time"]))
    print("go depth 5: wall %.1f ms, reported time %s ms" % (depthcase["wall_ms"],
                                                             depthcase["last_time"]))


if __name__ == "__main__":
    import sys
    fns = {"hashfull_multipv": probe_hashfull_multipv, "nps_zero": probe_nps_zero,
           "time_small": probe_time_small}
    for n in (sys.argv[1:] or list(fns)):
        print("==", n)
        fns[n]()
