#!/usr/bin/env python3
"""analyse_draw.py OUTJSONL : the job-2 table, with every parse asserted.

Prints per group: n, how many scored exactly 0, how many non-zero, the score range, and the list of
records whose score could not be parsed. FAILS LOUDLY (exit 3) if any record has no parseable score,
because an unparsed score must never be read as a zero.
"""
import json
import sys
from collections import defaultdict

GROUPS = ["A_KvK", "B_KNvK", "C_KBvK", "D_KNNvK", "E_threefold", "F_clock99", "Control_KQvK"]


def main():
    path = sys.argv[1]
    recs = [json.loads(l) for l in open(path)]
    by = defaultdict(list)
    for r in recs:
        by[r["group"]].append(r)

    unparsed = [r for r in recs if r["score_value"] is None]
    print(f"records: {len(recs)}  |  records with NO parseable score: {len(unparsed)}")
    for r in unparsed[:10]:
        print(f"  UNPARSED {r['group']} #{r['i']} {r['position'][:60]}")

    print()
    print(f"{'group':<14} {'n':>3} {'zero':>5} {'nonzero':>8} {'min':>7} {'max':>7}  kinds")
    for g in GROUPS:
        rs = by.get(g, [])
        if not rs:
            print(f"{g:<14} {'0':>3}  (no records)")
            continue
        vals = [r["score_value"] for r in rs if r["score_value"] is not None]
        kinds = sorted({r["score_kind"] for r in rs if r["score_kind"]})
        zero = sum(1 for v in vals if v == 0)
        print(f"{g:<14} {len(rs):>3} {zero:>5} {len(vals)-zero:>8} "
              f"{min(vals) if vals else '-':>7} {max(vals) if vals else '-':>7}  {','.join(kinds)}")

    print()
    print("non-zero records in detail:")
    for g in GROUPS:
        for r in by.get(g, []):
            if r["score_value"] not in (None, 0):
                print(f"  {g:<12} #{r['i']:>2} {r['score_kind']:>4} {r['score_value']:>7} "
                      f"best={r['bestmove']}  {r['position'][:52]}")

    if unparsed:
        print()
        print("CHECK FAILED — this table is NOT a result: some records carried no score, and an "
              "absent score must not be counted as a draw.")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
