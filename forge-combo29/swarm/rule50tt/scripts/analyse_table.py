"""Independent model of TTEntry::score_usable, and a comparison against the grid
the C++ harness emits. The model is written from the *comment* ("Below 90 ... two
clocks ... exact match stays usable except a mate the remaining half-moves cannot
deliver") so a disagreement is evidence about the code, not a restatement of it.
"""
import json
import sys
import collections

MATE_VALUE = 32000
MATE_IN_MAX_PLY = MATE_VALUE - 128


def is_mate(score):
    return score >= MATE_IN_MAX_PLY or score <= -MATE_IN_MAX_PLY


def model(stored, depth, score, current):
    """The rule as documented, with NO short-circuit on an exact clock match.

    This is the 'ideal' reading: an exact clock match is usable, except a mate
    the remaining half-moves cannot deliver. Unlike the shipped code this
    applies the mate test before the exact-match test.
    """
    capped = current if current < 100 else 100
    if is_mate(score):
        distance = MATE_VALUE - abs(score)
        if current + distance > 100:
            return False                 # mate cannot land before the counter hits 100
        return True                      # exact or not: the mate is still deliverable
    if stored == capped:
        return True
    inside = (stored + depth < 100 and current + depth < 100 and stored < 90 and capped < 90)
    return inside


def model_as_shipped_order(stored, depth, score, current):
    """Same predicates, but the exact-clock test first, like the C++."""
    capped = current if current < 100 else 100
    if stored == capped:
        return True
    if is_mate(score):
        distance = MATE_VALUE - abs(score)
        if current + distance > 100:
            return False
    inside = (stored + depth < 100 and current + depth < 100 and stored < 90 and capped < 90)
    return inside or stored == capped


def main(path):
    rows = json.load(open(path))["rows"]
    dis_shipped, dis_doc = [], []
    branch_counts = collections.Counter()
    for r in rows:
        s, d, sc, c = r["stored"], r["depth"], r["score"], r["current"]
        if r["usable"] != model_as_shipped_order(s, d, sc, c):
            dis_shipped.append(r)
        if r["usable"] != model(s, d, sc, c):
            dis_doc.append(r)
        branch_counts[(r["branch"], r["usable"])] += 1

    print(f"rows                     {len(rows)}")
    print("branch x verdict:")
    for k in sorted(branch_counts):
        print(f"  {k[0]:20} usable={str(k[1]):5} {branch_counts[k]}")
    print(f"disagrees with shipped-order model: {len(dis_shipped)}")
    print(f"disagrees with documented-order model: {len(dis_doc)}")

    # The interesting disagreement: exact clock match whose mate cannot land.
    exact_but_undeliverable = [
        r for r in rows
        if r["stored"] == min(r["current"], 100) and is_mate(r["score"])
        and r["current"] + (MATE_VALUE - abs(r["score"])) > 100
    ]
    print(f"\nexact-clock mate entries where current+distance>100 (accepted by the short-circuit):")
    for r in exact_but_undeliverable[:12]:
        print("   ", r)
    print(f"   total {len(exact_but_undeliverable)}")

    # Does any grid cell reach branch B at all?
    b = [r for r in rows if r["branch"] == "B:mate-too-long" and not r["usable"]]
    print(f"\nbranch B (mate refused) cells in the hand-built set: {len(b)}")
    for r in b:
        print("   ", r)
    return 0 if not dis_shipped else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/sut.json"))
