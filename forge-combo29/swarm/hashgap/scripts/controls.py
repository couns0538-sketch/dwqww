"""Is any of this reproducible, or is it noise?

Three controls, all required before any of the divergence numbers mean anything:

1. same size against itself -> must be 0/N. A non-zero here would mean the
   harness is not deterministic and every other row is meaningless.
2. Hash 64 vs 64 in two separate processes, same budget -> must be 0/N.
3. the geometry pair with the smallest step (64 vs 65) repeated with a different
   position set -> is the 8/16 at 2M a property of the engine or of these 16
   positions?

Control 1 and 2 differ: 1 reuses nothing and starts two fresh processes; it is the
real test of whether a cold cell is deterministic.
"""

import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor

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
    binary, fen, hash_mb, budget, tag = job
    import ucih

    try:
        cell = ucih.one_cell(binary, fen, f"go nodes {budget}", hash_mb)
    except Exception as exc:  # noqa: BLE001
        return {"fen": fen, "hash": hash_mb, "budget": budget, "tag": tag, "error": repr(exc)}
    trace = cell["trace"] or {}
    return {
        "fen": fen,
        "hash": hash_mb,
        "budget": budget,
        "tag": tag,
        "bestmove": cell["bestmove"],
        "score": cell["score"],
        "depth": cell["depth"],
        "nodes": trace.get("nodes"),
    }


def main():
    binary = sys.argv[1]
    out_path = sys.argv[2]
    position_file = sys.argv[3]
    second_file = sys.argv[4] if len(sys.argv) > 4 else position_file

    fens = load_positions(position_file, POSITION_COUNT)
    fens_b = load_positions(second_file, POSITION_COUNT)

    jobs = []
    # Control 1/2: the same cell twice, two fresh processes.
    for budget in (1000000, 2000000):
        for fen in fens:
            jobs.append((binary, fen, 64, budget, "a"))
            jobs.append((binary, fen, 64, budget, "b"))
    # Control 3: 64 vs 65 on a second position set.
    for budget in (2000000, 4000000):
        for fen in fens_b:
            jobs.append((binary, fen, 64, budget, "setB"))
            jobs.append((binary, fen, 65, budget, "setB"))

    print(f"{len(jobs)} cells", flush=True)
    rows = []
    started = time.monotonic()
    with ProcessPoolExecutor(max_workers=4) as pool:
        for i, row in enumerate(pool.map(run_one, jobs, chunksize=1), 1):
            rows.append(row)
            if i % 60 == 0:
                print(f"  {i}/{len(jobs)} {time.monotonic() - started:.0f}s", flush=True)

    with open(out_path, "w") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
    errors = [r for r in rows if "error" in r]
    print(f"wrote {len(rows)} rows, {len(errors)} refused\n")

    print("## Control: identical cell, two fresh processes\n")
    print("| budget | bestmove differs | score differs | nodes differ |")
    print("|---|---|---|---|")
    for budget in (1000000, 2000000):
        move_diff = score_diff = node_diff = 0
        for fen in fens:
            a = next((r for r in rows if r.get("fen") == fen and r.get("budget") == budget
                      and r.get("hash") == 64 and r.get("tag") == "a"), None)
            b = next((r for r in rows if r.get("fen") == fen and r.get("budget") == budget
                      and r.get("hash") == 64 and r.get("tag") == "b"), None)
            if not a or not b or "error" in a or "error" in b:
                continue
            if a["bestmove"] != b["bestmove"]:
                move_diff += 1
            if a["score"] != b["score"]:
                score_diff += 1
            if a["nodes"] != b["nodes"]:
                node_diff += 1
        print(f"| {budget} | **{move_diff}/{len(fens)}** | {score_diff}/{len(fens)} | "
              f"{node_diff}/{len(fens)} |")

    print("\n## Control: Hash 64 vs 65 on a second position set\n")
    print("| budget | differ |")
    print("|---|---|")
    for budget in (2000000, 4000000):
        differed = 0
        counted = 0
        for fen in fens_b:
            a = next((r for r in rows if r.get("fen") == fen and r.get("budget") == budget
                      and r.get("hash") == 64 and r.get("tag") == "setB"), None)
            b = next((r for r in rows if r.get("fen") == fen and r.get("budget") == budget
                      and r.get("hash") == 65 and r.get("tag") == "setB"), None)
            if not a or not b or "error" in a or "error" in b:
                continue
            counted += 1
            if a["bestmove"] != b["bestmove"] or a["score"] != b["score"]:
                differed += 1
        print(f"| {budget} | **{differed}/{counted}** |")


if __name__ == "__main__":
    main()
