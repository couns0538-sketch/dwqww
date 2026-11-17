"""Which TT mechanism makes two table sizes disagree?

The grid shows where sizes diverge. This asks how. Three arms, all on the trace
build, all at Threads 1, one fresh process per cell:

  full        the shipped search
  no_cutoff   the table still stores and still supplies tt_move, but a probe never
              returns early on a bound
  no_move     the table still stores and still cuts, but a probe never supplies a
              move for ordering

If `no_cutoff` is still size-dependent, cutoffs are not the mechanism. If
`no_move` is still size-dependent, move ordering is not the mechanism either, and
the honest answer is that this instrument did not find one.

Also reported, for the same cells: the number of entries the replacement policy
displaced at depth >= 1. A size difference that persists while that number is 0
cannot be a collision effect.
"""

import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import positions

HASHES = [1, 16, 64, 256]
BUDGET = 1000000
ARMS = ["full", "no_cutoff", "no_move"]
POSITION_SET = list(dict.fromkeys(positions.PRACTICAL + positions.SHARP))[:24]


def run_one(job):
    binary, fen, hash_mb, arm = job
    import ucih

    try:
        with ucih.Engine(binary, hash_mb=hash_mb) as engine:
            if arm == "no_cutoff":
                engine._send("trace_no_cutoff 1")
            elif arm == "no_move":
                engine._send("trace_no_move 1")
            engine._send("isready")
            engine._expect_until("readyok")
            engine.position(fen=fen)
            cell = engine.search(f"go nodes {BUDGET}")
            stats = engine.ttstats()
    except Exception as exc:  # noqa: BLE001
        return {"fen": fen, "hash": hash_mb, "arm": arm, "error": repr(exc)}

    trace = cell["trace"] or {}
    displaced = trace.get("displaced_depth") or {}
    deep_evictions = sum(count for depth, count in displaced.items() if int(depth) >= 1)
    return {
        "fen": fen,
        "hash": hash_mb,
        "arm": arm,
        "bestmove": cell["bestmove"],
        "score": cell["score"],
        "depth": cell["depth"],
        "nodes": trace.get("nodes"),
        "store_displace": trace.get("store_displace"),
        "deep_evictions": deep_evictions,
        "false_hit": trace.get("false_hit"),
        "load": stats["load_factor"],
    }


def main():
    binary = sys.argv[1]
    out_path = sys.argv[2]
    jobs = [(binary, fen, hash_mb, arm)
            for arm in ARMS
            for fen in POSITION_SET
            for hash_mb in HASHES]
    print(f"{len(jobs)} cells over {len(POSITION_SET)} positions", flush=True)

    rows = []
    started = time.monotonic()
    with ProcessPoolExecutor(max_workers=4) as pool:
        for i, row in enumerate(pool.map(run_one, jobs, chunksize=1), 1):
            rows.append(row)
            if i % 40 == 0:
                print(f"  {i}/{len(jobs)} {time.monotonic() - started:.0f}s", flush=True)

    with open(out_path, "w") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")

    errors = [r for r in rows if "error" in r]
    print(f"\nwrote {len(rows)} rows; {len(errors)} refused")

    by_key = {(r["fen"], r["hash"], r["arm"]): r for r in rows if "error" not in r}

    print(f"\n## Divergence from Hash 64 at go nodes {BUDGET}, by arm\n")
    print("| arm | Hash 1 | Hash 16 | Hash 256 | deep evictions (h16) | false hits (all) |")
    print("|---|---|---|---|---|---|")
    for arm in ARMS:
        cells = []
        for hash_mb in HASHES:
            if hash_mb == 64:
                continue
            differed = 0
            for fen in POSITION_SET:
                base = by_key.get((fen, 64, arm))
                other = by_key.get((fen, hash_mb, arm))
                if base is None or other is None:
                    continue
                if other["bestmove"] != base["bestmove"] or other["score"] != base["score"]:
                    differed += 1
            cells.append(f"**{differed}/{len(POSITION_SET)}**")
        h16_deep = sum(by_key[(fen, 16, arm)]["deep_evictions"]
                       for fen in POSITION_SET if (fen, 16, arm) in by_key)
        false_hits = sum(by_key[(fen, h, arm)]["false_hit"] or 0
                         for fen in POSITION_SET for h in HASHES if (fen, h, arm) in by_key)
        print(f"| {arm} | " + " | ".join(cells) + f" | {h16_deep} | {false_hits} |")

    # Sanity: the arms must actually change the tree, or the experiment is vacuous.
    print("\n## Arm liveness: mean depth and nodes, Hash 64\n")
    print("| arm | mean depth | mean nodes |")
    print("|---|---|---|")
    for arm in ARMS:
        cells = [by_key[(fen, 64, arm)] for fen in POSITION_SET if (fen, 64, arm) in by_key]
        if not cells:
            continue
        print(f"| {arm} | {sum(c['depth'] for c in cells)/len(cells):.1f} "
              f"| {sum(c['nodes'] or 0 for c in cells)/len(cells):.0f} |")


if __name__ == "__main__":
    main()
