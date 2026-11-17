"""Where does Hash 16 start to be unsafe in play, and is that budget ordinary?

Two questions, deliberately separated:

1. At which node budget does the BEST MOVE (not the score) start to change between
   Hash 16 and Hash 64? A score difference is visible to a harness; only a move
   difference is visible to a player.
2. Is that budget ordinary or absurd? Measured two ways, not asserted: the depth
   the engine reaches at that budget, and the nodes a real 1-second search
   actually spends on this machine's nps.

Positions come from a generated walk of real games in the repo, not hand-picked
tactics, so the answer is about the kind of position a game produces.
"""

import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor

HASHES = [16, 64]
BUDGETS = [200000, 300000, 400000, 500000, 750000, 1000000, 1500000, 2000000, 4000000]


def load_positions(path, count):
    fens = []
    with open(path) as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            fens.append(line)
            if len(fens) >= count:
                break
    return fens


def run_one(job):
    binary, fen, budget, hash_mb = job
    import ucih

    try:
        cell = ucih.one_cell(binary, fen, f"go nodes {budget}", hash_mb)
    except Exception as exc:  # noqa: BLE001
        return {"fen": fen, "budget": budget, "hash": hash_mb, "error": repr(exc)}
    trace = cell["trace"] or {}
    return {
        "fen": fen,
        "budget": budget,
        "hash": hash_mb,
        "bestmove": cell["bestmove"],
        "score": cell["score"],
        "depth": cell["depth"],
        "seldepth": cell["seldepth"],
        "nodes": trace.get("nodes"),
        "displace": trace.get("store_displace"),
    }


def main():
    binary = sys.argv[1]
    out_path = sys.argv[2]
    position_file = sys.argv[3]
    count = int(sys.argv[4]) if len(sys.argv) > 4 else 40

    fens = load_positions(position_file, count)
    jobs = [(binary, fen, budget, hash_mb)
            for fen in fens for budget in BUDGETS for hash_mb in HASHES]
    print(f"{len(jobs)} cells: {len(fens)} positions x {len(BUDGETS)} budgets x {len(HASHES)}",
          flush=True)

    rows = []
    started = time.monotonic()
    with ProcessPoolExecutor(max_workers=4) as pool:
        for i, row in enumerate(pool.map(run_one, jobs, chunksize=1), 1):
            rows.append(row)
            if i % 80 == 0:
                print(f"  {i}/{len(jobs)} {time.monotonic() - started:.0f}s", flush=True)

    with open(out_path, "w") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")

    errors = [r for r in rows if "error" in r]
    print(f"wrote {len(rows)} rows, {len(errors)} refused")
    for row in errors[:5]:
        print(" ", row)

    by_key = {(r["fen"], r["budget"], r["hash"]): r for r in rows if "error" not in r}
    print("\n## Bestmove and score divergence, Hash 16 vs Hash 64\n")
    print("| budget | move differs | score differs | any differs | mean depth h16 | mean depth h64 |")
    print("|---|---|---|---|---|---|")
    for budget in BUDGETS:
        move_diff = score_diff = any_diff = 0
        depths16, depths64 = [], []
        for fen in fens:
            a = by_key.get((fen, budget, 16))
            b = by_key.get((fen, budget, 64))
            if a is None or b is None:
                continue
            depths16.append(a["depth"])
            depths64.append(b["depth"])
            if a["bestmove"] != b["bestmove"]:
                move_diff += 1
            if a["score"] != b["score"]:
                score_diff += 1
            if a["bestmove"] != b["bestmove"] or a["score"] != b["score"]:
                any_diff += 1
        n = len(fens)
        print(f"| {budget} | **{move_diff}/{n}** | {score_diff}/{n} | {any_diff}/{n} | "
              f"{sum(depths16)/len(depths16):.1f} | {sum(depths64)/len(depths64):.1f} |")


if __name__ == "__main__":
    main()
