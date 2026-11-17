"""Re-derive the headline counts from the per-run rows, ignoring the summary counters.

Every number in FINDINGS.md that a reader will quote is recomputed here straight
from `rows`, so a stale or mis-written summary field cannot survive. The summary
counters are computed in the same pass that writes the rows, which means a bug
could agree with itself; this pass cannot.
"""
import json
import os
import sys

EV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "evidence")


def pair_counts(name):
    with open(os.path.join(EV, name)) as f:
        d = json.load(f)
    n = ds = dd = db = dn = 0
    for r in d["rows"]:
        a, b = r["runs"]
        n += 1
        if (a["score_cp"], a["score_mate"]) != (b["score_cp"], b["score_mate"]):
            ds += 1
        if a["depth"] != b["depth"]:
            dd += 1
        if a["bestmove"] != b["bestmove"]:
            db += 1
        if a["nodes"] != b["nodes"]:
            dn += 1
    return n, ds, dd, db, dn


def main():
    ok = True
    for name, expect in [("m3_corpus_T1.json", (200, 0, 0, 0, 0)),
                         ("m3c_corpus_T1_hash1.json", (200, 0, 0, 0, 0)),
                         ("m3b_corpus_T4.json", (200, 189, 0, 58, 200))]:
        got = pair_counts(name)
        match = got == expect
        ok &= match
        print(f"{name:28} re-derived n/score/depth/bm/nodes={got} "
              f"expected={expect} {'MATCH' if match else 'MISMATCH'}")

    with open(os.path.join(EV, "m4_order.json")) as f:
        d = json.load(f)
    arm = d["arms"][1]
    any_d = sum(1 for r in arm["rows"] if r["fields_moved"])
    sc = sum(1 for r in arm["rows"] if "score" in r["fields_moved"])
    bm = sum(1 for r in arm["rows"] if "bestmove" in r["fields_moved"])
    match = (any_d, sc, bm) == (194, 194, 66)
    ok &= match
    print(f"{'m4_order.json A-vs-B':28} re-derived any/score/bm={(any_d, sc, bm)} "
          f"expected=(194, 194, 66) {'MATCH' if match else 'MISMATCH'}")

    with open(os.path.join(EV, "m4b_order_reset.json")) as f:
        d = json.load(f)
    ua = d["arms"][1]
    match = ua["diff_any"] == 0 and len(ua["diff_ids"]) == 0
    ok &= match
    print(f"{'m4b ucinewgame order-dep':28} diff_any={ua['diff_any']} "
          f"diff_ids={len(ua['diff_ids'])} {'MATCH' if match else 'MISMATCH'}")

    print("\nRE-DERIVATION", "ALL MATCH" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
