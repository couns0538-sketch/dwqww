"""The 90 threshold: is it load-bearing, and would 89 or 91 behave differently?

Three questions, three controls:

1. Does the threshold change ANY search result versus a build with the guard
   removed? (`no_horizon` == the guard's horizon half deleted.)
2. Does 89 differ from 90? Does 91? Each variant differs from the shipped build
   in exactly two characters of the constant and nothing else, so a difference is
   attributable to the constant.
3. Where would a difference come from? Only at clocks >= 89, because below that
   `stored < 90` and `capped < 90` are both true and the threshold cannot bite.

A null here is only meaningful if the same harness shows a difference against a
build that is KNOWN to differ (brief rule 2: prove the path ran). `always_true`
is that build and is included as the positive control.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import uci_driver as u  # noqa: E402

BUILDS = {
    "shipped":   "/agent/repos/dwqww/forge-combo29/build-rule50/forge",
    "always_true": "/tmp/forge-variants/always_true/build/forge",
    "no_horizon":  "/tmp/forge-variants/no_horizon/build/forge",
    "thr89":       "/tmp/forge-variants/thr89/build/forge",
    "thr91":       "/tmp/forge-variants/thr91/build/forge",
    "mate_first":  "/tmp/forge-variants/mate_first/build/forge",
}

BOARDS = [
    ("kqk_a",    "8/8/8/8/8/1K6/2Q5/7k w - -"),
    ("kqk_b",    "8/8/8/8/8/2K5/1Q6/7k w - -"),
    ("krk_far",  "7k/8/8/R7/8/8/8/K7 w - -"),
    ("krk_box",  "7k/8/1R6/8/8/8/8/K7 w - -"),
    ("krk_edge", "k7/8/8/8/8/2K5/8/7R w - -"),
    ("kp_white", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - -"),
    ("mixed",    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ -"),
    ("mixed2",   "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - -"),
]

# 88/89/90/91/92 are the boundary; 0 and 60 are far below it and must not differ
# under a threshold change, which is the intra-board control.
CLOCKS = [0, 60, 88, 89, 90, 91, 92, 95]
DEPTH = 10
TIMEOUT = 20.0


def run(exe, boards, clocks, depth):
    out = {}
    e = u.Engine(exe, hash_mb=16, timeout=TIMEOUT)
    for name, fields in boards:
        for clock in clocks:
            key = (name, clock)
            try:
                r = e.search(f"position fen {fields} {clock} 60", f"go depth {depth}")
                out[key] = {"score_kind": r["score_kind"], "score": r["score"],
                            "nodes": r["nodes"], "bestmove": r["bestmove"],
                            "invalid_fen": r["invalid_fen"]}
            except TimeoutError:
                out[key] = {"timeout": True}
                e.close()
                e = u.Engine(exe, hash_mb=16, timeout=TIMEOUT)
    e.close()
    return out


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/threshold.json"
    results = {}
    for label, exe in BUILDS.items():
        print(f"running {label} ...", flush=True)
        results[label] = run(exe, BOARDS, CLOCKS, DEPTH)

    base = results["shipped"]
    summary = {}
    for label in BUILDS:
        if label == "shipped":
            continue
        diffs = []
        for key, a in base.items():
            b = results[label][key]
            if a.get("timeout") or b.get("timeout"):
                if a.get("timeout") != b.get("timeout"):
                    diffs.append((key, "timeout", a, b))
                continue
            if (a["score_kind"], a["score"], a["bestmove"]) != (b["score_kind"], b["score"], b["bestmove"]):
                diffs.append((key, "score/move", a, b))
        summary[label] = diffs
        print(f"\n{label}: {len(diffs)} differing cells of {len(base)}")
        for k, kind, a, b in diffs[:12]:
            print(f"   {k[0]:9} clock={k[1]:3}  shipped={a.get('score_kind')} {a.get('score')} {a.get('bestmove')}"
                  f"  this={b.get('score_kind')} {b.get('score')} {b.get('bestmove')}")

    json.dump({"results": {k: {f"{a}|{b}": v for (a, b), v in r.items()} for k, r in results.items()},
               "summary": {k: [[list(x[0]), x[1]] for x in v] for k, v in summary.items()}},
              open(path, "w"), indent=1)
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
