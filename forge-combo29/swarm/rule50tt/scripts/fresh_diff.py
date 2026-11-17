"""Fresh-process differential: the only design in this seat that can attribute a
difference to the clock.

Why this file exists. The first threshold sweep (sweep_threshold.py) ran every
cell through one long-lived process per build and reported differences at clocks
0 and 60 under variants that only change a `< 90` constant. A threshold cannot
affect clock 0. aa_control.py then showed that a warm table changes the score of
the *same* board at the *same* clock (krk_far clock 0: 441 warm vs 475 cold), so
the shared design was measuring table pressure, not the threshold. Those figures
are withdrawn in FINDINGS.md.

Design here: one process per measurement. A "warm" measurement is the second of
two searches inside one process; a "cold" measurement is the only search in its
process. Nothing is inherited between measurements.
"""
import concurrent.futures as cf
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import uci_driver as u  # noqa: E402

SHIPPED = "/agent/repos/dwqww/forge-combo29/build-rule50/forge"
TIMEOUT = 45.0


def one(exe, sequence, depth):
    """Run a sequence of position lines in one fresh process, return all results."""
    e = u.Engine(exe, hash_mb=16, timeout=TIMEOUT)
    try:
        return [e.search(p, f"go depth {depth}") for p in sequence]
    finally:
        e.close()


def pos(fields, clock):
    return f"position fen {fields} {clock} 60"


def sig(r):
    return {"kind": r["score_kind"], "score": r["score"], "bestmove": r["bestmove"]}


def job(args):
    label, exe, sequence, depth, repeat = args
    try:
        runs = [one(exe, sequence, depth) for _ in range(repeat)]
    except TimeoutError:
        return label, {"timeout": True}
    return label, {"runs": [[sig(r) for r in run] for run in runs],
                   "nodes": [[r["nodes"] for r in run] for run in runs],
                   "invalid": any(r["invalid_fen"] for run in runs for r in run)}


def stable(rec):
    if rec.get("timeout"):
        return False
    first = rec["runs"][0]
    return all(r == first for r in rec["runs"]) and len({tuple(n) for n in rec["nodes"]}) == 1


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "stale"
    out_path = sys.argv[2] if len(sys.argv) > 2 else f"/tmp/{which}.json"
    DEPTH = 10
    REPEAT = 3

    if which == "stale":
        # Item 2 and item 3 of the assignment. For each board: cold at each clock,
        # the warm 10->90 pair (and its reverse), and the same-clock warm control.
        boards = [
            ("kqk_b",    "8/8/8/8/8/2K5/1Q6/7k w - -", 10, 90),
            ("krk_far",  "7k/8/8/R7/8/8/8/K7 w - -", 10, 90),
            ("krk_box",  "7k/8/1R6/8/8/8/8/K7 w - -", 10, 90),
            ("kp_white", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - -", 10, 90),
            ("mixed",    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ -", 10, 90),
            ("kqk_b_rev", "8/8/8/8/8/2K5/1Q6/7k w - -", 90, 10),
            ("krk_rev",  "7k/8/8/R7/8/8/8/K7 w - -", 90, 10),
        ]
        jobs = []
        for name, fields, a, b in boards:
            jobs += [
                (f"{name}|coldA", SHIPPED, [pos(fields, a)], DEPTH, REPEAT),
                (f"{name}|coldB", SHIPPED, [pos(fields, b)], DEPTH, REPEAT),
                (f"{name}|warmAB", SHIPPED, [pos(fields, a), pos(fields, b)], DEPTH, REPEAT),
                (f"{name}|warmBB", SHIPPED, [pos(fields, b), pos(fields, b)], DEPTH, REPEAT),
            ]
    elif which == "threshold":
        # Item 4 with fresh processes: shipped vs thr89 vs thr91, boundary clocks.
        boards = [
            ("kqk_b",   "8/8/8/8/8/2K5/1Q6/7k w - -"),
            ("kqk_a",   "8/8/8/8/8/1K6/2Q5/7k w - -"),
            ("krk_far", "7k/8/8/R7/8/8/8/K7 w - -"),
            ("krk_box", "7k/8/1R6/8/8/8/8/K7 w - -"),
        ]
        clocks = [0, 60, 85, 87, 88, 89, 90, 91, 92, 95]
        builds = {
            "shipped": SHIPPED,
            "thr89": "/tmp/forge-variants/thr89/build/forge",
            "thr91": "/tmp/forge-variants/thr91/build/forge",
            "nohorizon": "/tmp/forge-variants/no_horizon/build/forge",
        }
        jobs = []
        for bname, exe in builds.items():
            for name, fields in boards:
                for clock in clocks:
                    jobs.append((f"{bname}|{name}|{clock}", exe, [pos(fields, clock)], DEPTH, 2))
    else:
        raise SystemExit("unknown experiment")

    records = {}
    with cf.ThreadPoolExecutor(max_workers=4) as pool:
        futs = [pool.submit(job, j) for j in jobs]
        for f in cf.as_completed(futs):
            label, rec = f.result()
            records[label] = rec
            if rec.get("invalid"):
                print(f"REFUSED {label}", flush=True)

    json.dump(records, open(out_path, "w"), indent=1)
    print(f"wrote {out_path} ({len(records)} measurements)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
