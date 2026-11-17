#!/usr/bin/env python3
"""Turn verdicts into the reported rate, with every denominator stated.

Rules this script enforces:
  * a rate always prints its denominator;
  * UNVERIFIABLE and BUDGET_CUT are separate classes and are never folded into
    "wrong" -- S4 withdrew exactly that error (10 of 190 short-PV claims were
    "unverifiable rather than false");
  * every wrong row carries its seldepth, depth, nodes and PV length;
  * the PV-length filter's measured value is computed against the WRONG set,
    with the UNVERIFIABLE set reported alongside so its coverage cannot be
    overstated.
"""
import collections
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths

HARVEST = paths.work_file("harvest_seldepth.jsonl")
VERDICTS = paths.work_file("verdicts.jsonl")


def main():
    labels = {json.loads(l)["id"]: json.loads(l) for l in open(HARVEST)}
    verdicts = [json.loads(l) for l in open(VERDICTS)]

    # Join, and keep only rows that have both a label and a verdict.
    rows = []
    for v in verdicts:
        lab = labels.get(v["id"])
        if lab is None:
            continue
        merged = dict(v)
        merged["seldepth"] = lab.get("seldepth")
        merged["depth"] = lab.get("depth")
        merged["nodes"] = lab.get("nodes")
        merged["pv"] = lab.get("pv")
        merged["pv_len"] = lab.get("pv_len")
        merged["bestmove"] = lab.get("bestmove")
        merged["score_value"] = lab.get("score_value")
        rows.append(merged)

    rows.sort(key=lambda r: (r["abs_n"], r["id"]))
    total_labels = len(labels)
    n = len(rows)

    classes = collections.Counter(r["class"] for r in rows)
    exact = classes.get("EXACT", 0)
    over = classes.get("WRONG_OVERSTATED", 0)
    under = classes.get("WRONG_UNDERSTATED", 0)
    mvwrong = classes.get("MV_WRONG", 0)
    unver = classes.get("UNVERIFIABLE", 0)
    cut = classes.get("BUDGET_CUT", 0)
    wrong = over + under + mvwrong
    verified = exact + wrong

    print("=" * 78)
    print("MATE-LABEL VERIFICATION — measured corpus")
    print("=" * 78)
    print(f"labels harvested                 : {total_labels}")
    print(f"labels with a verdict            : {n}")
    print(f"  verified (decided both halves) : {verified}")
    print(f"    EXACT                        : {exact}")
    print(f"    WRONG_OVERSTATED             : {over}")
    print(f"    WRONG_UNDERSTATED            : {under}")
    print(f"    MV_WRONG (distance ok, move) : {mvwrong}")
    print(f"  unverifiable                   : {unver}")
    print(f"  budget cut                     : {cut}")
    print()
    if verified:
        print(f"WRONG RATE among verified        : {wrong}/{verified} = {100*wrong/verified:.1f}%")
    print(f"UNVERIFIABLE RATE among attempted: {unver}/{n} = {100*unver/max(n,1):.1f}%")

    print()
    print("-" * 78)
    print("BY CLAIMED |N|  (rate always with its denominator)")
    print("-" * 78)
    print(f"{'|N|':>4} {'n':>4} {'EXACT':>6} {'OVER':>5} {'UNDER':>6} {'MV':>4} "
          f"{'UNVER':>6} {'CUT':>4} {'wrong/verified':>15}")
    for k in sorted(set(r["abs_n"] for r in rows)):
        sub = [r for r in rows if r["abs_n"] == k]
        c = collections.Counter(r["class"] for r in sub)
        w = c.get("WRONG_OVERSTATED", 0) + c.get("WRONG_UNDERSTATED", 0) + c.get("MV_WRONG", 0)
        v = c.get("EXACT", 0) + w
        rate = f"{w}/{v} = {100*w/v:.0f}%" if v else f"{w}/0"
        print(f"{k:>4} {len(sub):>4} {c.get('EXACT',0):>6} {c.get('WRONG_OVERSTATED',0):>5} "
              f"{c.get('WRONG_UNDERSTATED',0):>6} {c.get('MV_WRONG',0):>4} "
              f"{c.get('UNVERIFIABLE',0):>6} {c.get('BUDGET_CUT',0):>4} {rate:>15}")

    print()
    print("-" * 78)
    print("DIRECTION OF EVERY ERROR")
    print("-" * 78)
    if over == 0 and under == 0 and mvwrong == 0:
        print("no errors observed")
    for r in rows:
        if r["class"] in ("WRONG_OVERSTATED", "WRONG_UNDERSTATED", "MV_WRONG"):
            delta = ""
            if r["class"] == "WRONG_OVERSTATED":
                delta = "claimed LONGER than true"
            elif r["class"] == "WRONG_UNDERSTATED":
                delta = "claimed SHORTER than reachable"
            else:
                delta = "distance plausible, MOVE wrong"
            print(f"  {r['id']}  claimed mate {r['score_value']:>3}  {r['class']:<17} {delta}")
            print(f"       seldepth={r.get('seldepth')} depth={r.get('depth')} "
                  f"nodes={r.get('nodes')} pv_len={r.get('pv_len')} "
                  f"(filter wants {2*abs(r['score_value'])-(1 if r['score_value']>0 else 0)}, "
                  f"pass={r.get('pv_len_filter_pass')})")
            print(f"       pv={' '.join((r.get('pv') or [])[:8])}")
            print(f"       fen={r['fen']}")

    print()
    print("-" * 78)
    print("PV-LENGTH FILTER: measured value against the wrong set")
    print("-" * 78)
    wrong_rows = [r for r in rows if r["class"] in
                  ("WRONG_OVERSTATED", "WRONG_UNDERSTATED", "MV_WRONG")]
    if wrong_rows:
        caught = [r for r in wrong_rows if r.get("pv_len_would_reject")]
        missed = [r for r in wrong_rows if not r.get("pv_len_would_reject")]
        print(f"wrong labels                     : {len(wrong_rows)}")
        print(f"  filter WOULD have caught       : {len(caught)} "
              f"({100*len(caught)/len(wrong_rows):.1f}%)")
        print(f"  filter would NOT have caught   : {len(missed)} "
              f"({100*len(missed)/len(wrong_rows):.1f}%)")
        print()
        print("  Of the missed (right-length, wrong mate) — the class S4 named:")
        for r in missed:
            print(f"    {r['id']} claimed {r['score_value']:>3} pv_len {r['pv_len']} "
                  f"wanted {r.get('pv_len_wanted')} seldepth {r.get('seldepth')}")
    else:
        print("no wrong labels to test the filter against")

    print()
    print("-" * 78)
    print("FILTER BEHAVIOUR ON THE WHOLE CORPUS (independent of wrongness)")
    print("-" * 78)
    passed = [r for r in rows if r.get("pv_len_filter_pass")]
    rejected = [r for r in rows if not r.get("pv_len_filter_pass")]
    print(f"labels passing the length filter : {len(passed)}/{n} "
          f"({100*len(passed)/max(n,1):.1f}%)")
    print(f"labels rejected by length filter : {len(rejected)}/{n}")
    if rejected:
        rr = [r for r in rejected if r["class"] in
              ("WRONG_OVERSTATED", "WRONG_UNDERSTATED", "MV_WRONG")]
        print(f"  of those rejected, actually wrong: {len(rr)}/{len(rejected)}")
    print(f"  of those PASSING, actually wrong : {len([r for r in passed if r['class'] in ('WRONG_OVERSTATED','WRONG_UNDERSTATED','MV_WRONG')])}/{len(passed)}")

    print()
    print("-" * 78)
    print("UNVERIFIABLE: what stopped each one")
    print("-" * 78)
    reasons = collections.Counter(r.get("reason", "?") for r in rows
                                  if r["class"] in ("UNVERIFIABLE", "BUDGET_CUT"))
    for reason, count in reasons.most_common():
        print(f"  {count:>3}  {reason}")

    # Machine-readable summary for the write-up.
    summary = {
        "labels_total": total_labels,
        "labels_with_verdict": n,
        "verified": verified, "exact": exact,
        "wrong_overstated": over, "wrong_understated": under, "mv_wrong": mvwrong,
        "unverifiable": unver, "budget_cut": cut,
        "wrong_rate_among_verified": (wrong / verified) if verified else None,
        "by_abs_n": {},
        "filter_would_catch": None,
        "filter_wrong_total": len(wrong_rows),
    }
    for k in sorted(set(r["abs_n"] for r in rows)):
        sub = [r for r in rows if r["abs_n"] == k]
        c = collections.Counter(r["class"] for r in sub)
        summary["by_abs_n"][k] = dict(c)
    if wrong_rows:
        summary["filter_would_catch"] = sum(1 for r in wrong_rows if r.get("pv_len_would_reject"))
    with open(paths.work_file("summary.json"), "w") as f:
        json.dump(summary, f, indent=1, default=str)
    print()
    print(f"wrote {paths.work_file('summary.json')}")


if __name__ == "__main__":
    main()
