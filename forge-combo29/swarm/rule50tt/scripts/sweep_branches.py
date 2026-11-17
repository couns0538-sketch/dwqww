"""Sweep real searches for each branch of score_usable, using the trace build.

The trace build (make_variants.py trace) increments a counter per branch verdict
and prints one `info string tt_trace ...` line per finished depth. That gives
"the path RAN" as a number rather than as an assumption (brief rule 2).

The question this answers: branch B (the mate-distance test) is easy to reach at
the object level, but is it reachable from a SEARCH? A branch that no real search
ever takes is worth reporting as exactly that.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import uci_driver as u  # noqa: E402

TRACE = "/tmp/forge-variants/trace/build/forge"
SHIPPED = "/agent/repos/dwqww/forge-combo29/build-rule50/forge"

# Small mates plus the two boards the rest of this seat uses. Clocks sweep the
# whole interesting band, including above 90 where main-search TT cutoffs are
# switched off and only the eval channel remains.
BOARDS = [
    ("kqk_a",    "8/8/8/8/8/1K6/2Q5/7k w - -"),
    ("kqk_b",    "8/8/8/8/8/2K5/1Q6/7k w - -"),
    ("krk_far",  "7k/8/8/R7/8/8/8/K7 w - -"),
    ("krk_box",  "7k/8/1R6/8/8/8/8/K7 w - -"),
    ("krk_edge", "k7/8/8/8/8/2K5/8/7R w - -"),
    ("kp_white", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - -"),
    ("mixed",    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ -"),
]
CLOCKS = [0, 20, 40, 60, 70, 75, 80, 82, 84, 85, 86, 87, 88, 89, 90, 91, 92, 95, 98]
DEPTHS = [8, 10, 12]
# Clocks near 90 make these boards explode (one clock-84 depth-14 search reached
# 246 million mate-branch verdicts before this sweep was rewritten). A search
# that does not return inside this allowance is recorded as TIMEOUT, which is a
# result about the position rather than a gap.
PER_SEARCH_TIMEOUT = 25.0


def trace_of(lines):
    """Last tt_trace line in the set, parsed into counters."""
    last = None
    for l in lines:
        if "tt_trace" in l:
            last = l
    if last is None:
        return None
    parts = last.split()
    d = {}
    for i, tok in enumerate(parts):
        if tok in ("exact", "exact_mate_far", "mate", "inside", "outside", "stores", "stores_hi", "depthmax"):
            d[tok] = int(parts[i + 1])
    return d


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/branch_sweep.json"
    e = u.Engine(TRACE, hash_mb=16, timeout=PER_SEARCH_TIMEOUT)
    rows = []
    totals = {}
    for name, fields in BOARDS:
        for clock in CLOCKS:
            for depth in DEPTHS:
                pos = f"position fen {fields} {clock} 60"
                try:
                    r = e.search(pos, f"go depth {depth}", collect_all=True)
                except TimeoutError:
                    # The process is still searching; it cannot be reused.
                    rows.append({"board": name, "clock": clock, "depth": depth, "timeout": True})
                    print(f"TIMEOUT {name} clock={clock} depth={depth}", flush=True)
                    e.close()
                    e = u.Engine(TRACE, hash_mb=16, timeout=PER_SEARCH_TIMEOUT)
                    continue
                t = trace_of(r["all"])
                if t is None:
                    rows.append({"board": name, "clock": clock, "depth": depth,
                                 "score": r["score"], "nodes": r["nodes"], "trace": None})
                    continue
                for k, v in t.items():
                    totals[k] = totals.get(k, 0) + v
                rows.append({"board": name, "clock": clock, "depth": depth,
                             "score": r["score"], "score_kind": r["score_kind"],
                             "nodes": r["nodes"], "bestmove": r["bestmove"], "trace": t})
                if t.get("mate", 0):
                    print(f"*** BRANCH B FIRES  {name} clock={clock} depth={depth} "
                          f"mate={t['mate']} nodes={r['nodes']}", flush=True)
    e.close()
    json.dump({"rows": rows, "totals": totals}, open(out_path, "w"), indent=1)
    done = [r for r in rows if r.get("trace")]
    print(f"\nsearches {len(rows)}, completed with a trace {len(done)}, "
          f"timed out {sum(1 for r in rows if r.get('timeout'))}")
    print("branch verdict totals across every finished depth:")
    for k in ("exact", "mate", "inside", "outside", "stores", "stores_hi"):
        print(f"  {k:12} {totals.get(k, 0):>12}")
    firing = [r for r in done if r["trace"].get("mate", 0)]
    print(f"\nsearches where branch B fired: {len(firing)} of {len(done)}")
    for r in firing[:10]:
        print(f"  {r['board']:9} clock={r['clock']:3} depth={r['depth']:2} "
              f"mate={r['trace']['mate']:>10} score={r['score_kind']} {r['score']}")
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
