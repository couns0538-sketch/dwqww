"""The decisive falsification test: same size, different geometry.

If divergence is collision PRESSURE, then two tables of almost identical size and
almost identical load should agree, because neither is under more pressure than
the other. Hash 64 and Hash 65 differ by one megabyte: 1,048,576 clusters against
1,064,960, a load difference under 2%.

If those two disagree at the same rate as Hash 64 versus 256, then the cause is
not how full the table is. It is that the search amplifies any difference in what
a probe happens to find, because the table is read at many decision points, not
only on a cutoff. In that case a size change is a perturbation and the divergence
is chaotic amplification, not "fewer collisions".

The same grid is repeated for a genuinely smaller pair (Hash 32 vs 64, a 2x size
step at low load) so the comparison has an intermediate point.
"""

import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor

# Pairs chosen so load differs little but geometry does, and vice versa.
PAIRS = [(64, 65), (64, 96), (32, 64), (64, 256)]
BUDGETS = [500000, 1000000, 2000000]
POSITION_COUNT = 16


def load_positions(path, count):
    fens = []
    with open(path) as handle:
        for line in handle:
            line = line.strip()
            if line and not line.startswith("#"):
                fens.append(line)
                if len(fens) >= count:
                    break
    return fens


def run_one(job):
    binary, fen, hash_mb, budget = job
    import ucih

    try:
        cell = ucih.one_cell(binary, fen, f"go nodes {budget}", hash_mb, want_ttstats=True)
    except Exception as exc:  # noqa: BLE001
        return {"fen": fen, "hash": hash_mb, "budget": budget, "error": repr(exc)}
    trace = cell["trace"] or {}
    return {
        "fen": fen,
        "hash": hash_mb,
        "budget": budget,
        "bestmove": cell["bestmove"],
        "score": cell["score"],
        "depth": cell["depth"],
        "nodes": trace.get("nodes"),
        "store_displace": trace.get("store_displace"),
        "load": cell["ttstats"]["load_factor"],
        "clusters": cell["ttstats"]["clusters"],
    }


def main():
    binary = sys.argv[1]
    out_path = sys.argv[2]
    position_file = sys.argv[3]

    fens = load_positions(position_file, POSITION_COUNT)
    sizes = sorted({size for pair in PAIRS for size in pair})
    jobs = [(binary, fen, size, budget)
            for budget in BUDGETS for fen in fens for size in sizes]
    print(f"{len(jobs)} cells over sizes {sizes}", flush=True)

    rows = []
    started = time.monotonic()
    with ProcessPoolExecutor(max_workers=4) as pool:
        for i, row in enumerate(pool.map(run_one, jobs, chunksize=1), 1):
            rows.append(row)
            if i % 100 == 0:
                print(f"  {i}/{len(jobs)} {time.monotonic() - started:.0f}s", flush=True)

    with open(out_path, "w") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")

    errors = [r for r in rows if "error" in r]
    print(f"wrote {len(rows)} rows, {len(errors)} refused")

    by_key = {(r["fen"], r["hash"], r["budget"]): r for r in rows if "error" not in r}

    print("\n## Same node budget, different size step\n")
    print("| size pair | clusters ratio | mean load a | mean load b | budget | differ |")
    print("|---|---|---|---|---|---|")
    for a_size, b_size in PAIRS:
        for budget in BUDGETS:
            differed = 0
            counted = 0
            loads_a, loads_b = [], []
            for fen in fens:
                a = by_key.get((fen, a_size, budget))
                b = by_key.get((fen, b_size, budget))
                if a is None or b is None:
                    continue
                counted += 1
                loads_a.append(a["load"])
                loads_b.append(b["load"])
                if (a["bestmove"] != b["bestmove"] or a["score"] != b["score"]):
                    differed += 1
            if not counted:
                continue
            ratio = (by_key[(fens[0], b_size, budget)]["clusters"]
                     / by_key[(fens[0], a_size, budget)]["clusters"])
            print(f"| {a_size} vs {b_size} | {ratio:.2f}x | "
                  f"{sum(loads_a)/len(loads_a):.3f} | {sum(loads_b)/len(loads_b):.3f} | "
                  f"{budget} | **{differed}/{counted}** |")

    print("\n## Reading\n")
    print("A collision-pressure account requires the 64-vs-65 row (essentially equal")
    print("load) to agree far more often than the 64-vs-256 row (4x less load).")
    print("If the two rows differ by about the same amount, load is not the governor.")


if __name__ == "__main__":
    main()
