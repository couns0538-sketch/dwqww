#!/usr/bin/env python3
"""analyze_ceiling.py RESULTSJSONL — the ceiling as a measured function of |N|.

Reports, per |N|: how many claims were fully adjudicated, how many hit the time cap, and the time/memo at the largest
completed budget. Also prints the largest |N| at which MOST claims adjudicate inside the cap, which is the number a
reuser needs and the one I had previously been quoting from three boards of anecdote.

A timeout is counted as UNADJUDICATED, never as a negative answer about the position.
"""
import json
import statistics
import sys


def main():
    recs = [json.loads(l) for l in open(sys.argv[1])]
    by = {}
    for r in recs:
        k = abs(r["value"])
        by.setdefault(k, []).append(r)

    print(f"{'|N|':>3} {'claims':>6} {'adj':>4} {'timeout':>7}  {'median last-budget secs':>23}  {'max memo':>9}  verdicts")
    print("-" * 96)
    for k in sorted(by):
        rs = by[k]
        adj = [r for r in rs if r["adjudicated"]]
        un = [r for r in rs if not r["adjudicated"]]
        secs = [r["steps"][-1]["secs"] for r in adj if r["steps"]]
        memo = [r["steps"][-1]["memo"] for r in adj if r["steps"]]
        verdicts = {}
        for r in adj:
            verdicts[r["verdict"]] = verdicts.get(r["verdict"], 0) + 1
        med = f"{statistics.median(secs):.1f}" if secs else "-"
        mx = max(memo) if memo else "-"
        print(f"{k:>3} {len(rs):>6} {len(adj):>4} {len(un):>7}  {med:>23}  {str(mx):>9}  {verdicts or '-'}")

    print()
    print("THE CEILING (largest |N| where most claims adjudicate):")
    ceiling = None
    for k in sorted(by):
        rs = by[k]
        adj = sum(1 for r in rs if r["adjudicated"])
        if adj * 2 >= len(rs):
            ceiling = k
        else:
            print(f"  |N|={k}: {adj}/{len(rs)} adjudicated -> below half, ceiling stops below this")
            break
    print(f"  MEASURED CEILING = |N| {ceiling}  (most claims adjudicate at this distance, not beyond)")

    tot = len(recs)
    adj = sum(1 for r in recs if r["adjudicated"])
    wrong = [r for r in recs if r["adjudicated"] and r["verdict"] != "CORRECT"]
    print()
    print(f"TOTAL: {adj}/{tot} adjudicated; {tot-adj} NOT ADJUDICATED (budget exhausted, no verdict)")
    print(f"WRONG among adjudicated: {len(wrong)}")
    for r in wrong:
        print(f"  claim mate {r['value']} -> truth mate {r['truth']} ({r['verdict']})  {r['fen']}")
    print()
    print("Timeouts are reported as unadjudicated on purpose: a budget that ran out is not evidence the mate is absent.")


if __name__ == "__main__":
    main()
