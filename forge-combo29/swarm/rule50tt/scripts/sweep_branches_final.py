"""Focused branch-reachability sweep against the FINAL trace build.

Records, per search: the score, the node count, and the four branch counters plus
`exact_mate_far` and the store counters. `exact_mate_far` counts exactly the cells
where branch A's short circuit accepts a mate that cannot land before the counter
reaches 100 -- the cells where the shipped order and the pre-d9a8587df order
disagree. If it is 0 everywhere, that is the measurement behind the report's
"branch B cannot be reached through branch A" finding.

Small board set and modest depth: the near-90 clocks explode on basic-mate boards
(one depth-14 search at clock 84 reached 246 million mate-branch verdicts), so a
search that does not finish inside the allowance is recorded as TIMEOUT.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import uci_driver as u  # noqa: E402

TRACE = "/tmp/forge-variants/trace/build/forge"
TIMEOUT = 25.0

BOARDS = [
    ("kqk_a",    "8/8/8/8/8/1K6/2Q5/7k w - -"),
    ("kqk_b",    "8/8/8/8/8/2K5/1Q6/7k w - -"),
    ("krk_far",  "7k/8/8/R7/8/8/8/K7 w - -"),
    ("krk_box",  "7k/8/1R6/8/8/8/8/K7 w - -"),
    ("krk_edge", "k7/8/8/8/8/2K5/8/7R w - -"),
    ("kp_white", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - -"),
    ("mixed",    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ -"),
]
CLOCKS = [0, 50, 80, 84, 86, 88, 89, 90, 92, 95, 99]
DEPTH = 12


def parse(lines):
    last = None
    for l in lines:
        if "tt_trace" in l:
            last = l
    if last is None:
        return None
    p = last.split()
    keys = ("exact", "exact_mate_far", "mate", "inside", "outside", "stores", "stores_hi", "depthmax")
    return {p[i]: int(p[i + 1]) for i in range(len(p) - 1) if p[i] in keys}


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/branch_final.json"
    rows, totals = [], {}
    e = u.Engine(TRACE, hash_mb=16, timeout=TIMEOUT)
    for name, fields in BOARDS:
        for clock in CLOCKS:
            try:
                r = e.search(f"position fen {fields} {clock} 60", f"go depth {DEPTH}", collect_all=True)
            except TimeoutError:
                rows.append({"board": name, "clock": clock, "timeout": True})
                print(f"TIMEOUT {name} clock={clock}", flush=True)
                e.close()
                e = u.Engine(TRACE, hash_mb=16, timeout=TIMEOUT)
                continue
            t = parse(r["all"])
            rows.append({"board": name, "clock": clock, "score_kind": r["score_kind"],
                         "score": r["score"], "nodes": r["nodes"], "bestmove": r["bestmove"],
                         "trace": t})
            if t:
                for k, v in t.items():
                    totals[k] = totals.get(k, 0) + v
    e.close()
    json.dump({"depth": DEPTH, "rows": rows, "totals": totals}, open(out_path, "w"), indent=1)

    done = [r for r in rows if r.get("trace")]
    print(f"\nsearches {len(rows)}, traced {len(done)}, timed out {sum(1 for r in rows if r.get('timeout'))}")
    for k in ("exact", "exact_mate_far", "mate", "inside", "outside", "stores", "stores_hi"):
        print(f"  {k:16} {totals.get(k, 0):>12}")
    fire = [r for r in done if r["trace"]["mate"]]
    print(f"\nbranch B fired in {len(fire)} of {len(done)} searches")
    for r in fire[:8]:
        print(f"  {r['board']:9} clock={r['clock']:3} mate={r['trace']['mate']:>8} "
              f"score={r['score_kind']} {r['score']}")
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
