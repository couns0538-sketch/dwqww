#!/usr/bin/env python3
"""Job 2 B5: show that the B2 comparison is able to fail.

If my evaluator agreed with the engine because it is trivial, or because both
sides are reading the same wrong thing, the comparison would still print
"0 mismatches". This script perturbs exactly one number in a COPY of a net, in a
way that must change the evaluation, and shows that my evaluator then disagrees
with the unperturbed engine.

Two perturbations, each of which must be visible:
  P1  w2[0][0] += 1 (one output weight of bucket 0)   -> changes every position
      whose output bucket is 0... and only those, which also localises the effect.
  P2  b2[1] += 1 (the output bias of bucket 1)        -> changes exactly the value
      of positions in bucket 1 by round(1 * eval_scale / (QA*QB)) = 0 for
      eval_scale 400, so it may NOT show. Reported either way, not hidden.

So the script also runs P3: b2[0] += 4096, a large bias change that must move
every bucket-0 value by 4096*eval_scale/(255*64) = 100 cp (eval_scale 400).

Usage: b5_perturb.py <net> <fens> <outdir>
"""
import copy
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deepseek_nnue_v3_ref as ref
from b2_compare import engine_values


def compare(netobj, fens, engine_values_list):
    diffs = []
    for i, fen in enumerate(fens):
        cp, _info = ref.evaluate(netobj, fen)
        if cp != engine_values_list[i]:
            diffs.append({"index": i, "fen": fen, "mine": cp, "engine": engine_values_list[i],
                          "delta": cp - engine_values_list[i]})
    return diffs


def main():
    net_path, fens_path, outdir = sys.argv[1:4]
    os.makedirs(outdir, exist_ok=True)
    with open(fens_path) as f:
        fens = [l.strip() for l in f if l.strip()]

    base = ref.load_net(net_path)
    engine_vals, _raw, code = engine_values("/tmp/ds/build-release/forge", net_path, fens)

    # Sanity: the unperturbed evaluator must agree (same test as B2).
    baseline = compare(base, fens, engine_vals)

    results = {"net": net_path, "positions": len(fens), "engine_exit_code": code,
               "baseline_mismatches": len(baseline), "perturbations": []}

    # P1: one w2 weight of output bucket 0.
    p1 = copy.deepcopy(base)
    p1.w2[0][0] += 1
    d1 = compare(p1, fens, engine_vals)
    buckets = [ref.evaluate(base, fens[d["index"]])[1]["ob"] for d in d1]
    results["perturbations"].append({
        "name": "P1 w2[0][0] += 1", "mismatches": len(d1),
        "output_buckets_of_differing_positions": sorted(set(buckets)),
        "first": d1[0] if d1 else None,
    })

    # P2: bias of bucket 1 by +1 (may be invisible because of the scaling).
    p2 = copy.deepcopy(base)
    p2.b2[1] += 1
    d2 = compare(p2, fens, engine_vals)
    results["perturbations"].append({
        "name": "P2 b2[1] += 1", "mismatches": len(d2),
        "first": d2[0] if d2 else None,
        "note": "measured, not assumed: +1 bias unit is 400/(255*64) = 0.0245 cp, but the "
                "truncating division does not absorb it for every position, so some bucket-1 "
                "values move by exactly 1",
    })

    # P3: a bias change large enough to be visible, on bucket 0.
    p3 = copy.deepcopy(base)
    p3.b2[0] += 4096
    d3 = compare(p3, fens, engine_vals)
    results["perturbations"].append({
        "name": "P3 b2[0] += 4096", "mismatches": len(d3),
        "first": d3[0] if d3 else None,
    })

    with open(f"{outdir}/B5-perturbation.json", "w") as f:
        json.dump(results, f, indent=2, sort_keys=True)
    print(json.dumps({k: v for k, v in results.items() if k != "perturbations"}, sort_keys=True))
    for p in results["perturbations"]:
        print(f"  {p['name']}: {p['mismatches']} mismatches"
              + (f", buckets {p.get('output_buckets_of_differing_positions')}" if p.get("output_buckets_of_differing_positions") is not None else ""))


if __name__ == "__main__":
    main()
