"""Wire-output comparison: does `depth 1` on a drawn root break a GUI-visible contract?

Reads each `go` to `bestmove` before sending anything else. (Piping a whole script with
`quit` at the end makes the engine abort the search and fabricate a bestmove, which is the
documented artifact in the brief - it produced `a2a3` with zero info lines and would have
made every "no info lines" verdict meaningless.)

Checks encoded:
  1. exactly one `bestmove` per `go`;
  2. within one search, `info depth` is non-decreasing and never exceeds the request;
  3. the LAST info depth is what a GUI shows as "depth reached";
  4. the drawn root reports a legal move;
  5. a NORMAL search after a drawn root in the same session is unaffected, and its node
     count matches the base build's with the same history;
  6. `go depth 0` on a drawn root does not emit `depth 0`.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ucih import Engine, EngineError  # noqa: E402

BASE = os.path.expanduser("~/b_base/forge")
PATCHED = os.path.expanduser("~/b_patched/forge")

DRAWN = "8/8/4k3/8/3Q4/8/4K3/8 w - - 100 1"
NORMAL = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"


def one_search(exe, fen, gocmd, timeout=300):
    e = Engine(exe)
    try:
        e.send("ucinewgame")
        e.position(fen)
        lines, bm, info = e.go(gocmd, timeout=timeout)
        return {"lines": lines, "bestmove": bm, "info": info}
    finally:
        e.quit()


def two_searches(exe, fen1, fen2, gocmd="go depth 8"):
    e = Engine(exe)
    try:
        e.send("ucinewgame")
        e.position(fen1)
        l1, bm1, i1 = e.go(gocmd, timeout=300)
        e.send("ucinewgame")
        e.position(fen2)
        l2, bm2, i2 = e.go(gocmd, timeout=300)
        return {"first": {"bestmove": bm1, "info": i1},
                "second": {"bestmove": bm2, "info": i2}}
    finally:
        e.quit()


def shape(info, requested):
    depths = [int(l.split()[2]) for l in info if l.startswith("info depth")]
    nodes = 0
    for l in info:
        m = re.search(r"\bnodes (\d+)", l)
        if m:
            nodes = int(m.group(1))
    return {
        "info_lines": len(info), "depths": depths,
        "last_depth": depths[-1] if depths else None,
        "monotonic": all(b >= a for a, b in zip(depths, depths[1:])),
        "within_request": all(d <= max(requested, 1) for d in depths),
        "nodes": nodes,
        "last_info": info[-1] if info else "",
    }


def main():
    problems = []
    rows = []

    def note(case, tag, s, requested):
        rows.append(dict(case=case, build=tag, requested=requested, **s))

    for requested, gocmd in ((8, "go depth 8"), (1, "go depth 1"), (0, "go depth 0")):
        for tag, exe in (("base", BASE), ("patched", PATCHED)):
            r = one_search(exe, DRAWN, gocmd)
            s = shape(r["info"], requested)
            s["bestmove"] = r["bestmove"]
            note("drawn_d%d" % requested, tag, s, requested)
            if requested != 0 and s["last_depth"] != 1 and tag == "patched":
                problems.append("patched drawn root at %s reported last depth %r, expected 1" %
                                (gocmd, s["last_depth"]))
            if s["depths"] and not s["within_request"]:
                problems.append("%s %s emitted a depth above the request: %r" %
                                (tag, gocmd, s["depths"]))
            if s["depths"] and min(s["depths"]) < 1:
                problems.append("%s %s emitted depth 0 (invalid on the wire): %r" % (tag, gocmd, s["depths"]))

    for tag, exe in (("base", BASE), ("patched", PATCHED)):
        r = one_search(exe, NORMAL, "go depth 8")
        s = shape(r["info"], 8)
        s["bestmove"] = r["bestmove"]
        note("normal_d8", tag, s, 8)
        if s["last_depth"] != 8:
            problems.append("%s: normal root reached depth %r, expected 8" % (tag, s["last_depth"]))

    # order independence with the same session history
    tn = {}
    for tag, exe in (("base", BASE), ("patched", PATCHED)):
        tn[tag] = two_searches(exe, DRAWN, NORMAL)
        s0 = shape(tn[tag]["first"]["info"], 8); s0["bestmove"] = tn[tag]["first"]["bestmove"]
        s1 = shape(tn[tag]["second"]["info"], 8); s1["bestmove"] = tn[tag]["second"]["bestmove"]
        note("drawn_then_normal[0]", tag, s0, 8)
        note("drawn_then_normal[1]", tag, s1, 8)
        if shape(tn[tag]["second"]["info"], 8)["last_depth"] != 8:
            problems.append("%s: normal search AFTER a drawn root reached depth %r, expected 8" %
                            (tag, shape(tn[tag]["second"]["info"], 8)["last_depth"]))
    b_nodes = shape(tn["base"]["second"]["info"], 8)["nodes"]
    p_nodes = shape(tn["patched"]["second"]["info"], 8)["nodes"]
    if b_nodes != p_nodes:
        problems.append("normal search after a drawn root differs in nodes: base %d patched %d" %
                        (b_nodes, p_nodes))

    nd = {}
    for tag, exe in (("base", BASE), ("patched", PATCHED)):
        nd[tag] = two_searches(exe, NORMAL, DRAWN)
        s0 = shape(nd[tag]["first"]["info"], 8); s0["bestmove"] = nd[tag]["first"]["bestmove"]
        s1 = shape(nd[tag]["second"]["info"], 8); s1["bestmove"] = nd[tag]["second"]["bestmove"]
        note("normal_then_drawn[0]", tag, s0, 8)
        note("normal_then_drawn[1]", tag, s1, 8)

    print("%-26s %-8s %5s %6s %6s %8s %10s %8s %s" %
          ("case", "build", "req", "lines", "last", "monoton", "within", "nodes", "bestmove"))
    for r in rows:
        print("%-26s %-8s %5d %6d %6s %8s %10s %8d %s" % (
            r["case"], r["build"], r["requested"], r["info_lines"],
            r["last_depth"], r["monotonic"], r["within_request"], r["nodes"], r["bestmove"]))

    print("\n== contract checks ==")
    if problems:
        print("PROBLEMS (%d):" % len(problems))
        for p in problems:
            print("  -", p)
    else:
        print("no contract violation found across %d observations" % len(rows))

    with open("wire_report.json", "w") as fh:
        json.dump({"rows": rows, "problems": problems}, fh, indent=2)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
