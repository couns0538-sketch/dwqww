"""Generate the plan for tt_probe_harness.cpp.

The *expectation* for each cell comes from the Python model below, which was
written from the function's doc comment and the fifty-move rule, not from the
C++. The C++ then stores real entries through the real TranspositionTable and
reports what the shipped code does. Expectation and observation are therefore
produced by two independent implementations -- the arrangement that caught two
arithmetic errors this seat had written by hand into the C++ table
(90->85 mate15 and 99->98 mate1, both of which the horizon test refuses
regardless of the mate test).

Output: a CSV of label,stored,probe,depth,score,expect
"""
import csv
import itertools
import sys

MV = 32000
MATE_IN_MAX_PLY = MV - 128


def is_mate(score):
    return score >= MATE_IN_MAX_PLY or score <= -MATE_IN_MAX_PLY


def model(stored, depth, score, current):
    """score_usable per its doc comment, exact-clock short circuit included."""
    capped = current if current < 100 else 100
    if stored == capped:
        return True
    if is_mate(score):
        distance = MV - abs(score)
        if current + distance > 100:
            return False
    inside = (stored + depth < 100 and current + depth < 100 and stored < 90 and capped < 90)
    return inside


def decisive(store_pred):
    """Cells where removing store_pred's clause flips the verdict: the only cells
    that can show that clause is load-bearing rather than redundant."""
    out = []
    clocks = range(0, 101)
    for stored, current, depth, dist in itertools.product(clocks, clocks, range(0, 12), (1, 3, 10, 15, 20, 40)):
        score = MV - dist
        if model(stored, depth, score, current):
            continue
        if store_pred == "mate":
            # horizon test alone would accept it
            if (stored + depth < 100 and current + depth < 100 and stored < 90 and min(current, 100) < 90
                    and stored != min(current, 100)):
                out.append((stored, current, depth, score))
        elif store_pred == "horizon":
            if not is_mate(score) and stored != min(current, 100):
                out.append((stored, current, depth, score))
    return out


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/plan.csv"
    rows = []

    def add(label, stored, probe, depth, score):
        rows.append((label, stored, probe, depth, score, model(stored, depth, score, probe)))

    # --- Branch A: exact clock match, sweeps every clock.
    for c in (0, 1, 10, 50, 88, 89, 90, 91, 95, 99, 100):
        add(f"A exact {c} cp", c, c, 8, 120)
    add("A exact 100->120capped", 100, 120, 8, 120)
    add("A exact 99->120capped", 99, 120, 8, 120)
    add("A exact 90 mate15", 90, 90, 8, MV - 15)
    add("A exact 95 mate20", 95, 95, 8, MV - 20)

    # --- Branch B: the mate test. Include every cell where it is decisive.
    add("B 90->95 mate15", 90, 95, 8, MV - 15)
    add("B 90->91 mate15", 90, 91, 8, MV - 15)
    add("B 90->86 mate15", 90, 86, 8, MV - 15)
    add("B 90->85 mate15", 90, 85, 8, MV - 15)
    add("B 80->90 mate15", 80, 90, 8, MV - 15)
    add("B 99->100 mate3", 99, 100, 2, MV - 3)
    add("B 98->99 mate1", 98, 99, 1, MV - 1)
    add("B 99->98 mate1", 99, 98, 1, MV - 1)
    add("B 90->95 -mate15", 90, 95, 8, -(MV - 15))
    add("B 90->95 mate15 depth0", 90, 95, 0, MV - 15)
    dec = decisive("mate")
    for i, (st, cur, dep, sc) in enumerate(dec[:6]):
        add(f"B decisive{i} {st}->{cur} d{dep} m{MV-sc}", st, cur, dep, sc)

    # --- Branch C: inside horizon, clocks differ, both < 90.
    add("C 10->20 d8", 10, 20, 8, 120)
    add("C 10->89 d8", 10, 89, 8, 120)
    add("C 89->10 d8", 89, 10, 8, 120)
    add("C 50->50 d49", 50, 50, 49, 120)
    add("C 0->0 d0", 0, 0, 0, 120)
    add("C 5->15 d84", 5, 15, 84, 120)

    # --- Branch D: outside horizon.
    add("D 10->20 d90", 10, 20, 90, 120)
    add("D 95->10 d4", 95, 10, 4, 120)
    add("D 10->95 d4", 10, 95, 4, 120)
    add("D 50->60 d50", 50, 60, 50, 120)
    add("D 89->90 d0", 89, 90, 0, 120)
    add("D 90->89 d0", 90, 89, 0, 120)

    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["label", "stored", "probe", "depth", "score", "expect"])
        for r in rows:
            w.writerow([r[0], r[1], r[2], r[3], r[4], int(r[5])])
    print(f"wrote {path}: {len(rows)} cells, "
          f"{sum(1 for r in rows if r[5])} expect usable, "
          f"{sum(1 for r in rows if not r[5])} expect refused")
    print(f"mate-decisive cells available: {len(dec)}")


if __name__ == "__main__":
    main()
