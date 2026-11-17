"""ABBA paired timing, following the design in forge-findings.md §5b / §6.

Fixed `go nodes 200000` so both builds search the same tree, `ucinewgame` before
every search (the only cold reset per §7 item 3), Threads 1, Hash 16, OwnBook
false. Order per position is ABBA, so drift in the machine cancels within the
pair. The report is a ratio of per-position medians with a bootstrap CI plus a
sign count -- never a bare mean (§6: "a claim about slower needs the CI and the
direction share").
"""

import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

import paths
from harness import Engine, parse_info


def run_position_pair(engA, engB, fen, limit, timeout):
    """ABBA: A, B, B, A. Returns the four wall times."""
    times = {"A": [], "B": []}
    nodes = {"A": [], "B": []}
    moves = {"A": [], "B": []}
    for who in ("A", "B", "B", "A"):
        eng = engA if who == "A" else engB
        eng.send("ucinewgame")
        eng.isready()
        eng.send(f"position fen {fen}")
        t0 = time.perf_counter()
        text = eng.command(limit, timeout=timeout)
        dt = time.perf_counter() - t0
        info, best = parse_info(text)
        times[who].append(dt)
        nodes[who].append(info.get("nodes", -1))
        moves[who].append(best)
    return times, nodes, moves


def bootstrap_ci(values, n=10000, seed=12345):
    import random
    rng = random.random()
    del rng
    r = random.Random(seed)
    k = len(values)
    meds = []
    for _ in range(n):
        sample = [values[r.randrange(k)] for _ in range(k)]
        meds.append(statistics.median(sample))
    meds.sort()
    return meds[int(0.025 * n)], meds[int(0.975 * n)]


def main(argv):
    if len(argv) < 4:
        print(__doc__.strip())
        print("\nusage: abba.py <engineA> <engineB> <fens> [limit] [out.json]", file=sys.stderr)
        return 2
    try:
        exeA = argv[1]   # reference (native)
        exeB = argv[2]   # candidate (v2 / v3)
        fen_path, fens = paths.fen_file(argv[3])
        limit = argv[4] if len(argv) > 4 else "go nodes 200000"
        out_path = paths.out_path(argv[5] if len(argv) > 5 else "abba.json")
    except paths.InputError as exc:
        print(f"abba.py: {exc}", file=sys.stderr)
        return 2
    timeout = 600.0

    engA = Engine(exeA, hash_mb=16, threads=1, nnue=True, book=False)
    engB = Engine(exeB, hash_mb=16, threads=1, nnue=True, book=False)

    rows = []
    try:
        for i, fen in enumerate(fens, 1):
            times, nodes, moves = run_position_pair(engA, engB, fen, limit, timeout)
            a = statistics.median(times["A"])
            b = statistics.median(times["B"])
            rows.append({
                "i": i, "fen": fen,
                "A_times": times["A"], "B_times": times["B"],
                "A_med": a, "B_med": b, "ratio": b / a,
                "A_nodes": nodes["A"], "B_nodes": nodes["B"],
                "A_moves": moves["A"], "B_moves": moves["B"],
            })
            print(f"{i:3d}/{len(fens)}  A {a*1000:7.1f}ms  B {b*1000:7.1f}ms  "
                  f"ratio {b/a:6.4f}  nodes {nodes['A'][0]}/{nodes['B'][0]}", flush=True)
    finally:
        engA.close()
        engB.close()

    ratios = [r["ratio"] for r in rows]
    node_mismatch = [r["i"] for r in rows if r["A_nodes"][0] != r["B_nodes"][0]
                     or r["A_nodes"][1] != r["B_nodes"][1]]
    move_mismatch = [r["i"] for r in rows if set(r["A_moves"]) != set(r["B_moves"])]

    med = statistics.median(ratios)
    lo, hi = bootstrap_ci(ratios)
    faster = sum(1 for x in ratios if x < 1.0)
    slower = sum(1 for x in ratios if x > 1.0)

    # exact two-sided sign test
    from math import comb
    n = faster + slower
    k = min(faster, slower)
    p = min(1.0, 2 * sum(comb(n, j) for j in range(k + 1)) / (2 ** n)) if n else 1.0

    summary = {
        "exeA": exeA, "exeB": exeB, "limit": limit, "n_positions": len(rows),
        "fens": fen_path,
        "median_ratio": med, "ci95": [lo, hi],
        "B_faster_count": faster, "B_slower_count": slower,
        "sign_test_two_sided_p": p,
        "node_mismatch_positions": node_mismatch,
        "move_mismatch_positions": move_mismatch,
        "spread": {"min": min(ratios), "q1": statistics.quantiles(ratios, n=4)[0],
                   "q3": statistics.quantiles(ratios, n=4)[2], "max": max(ratios)},
    }
    with open(out_path, "w") as f:  # NOSONAR - out_path is confined to PORTABLE_WORK by paths.out_path
        json.dump({"summary": summary, "rows": rows}, f, indent=1)
    print("\n=== SUMMARY ===")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
