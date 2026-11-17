#!/usr/bin/env python3
"""Summarise a determinism.jsonl run.

Every number this prints is computed from the rows; nothing is carried in prose.
The two questions are kept apart because they fail for different reasons:

  Q1 reproducible AT a thread count  -- do repeats of the same search agree?
  Q2 same AS Threads 1              -- does the threaded search reach the same tree?

`nodes` is a SUM over workers above Threads 1 (search.cpp:2696-2705), so Q2 on
nodes is not expected to hold and its failure is arithmetic, not a defect.

A third column counts the positions where the move differs while the score is
identical -- a tie-break flip, which is a weaker event than a score change.

Usage: python3 analyse_det.py <jsonl> [threads...]
"""
import json
import sys
from collections import defaultdict


def load(path):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    if not rows:
        raise SystemExit(f"no rows in {path}")
    return rows


def key(sig):
    """The identity of one search. Wall time is deliberately NOT part of it."""
    if sig["no_info_depth"]:
        return ("NOINFO", sig["bestmove"])
    return (sig["nodes"], sig["score_kind"], sig["score"], sig["bestmove"])


def main():
    path = sys.argv[1]
    threads_wanted = [int(t) for t in sys.argv[2:]] or None
    rows = load(path)

    by_thread = defaultdict(list)
    for r in rows:
        by_thread[r["threads"]].append(r)

    print(f"file: {path}")
    print(f"rows: {len(rows)}")
    limits = sorted({r["limit"] for r in rows})
    print(f"limits: {limits}")
    print()

    # ---- Q1: reproducibility inside each thread count
    print("Q1  reproducible AT a thread count (do repeats of the same search agree?)")
    print(f"{'thr':>4} {'pos':>4} {'reps':>5} {'nodes differ':>13} {'score differ':>14} "
          f"{'move differ':>12} {'move-differs-score-same':>24} {'no-info':>8}")
    summary = {}
    for th in sorted(by_thread):
        if threads_wanted and th not in threads_wanted:
            continue
        per_pos = defaultdict(list)
        for r in by_thread[th]:
            per_pos[r["idx"]].append(r)
        n_pos = len(per_pos)
        reps = len(next(iter(per_pos.values())))
        nodes_d = score_d = move_d = move_only = noinfo = 0
        for idx, rs in per_pos.items():
            sigs = [key(r["sig"]) for r in rs]
            if any(r["sig"]["no_info_depth"] for r in rs):
                noinfo += 1
            ns = {s[0] for s in sigs}
            sc = {(s[1], s[2]) for s in sigs}
            mv = {s[-1] for s in sigs}
            if len(ns) > 1:
                nodes_d += 1
            if len(sc) > 1:
                score_d += 1
            if len(mv) > 1:
                move_d += 1
                if len(sc) == 1:
                    move_only += 1
        summary[th] = dict(n_pos=n_pos, reps=reps, nodes_differ=nodes_d,
                           score_differ=score_d, move_differ=move_d,
                           move_only=move_only, noinfo=noinfo)
        print(f"{th:>4} {n_pos:>4} {reps:>5} {nodes_d:>13} {score_d:>14} {move_d:>12} "
              f"{move_only:>24} {noinfo:>8}")
    print()

    # ---- Q2: agreement with Threads 1
    if 1 in by_thread:
        print("Q2  same AS Threads 1 (first repeat of each position; nodes are a thread SUM, so")
        print("    a nodes mismatch above Threads 1 is arithmetic, not a defect)")
        print(f"{'thr':>4} {'positions':>10} {'nodes same':>11} {'score same':>11} {'move same':>10}")
        base = {}
        for r in by_thread[1]:
            if r["rep"] == 0:
                base[r["idx"]] = key(r["sig"])
        for th in sorted(by_thread):
            if th == 1 or (threads_wanted and th not in threads_wanted):
                continue
            cur = {r["idx"]: key(r["sig"]) for r in by_thread[th] if r["rep"] == 0}
            common = sorted(set(base) & set(cur))
            ns = sum(1 for i in common if base[i][0] == cur[i][0])
            ss = sum(1 for i in common if (base[i][1], base[i][2]) == (cur[i][1], cur[i][2]))
            ms = sum(1 for i in common if base[i][-1] == cur[i][-1])
            print(f"{th:>4} {len(common):>10} {ns:>11} {ss:>11} {ms:>10}")
        print()

    # ---- the rows behind the numbers, so a reader can see them
    print("per-position detail, Threads 4 (first 3 positions):")
    shown = 0
    for idx in sorted({r["idx"] for r in by_thread.get(4, [])}):
        rs = [r for r in by_thread[4] if r["idx"] == idx]
        print(f"  pos {idx} {rs[0]['fen'][:44]}")
        for r in rs:
            s = r["sig"]
            print(f"    rep{r['rep']} nodes={s.get('nodes')} score={s.get('score_kind')}{s.get('score')} "
                  f"move={s.get('bestmove')} wall={r['wall']}")
        shown += 1
        if shown >= 3:
            break
    return 0


if __name__ == "__main__":
    sys.exit(main())
