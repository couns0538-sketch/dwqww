"""What threshold does the code's OWN rule imply? A sweep, not an opinion.

The horizon test says a stored score is reusable when the search that produced it
could not have been cut short by the fifty-move draw. A mate score is reusable
when it can still land before the counter reaches 100. Neither statement mentions
90: it appears only as `stored_clock < 90 && capped < 90`.

So the question "why 90 and not 89 or 91" is really "what is the largest safe
threshold". This script derives it from the arithmetic in the same function:

  * any non-mate score stored at clock s was searched to depth d, so its subtree
    reached clock s + d. A reuser at clock c reaches c + d.
  * for the score to remain a *non-draw* everywhere it is reused, both ends must
    stay under 100. A pair can be arbitrarily close to the boundary, so the only
    universally safe threshold is one that leaves the whole remaining span.

It reports, for each candidate threshold T, the cells where the function would
accept a score that the fifty-move rule can actually invalidate within the
stored depth -- i.e. cells the threshold FAILS to protect. The correct constant
is the smallest one with zero unsound acceptances, which the sweep prints.
"""
import csv

MV = 32000


def decide(stored, depth, score, current, T):
    capped = min(current, 100)
    if stored == capped:
        return True
    if score >= MV - 128 or score <= -(MV - 128):
        dist = MV - abs(score)
        if current + dist > 100:
            return False
    horizon = (stored + depth < 100 and current + depth < 100 and stored < T and capped < T)
    return horizon


def unsound(stored, depth, score, current, T):
    """True when the function accepts this cell but the fifty-move rule can fire
    inside the stored search horizon, so the accepted score is not a score of the
    game under the rule.

    The rule: a non-mate score stored with depth d claims knowledge to clock
    stored+d. Reusing it at clock c claims the same knowledge to c+d. If either
    end reaches 100 the subtree contained a forced draw the score does not
    account for.
    """
    if not decide(stored, depth, score, current, T):
        return False
    capped = min(current, 100)
    if stored == capped:
        # The short circuit accepts regardless; report it separately, not here.
        return False
    if score >= MV - 128 or score <= -(MV - 128):
        return False
    return stored + depth >= 100 or capped + depth >= 100


def main():
    clocks = range(0, 101)
    depths = range(0, 26)
    scores = [120, 0, -120]

    print(f"{'T':>4} {'accepted cells':>15} {'unsound accepts':>16} {'first unsound cell':>34}")
    first_clean = None
    for T in range(80, 101):
        acc = bad = 0
        example = None
        for stored in clocks:
            for depth in depths:
                for score in scores:
                    for current in clocks:
                        if decide(stored, depth, score, current, T):
                            acc += 1
                            if unsound(stored, depth, score, current, T):
                                bad += 1
                                if example is None:
                                    example = (stored, depth, score, current)
        print(f"{T:>4} {acc:>15} {bad:>16} {str(example):>34}")
        if bad == 0 and first_clean is None:
            first_clean = T
    print(f"\nsmallest threshold with zero unsound accepts: {first_clean}")

    # The specific cells a 89 / 90 / 91 threshold disagree on.
    print("\ncells where the verdict differs, T=89 vs T=90 (and 90 vs 91):")
    n = 0
    for stored in clocks:
        for depth in depths:
            for score in scores:
                for current in clocks:
                    a = decide(stored, depth, score, current, 89)
                    b = decide(stored, depth, score, current, 90)
                    c = decide(stored, depth, score, current, 91)
                    if a != b or b != c:
                        n += 1
    print(f"  {n} cells differ across the three thresholds (of "
          f"{len(clocks)*len(depths)*len(scores)*len(clocks)} total)")

    # Emit a plan for the object-level harness so the sweep is checked against the
    # real header rather than against this model.
    rows = []
    for T, tag in ((89, "thr89"), (90, "shipped"), (91, "thr91")):
        for cell in ((10, 89, 8, 120), (89, 10, 8, 120), (89, 90, 0, 120), (90, 89, 0, 120),
                     (90, 85, 8, MV - 15), (88, 89, 8, 120), (89, 91, 8, 120)):
            st, cur, dep, sc = cell
            rows.append((f"{tag} cell {st}->{cur} d{dep}", st, cur, dep, sc, int(decide(st, dep, sc, cur, T))))
    with open("/tmp/plan_threshold.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["label", "stored", "probe", "depth", "score", "expect"])
        w.writerows(rows)
    print("\nwrote /tmp/plan_threshold.csv")


if __name__ == "__main__":
    main()
