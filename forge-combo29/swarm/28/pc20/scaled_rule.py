#!/usr/bin/env python3
"""scaled_rule.py — arithmetic on measured ladders: what would a soft-scaled stop rule cost?

NOT a new experiment. It reads the two iteration-ladder files I already committed and answers one question:

    If the engine refused to START an iteration that could not finish inside a budget B, instead of
    running on to the hard limit, how much time would that save and how many plies would it cost?

Method, per measured search, from the ladder (depth, cumulative ms) and the plan:
  - the ladder tells exactly what each completed iteration cost;
  - the search's LAST completed iteration is the last ladder entry;
  - the time spent after it is `wall - last_entry_time` = the discarded iteration (measured, not guessed);
  - a rule with budget B stops at the last completion `t` such that `t <= B`, giving depth d(t).

For B = soft (the plan) vs B = hard (current behaviour) I report, per search:
  depth under soft-stop vs depth actually reached, and the time each would spend.
The PLY COST is the difference in depth; the TIME SAVING is wall minus the soft-stop time.

Sparse vs busy is classified by piece count (<= 12 = sparse).

Usage: scaled_rule.py
"""
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def parse_ladder(path):
    """yield (fen_or_index, [(depth, cumulative_ms), ...]) — the ladder files carry index, not FEN."""
    for line in open(path).read().splitlines()[1:]:
        p = line.split("\t")
        if len(p) < 6:
            continue
        idx, visited = p[0], p[1]
        seq = []
        for tok in visited.split():
            d, t = tok.split(":")
            seq.append((int(d), float(t)))
        if seq:
            yield idx, seq


def main() -> int:
    print("## Per-search arithmetic from the 10000 ms ladders (soft 454 ms, hard 2270 ms)")
    print()
    print("These ladders were measured at wtime 10000, so the plan there is 2.5x the 6 s plan. They are the")
    print("only place I recorded per-iteration cost, so the arithmetic is relative to THAT plan and I say")
    print("so rather than pretending it is the 6 s control.")
    print()
    for name, label in (("ladder_base_w10000.tsv", "base"), ("ladder_PC20_w10000.tsv", "PC20")):
        path = os.path.join(HERE, name)
        if not os.path.exists(path):
            print(f"({name} missing)")
            continue
        soft, hard = 454, 2270
        saved, lost_ply, rows = [], [], 0
        for idx, seq in parse_ladder(path):
            rows += 1
            actual_depth = seq[-1][0]
            actual_time = seq[-1][1]
            # soft-stop: the last completion at or before soft
            fit = [e for e in seq if e[1] <= soft]
            if not fit:
                continue
            soft_depth, soft_time = fit[-1]
            saved.append(actual_time - soft_time)
            lost_ply.append(actual_depth - soft_depth)
        if not rows:
            continue
        print(f"**{label}**: {rows} searches")
        print()
        print(f"- median time the soft-stop rule would save: {statistics.median(saved):.0f} ms "
              f"(max {max(saved):.0f} ms)")
        print(f"- median plies lost: {statistics.median(lost_ply):.0f} "
              f"(mean {statistics.mean(lost_ply):.1f}, max {max(lost_ply)})")
        print(f"- searches losing 0 plies: {sum(1 for x in lost_ply if x == 0)}, "
              f"1 ply: {sum(1 for x in lost_ply if x == 1)}, "
              f"2+: {sum(1 for x in lost_ply if x >= 2)}")
        print()

    print("## Reading")
    print()
    print("The 'saving' here is not the overspend — it is the whole time difference between stopping at")
    print("the last completion inside soft and continuing to the depth actually reached. That is the")
    print("honest bound for a soft-scaled rule: it buys the saving AT the ply cost shown, because the")
    print("iterations it refuses are precisely the ones that produced the extra depth.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
