#!/usr/bin/env python3
"""Parallel, globally deadline-bounded runner for verify.py.

Each row is independent and each oracle query is a fresh process, so rows can
run concurrently without shared state -- which also makes the S4 state-leak bug
(recursion unwound without popping, only on the timeout path) structurally
impossible here.

A GLOBAL budget is enforced. When it expires the run stops and whatever rows are
finished are the measurement; the rest are reported as BUDGET_CUT, separate from
UNVERIFIABLE, because "I ran out of my own budget" and "the checker could not
decide this claim" are different facts and must not be merged.
"""
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.path.insert(0, "/tmp/fw")

# Per-claim deadlines. S4 measured |N|<=3 safe at 27/27, |N|=4 the ceiling,
# |N|>=5 never confirmed. The deadlines below are generous relative to the
# measured costs (S4: half B at n=3 took 7 s, half A pinned 109 s) and are
# bounded so no single claim can consume the whole run.
DEADLINE = {1: 60_000, 2: 90_000, 3: 150_000, 4: 240_000, 5: 240_000, 6: 240_000}
DEFAULT_DEADLINE = 180_000


def deadline_for(n):
    return DEADLINE.get(n, DEFAULT_DEADLINE)


def one_row(row, global_deadline_epoch):
    """Worker: verify one row. Returns a verdict dict."""
    import chess
    import verify

    if time.time() > global_deadline_epoch:
        return {"id": row["id"], "class": "BUDGET_CUT", "reason": "global budget exhausted before start"}

    board = chess.Board(row["fen"])
    if not board.is_valid():
        return {"id": row["id"], "class": "UNVERIFIABLE", "reason": "invalid fen by python-chess"}

    n = abs(row["score_value"])
    verdict = {
        "id": row["id"], "fen": row["fen"], "claimed_N": row["score_value"],
        "abs_N": n, "abs_n": n,
        "pv_len": row["pv_len"], "pv_len_wanted": row["pv_len_wanted"],
        "pv_len_filter_pass": row["pv_len_filter_pass"],
        "pv_len_would_reject": not row["pv_len_filter_pass"],
        "deadline_ms": deadline_for(n),
        "engine_sha256": row["engine_sha256"], "base_commit": row["base_commit"],
        "options": row["options"], "depth": row["depth"],
        "oracle_version": "matelabels-oracle v1",
        "python_chess_valid": True,
    }
    # Shrink each query's deadline to whatever global budget remains, so a late
    # row cannot overrun the run's own deadline.
    remaining_ms = int((global_deadline_epoch - time.time()) * 1000)
    if remaining_ms < 5000:
        verdict.update(class_="", **{})
        verdict["class"] = "BUDGET_CUT"
        verdict["reason"] = "global budget exhausted"
        return verdict
    verdict["deadline_ms"] = min(verdict["deadline_ms"], remaining_ms)

    if row["score_value"] < 0:
        return verify.classify_loss(row, verdict)
    return verify.classify_win(row, verdict)


def main():
    in_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/fw/harvest.jsonl"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "/tmp/fw/verdicts.jsonl"
    budget_s = int(sys.argv[3]) if len(sys.argv) > 3 else 5400
    workers = int(sys.argv[4]) if len(sys.argv) > 4 else 4

    rows = [json.loads(l) for l in open(in_path)]
    done = set()
    try:
        for line in open(out_path):
            try:
                done.add(json.loads(line)["id"])
            except Exception:
                pass
    except FileNotFoundError:
        pass

    todo = [r for r in rows if r["id"] not in done]
    # Smallest claims first: the cheap cells fill early so a cut still leaves a
    # usable, unbiased-on-distance partial result.
    todo.sort(key=lambda r: (abs(r["score_value"]), r["id"]))

    deadline_epoch = time.time() + budget_s
    t0 = time.time()
    print(f"{len(todo)} rows to verify, {workers} workers, budget {budget_s}s", flush=True)

    finished = 0
    with open(out_path, "a") as out, ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(one_row, r, deadline_epoch): r for r in todo}
        for fut in as_completed(futures):
            r = futures[fut]
            try:
                v = fut.result()
            except Exception as exc:  # a crash must be a recorded verdict, not a hole
                v = {"id": r["id"], "class": "UNVERIFIABLE", "reason": f"worker exception: {exc!r}"}
            out.write(json.dumps(v) + "\n")
            out.flush()
            finished += 1
            if finished % 10 == 0 or finished == len(todo):
                print(f"  {finished}/{len(todo)}  wall={time.time()-t0:.0f}s  "
                      f"last={v['id']} {v['class']}", flush=True)

    print(f"\ndone {finished} rows in {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
