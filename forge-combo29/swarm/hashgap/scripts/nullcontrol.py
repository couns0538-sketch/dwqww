"""Null control, plus the arm that decides whether cutoffs or ordering carry it.

`no_read` is the important one. It removes the probe result from the search
entirely while leaving every store in place. The answer must then be identical at
every table size, because a table nobody reads cannot change a search. If sizes
still differ under `no_read`, the harness is leaking something other than the
table and none of the other rows may be trusted.

`no_cutoff` and `no_move` were run by mechanism.py; this runs all four arms over
a wider budget range so the threshold behaviour is visible per arm.
"""

import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor

HASHES = [1, 16, 64, 256]
BUDGETS = [500000, 1000000, 2000000]
ARMS = ["no_read", "no_cutoff", "no_move"]
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
    binary, fen, hash_mb, arm, budget = job
    import ucih

    try:
        with ucih.Engine(binary, hash_mb=hash_mb) as engine:
            engine._send(f"trace_{arm} 1")
            engine._send("isready")
            engine._expect_until("readyok")
            engine.position(fen=fen)
            cell = engine.search(f"go nodes {budget}")
    except Exception as exc:  # noqa: BLE001
        return {"fen": fen, "hash": hash_mb, "arm": arm, "budget": budget, "error": repr(exc)}

    trace = cell["trace"] or {}
    return {
        "fen": fen,
        "hash": hash_mb,
        "arm": arm,
        "budget": budget,
        "bestmove": cell["bestmove"],
        "score": cell["score"],
        "nodes": trace.get("nodes"),
    }


def main():
    binary = sys.argv[1]
    out_path = sys.argv[2]
    position_file = sys.argv[3]

    fens = load_positions(position_file, POSITION_COUNT)
    jobs = [(binary, fen, hash_mb, arm, budget)
            for arm in ARMS for budget in BUDGETS for fen in fens for hash_mb in HASHES]
    print(f"{len(jobs)} cells: {len(fens)} positions x {len(BUDGETS)} budgets "
          f"x {len(HASHES)} hashes x {len(ARMS)} arms", flush=True)

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
    for row in errors[:5]:
        print(" ", row)

    by_key = {(r["fen"], r["hash"], r["arm"], r["budget"]): r
              for r in rows if "error" not in r}

    print("\n## Divergence from Hash 64, per arm and budget\n")
    print("| arm | budget | Hash 1 | Hash 16 | Hash 256 |")
    print("|---|---|---|---|---|")
    for arm in ARMS:
        for budget in BUDGETS:
            cells = []
            for hash_mb in HASHES:
                if hash_mb == 64:
                    continue
                differed = 0
                counted = 0
                for fen in fens:
                    base = by_key.get((fen, 64, arm, budget))
                    other = by_key.get((fen, hash_mb, arm, budget))
                    if base is None or other is None:
                        continue
                    counted += 1
                    if (other["bestmove"] != base["bestmove"]
                            or other["score"] != base["score"]):
                        differed += 1
                cells.append(f"**{differed}/{counted}**")
            print(f"| {arm} | {budget} | " + " | ".join(cells) + " |")

    print("\n## Arm liveness (Hash 64, mean nodes)\n")
    print("| arm | 500k | 1M | 2M |")
    print("|---|---|---|---|")
    for arm in ARMS:
        values = []
        for budget in BUDGETS:
            nodes = [by_key[(fen, 64, arm, budget)]["nodes"] or 0
                     for fen in fens if (fen, 64, arm, budget) in by_key]
            values.append(f"{sum(nodes)/len(nodes):.0f}" if nodes else "-")
        print(f"| {arm} | " + " | ".join(values) + " |")


if __name__ == "__main__":
    main()
