"""How much does each predicate of score_usable actually decide?

The function's four branches are not four independent guards: branch B (the
mate-distance test) and branch D (the horizon test) overlap, and the exact-clock
short circuit in branch A pre-empts both. This script partitions every
(stored, depth, score, current) cell by which predicate *decided* the verdict,
so "verified" can mean something narrower than "the branch printed".
"""
import itertools
import json
import sys

MV = 32000
MATE_IN_MAX_PLY = MV - 128


def predicates(stored, depth, score, current):
    capped = min(current, 100)
    is_mate = score >= MATE_IN_MAX_PLY or score <= -MATE_IN_MAX_PLY
    dist = MV - abs(score) if is_mate else None
    exact = stored == capped
    mate_kill = is_mate and (current + dist > 100)
    horizon = stored + depth < 100 and current + depth < 100 and stored < 90 and capped < 90
    return exact, mate_kill, horizon


def verdict(stored, depth, score, current):
    exact, mate_kill, horizon = predicates(stored, depth, score, current)
    if exact:
        return True
    if mate_kill:
        return False
    return horizon


def counterfactual(stored, depth, score, current):
    """What would the verdict be with each predicate removed? The delta is that
    predicate's decision power on this cell."""
    exact, mate_kill, horizon = predicates(stored, depth, score, current)
    base = verdict(stored, depth, score, current)
    out = {}
    # without the exact-clock short circuit
    if mate_kill:
        no_exact = False
    else:
        no_exact = horizon
    out["exact"] = base != no_exact
    # without the mate test
    out["mate"] = base != (True if exact else horizon)
    # without the horizon test
    out["horizon"] = base != (True if exact else (False if mate_kill else True))
    return base, out


def main():
    clocks = range(0, 101)
    depths = [0, 1, 2, 4, 8, 16, 32, 49, 50, 64]
    mates = [MV - d for d in (1, 2, 3, 5, 10, 15, 20, 40, 100)] + [0, 1, 50, 120, -120]

    decisive = {"exact": 0, "mate": 0, "horizon": 0}
    total = 0
    mate_decisive_cells = []
    for stored, depth, score, current in itertools.product(clocks, depths[:-3], mates, clocks):
        total += 1
        base, d = counterfactual(stored, depth, score, current)
        for k, v in d.items():
            if v:
                decisive[k] += 1
        if d["mate"]:
            mate_decisive_cells.append((stored, depth, score, current, base))

    print(f"cells                       {total}")
    print(f"exact-clock is decisive     {decisive['exact']:>10}  ({100*decisive['exact']/total:.2f}%)")
    print(f"mate test is decisive       {decisive['mate']:>10}  ({100*decisive['mate']/total:.2f}%)")
    print(f"horizon test is decisive    {decisive['horizon']:>10}  ({100*decisive['horizon']/total:.2f}%)")
    print(f"\nmate-decisive cells: {len(mate_decisive_cells)}")
    for r in mate_decisive_cells[:20]:
        print(f"  stored={r[0]:3} depth={r[1]:2} score={r[2]:6} current={r[3]:3} -> usable={r[4]}")


if __name__ == "__main__":
    main()
