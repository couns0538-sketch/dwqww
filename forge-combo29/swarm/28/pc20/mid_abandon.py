#!/usr/bin/env python3
"""mid_abandon.py — what would abandoning INSIDE an iteration buy?

The rule in GATED_SOFT_STOP_RULE.md fires at iteration boundaries, so it cannot prevent the cost of the
iteration that overran. This measures the larger change: abandon the current iteration as soon as the soft
plan is crossed.

There are TWO distinct cases and they have very different economics. Conflating them would overstate or
understate the case, so both are computed separately.

CASE A — abandon an iteration that WOULD have completed (the 10 "overrun" iterations).
  The iteration started at t_prev and finished at t_i, with t_prev < B < t_i. Abandoning at B saves
  exactly (t_i - B) ms — that part is exact, not an estimate, because "abandon when soft is crossed" means
  stopping at time B. But it LOSES that depth, so the cost is 1 ply.
  Data: the committed ladders (wtime 10000, so B = 454 is the true plan; B = 317 is the 6 s plan applied
  to the same iteration costs, which is an approximation and is labelled as one).

CASE B — abandon an iteration that would have been DISCARDED anyway.
  Here the search ran past its last completed iteration to the hard limit and finished nothing (S-F31).
  Abandoning saves the WHOLE overspend and loses NOTHING, because the depth was never going to be kept.
  Data: out_real/realclock_*.tsv at the real 6+0.06 control, where wall_ms - engine_time_ms is exactly
  that discarded span.

Case B is the strictly better target: same mechanism, zero ply cost. That is the finding to check.

Usage: mid_abandon.py
"""
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def parse_ladders():
    out = []
    for name in ("ladder_base_w10000.tsv", "ladder_PC20_w10000.tsv"):
        p = os.path.join(HERE, name)
        if not os.path.exists(p):
            continue
        for line in open(p).read().splitlines()[1:]:
            f = line.split("\t")
            if len(f) < 6:
                continue
            seq = []
            for tok in f[1].split():
                d, t = tok.split(":")
                seq.append((int(d), float(t)))
            if len(seq) >= 2:
                out.append((os.path.basename(p), f[0], seq))
    return out


def load_tsv(path):
    rows = []
    with open(path) as fh:
        head = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) == len(head):
                rows.append(dict(zip(head, p)))
    return rows


def pct(v, q):
    s = sorted(v)
    k = (len(s) - 1) * q / 100.0
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def main() -> int:
    ladders = parse_ladders()

    print("## CASE A — abandon an iteration that would have COMPLETED (costs 1 ply)")
    print()
    for B, note in ((454.0, "the true 10 s plan"), (317.0, "the 6 s plan applied to 10 s iteration costs (approximation)")):
        cases = []
        for fname, idx, seq in ladders:
            for i in range(1, len(seq)):
                t_prev, t_i = seq[i - 1][1], seq[i][1]
                cost = t_i - t_prev
                if cost <= 0:
                    continue
                if t_prev < B < t_i:          # the plan is crossed INSIDE this iteration
                    cases.append({"f": fname, "idx": idx, "d": seq[i][0], "t_prev": t_prev,
                                  "t_i": t_i, "cost": cost, "save": t_i - B,
                                  "frac_after": (t_i - B) / cost})
        print(f"### B = {B:.0f} ms — {note}")
        print()
        if not cases:
            print("no cases")
            continue
        print(f"{len(cases)} iterations cross the soft plan inside themselves and complete.")
        print()
        print("| ladder | position | depth | iteration started | finished | cost | saved by abandoning at B "
              "| fraction of the iteration wasted | plies lost |")
        print("|---|---|---|---|---|---|---|---|---|")
        for c in sorted(cases, key=lambda x: -x["save"]):
            print(f"| {c['f'][:12]} | #{c['idx']} | d{c['d']} | {c['t_prev']:.0f} | {c['t_i']:.0f} | "
                  f"{c['cost']:.0f} | **{c['save']:.0f} ms** | {c['frac_after']*100:.0f} % | 1 |")
        saves = [c["save"] for c in cases]
        print()
        print(f"saving: median {statistics.median(saves):.0f} ms, mean {statistics.mean(saves):.0f} ms, "
              f"max {max(saves):.0f} ms, total {sum(saves):.0f} ms across {len(cases)} cases")
        print()

    print("## CASE B — abandon an iteration that would have been DISCARDED (costs NOTHING)")
    print()
    print("At the real 6+0.06 control, `wall_ms - engine_time_ms` is time spent on an iteration the search")
    print("threw away. Abandoning at the soft plan recovers that span at ZERO ply cost.")
    print()
    print("| build | n | median discarded span | max discarded span | searches where it is >50 ms |")
    print("|---|---|---|---|---|")
    allspans = {}
    for label in ("base", "PC20"):
        p = os.path.join(HERE, "out_real", f"realclock_{label}.tsv")
        if not os.path.exists(p):
            continue
        rows = load_tsv(p)
        spans = []
        for r in rows:
            if not r["engine_time_ms"]:
                continue
            span = float(r["wall_ms"]) - float(r["engine_time_ms"])
            spans.append(span)
        allspans[label] = spans
        print(f"| {label} | {len(spans)} | {statistics.median(spans):.0f} ms | {max(spans):.0f} ms | "
              f"{sum(1 for s in spans if s > 50)} |")
    print()
    for label, spans in allspans.items():
        if not spans:
            continue
        tot = sum(spans)
        print(f"**{label}**: {len(spans)} searches discard a total of {tot:.0f} ms; the 90th percentile "
              f"span is {pct(spans,90):.0f} ms.")
    print()

    print("## The comparison the owner needs")
    print()
    print("| change | ply cost | median gain per case | max gain | risk |")
    print("|---|---|---|---|---|")
    a317 = [c for c in (lambda: [
        {"save": seq[i][1] - 317.0} for _f, _i2, seq in ladders
        for i in range(1, len(seq))
        if seq[i-1][1] < 317.0 < seq[i][1] and seq[i][1] - seq[i-1][1] > 0])() ]
    a454 = [c for c in (lambda: [
        {"save": seq[i][1] - 454.0} for _f, _i2, seq in ladders
        for i in range(1, len(seq))
        if seq[i-1][1] < 454.0 < seq[i][1] and seq[i][1] - seq[i-1][1] > 0])() ]
    b = allspans.get("PC20", [])
    if a317:
        print(f"| mid-iteration abandon (B=317, completing iteration) | 1 ply | "
              f"{statistics.median([c['save'] for c in a317]):.0f} ms | "
              f"{max(c['save'] for c in a317):.0f} ms | loses the depth it was working on |")
    if b:
        print(f"| mid-iteration abandon (discarded iteration) | **0 plies** | "
              f"{statistics.median(b):.0f} ms | {max(b):.0f} ms | none — that depth was never kept |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
