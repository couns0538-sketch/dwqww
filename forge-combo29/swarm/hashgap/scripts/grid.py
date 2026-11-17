"""The main grid: Hash 1 / 16 / 64 / 256 x node budget x position.

Every cell is a fresh process (see ucih's docstring for why `Clear Hash` cannot be
used to reset between cells).  Each cell records the answer, the search's own
depth, and every trace counter, so the counters can be correlated with whether
the answer differed rather than described in isolation.

Usage:  grid.py <binary> <out.jsonl> [--workers N]
"""

import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import positions

HASHES = [1, 16, 64, 256]
BUDGETS = [50000, 200000, 500000, 1000000, 2000000]
POSITION_SET = list(dict.fromkeys(positions.PRACTICAL + positions.SHARP))[:24]

COUNTER_KEYS = [
    "probe", "probe_hit", "probe_miss",
    "hit_shallower", "hit_equal", "hit_deeper", "hit_shallower_by_3plus",
    "hit_stale_generation", "false_hit",
    "store", "store_admit", "store_reject",
    "store_into_empty", "store_same_key", "store_displace",
    "nodes", "depth", "seldepth",
    "probe_cluster_fill_mean", "store_cluster_fill_mean",
]


def run_one(job):
    binary, fen, budget, hash_mb = job
    import ucih

    started = time.monotonic()
    try:
        cell = ucih.one_cell(binary, fen, f"go nodes {budget}", hash_mb, want_ttstats=True)
    except Exception as exc:  # noqa: BLE001 - a refused cell must be visible, not silent
        return {"fen": fen, "budget": budget, "hash": hash_mb, "error": repr(exc)}

    trace = cell["trace"] or {}
    row = {
        "fen": fen,
        "budget": budget,
        "hash": hash_mb,
        "bestmove": cell["bestmove"],
        "score": cell["score"],
        "depth": cell["depth"],
        "seldepth": cell["seldepth"],
        "info_lines": cell["info_lines"],
        "ttstats": cell["ttstats"],
        "elapsed_s": round(time.monotonic() - started, 3),
    }
    for key in COUNTER_KEYS:
        row[key] = trace.get(key)
    row["displaced_depth"] = trace.get("displaced_depth", {})
    return row


def main():
    binary = sys.argv[1]
    out_path = sys.argv[2]
    workers = 4
    if "--workers" in sys.argv:
        workers = int(sys.argv[sys.argv.index("--workers") + 1])

    jobs = [
        (binary, fen, budget, hash_mb)
        for fen in POSITION_SET
        for budget in BUDGETS
        for hash_mb in HASHES
    ]
    print(f"{len(jobs)} cells: {len(POSITION_SET)} positions x {len(BUDGETS)} budgets "
          f"x {len(HASHES)} hash sizes, {workers} workers", flush=True)

    rows = []
    started = time.monotonic()
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for i, row in enumerate(pool.map(run_one, jobs, chunksize=1), 1):
            rows.append(row)
            if i % 40 == 0 or i == len(jobs):
                done = time.monotonic() - started
                print(f"  {i}/{len(jobs)} cells, {done:.0f}s elapsed, "
                      f"eta {done / i * (len(jobs) - i):.0f}s", flush=True)

    errors = [r for r in rows if "error" in r]
    with open(out_path, "w") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")

    print(f"\nwrote {len(rows)} rows to {out_path}")
    if errors:
        print(f"REFUSED CELLS: {len(errors)}")
        for row in errors[:10]:
            print(f"  hash={row['hash']} budget={row['budget']} {row['fen']}: {row['error']}")
    else:
        print("no refused cells")


if __name__ == "__main__":
    main()
