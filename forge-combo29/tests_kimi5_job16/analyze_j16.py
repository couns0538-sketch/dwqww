#!/usr/bin/env python3
"""kimi5 job 16 analysis, pure stdlib.
compare: python3 analyze_j16.py cmp A.json B.json  -> per-position nodes+bestmove equality
ratio:   python3 analyze_j16.py boot A.json B.json  -> bootstrap ratio of node sums B/A over positions
counters: python3 analyze_j16.py malc file_full.txt [more...] -> summed MALC fields + lines summed
"""
import json
import random
import sys


def load(path):
    with open(path) as f:
        return json.load(f)


def cmp(a, b):
    A, B = load(a), load(b)
    na, nb = A["per_position"], B["per_position"]
    ba, bb = A["bestmove"], B["bestmove"]
    assert len(na) == len(nb), (len(na), len(nb))
    diff_nodes = [i for i in range(len(na)) if na[i] != nb[i]]
    diff_bm = [i for i in range(len(na)) if ba[i] != bb[i]]
    print(f"{a} vs {b}: n={len(na)} sumA={sum(na)} sumB={sum(nb)} "
          f"nodes_diff={len(diff_nodes)} bm_diff={len(diff_bm)}")
    if diff_nodes:
        print("  first node diffs:", [(i, na[i], nb[i]) for i in diff_nodes[:8]])
    if diff_bm:
        print("  first bm diffs:", [(i, ba[i], bb[i]) for i in diff_bm[:8]])


def boot(a, b, resamples=2000, seed=2601):
    A, B = load(a), load(b)
    na, nb = A["per_position"], B["per_position"]
    assert len(na) == len(nb)
    n = len(na)
    rng = random.Random(seed)
    ratios = []
    for _ in range(resamples):
        idx = [rng.randrange(n) for _ in range(n)]
        sa = sum(na[i] for i in idx)
        sb = sum(nb[i] for i in idx)
        ratios.append(sb / sa)
    ratios.sort()
    lo = ratios[int(0.025 * resamples)]
    hi = ratios[int(0.975 * resamples)]
    diff_bm = sum(1 for i in range(n) if A["bestmove"][i] != B["bestmove"][i])
    print(f"{b} vs {a}: sumA={sum(na)} sumB={sum(nb)} ratio={sum(nb)/sum(na):.4f} "
          f"boot95=[{lo:.4f}, {hi:.4f}] bm_changed={diff_bm}/{n}")


def malc(paths):
    tot = {}
    lines = 0
    for p in paths:
        with open(p) as f:
            for line in f:
                if "MALC v1" not in line:
                    continue
                lines += 1
                parts = line.split()
                i = parts.index("MALC") + 2
                while i + 1 < len(parts):
                    key, val = parts[i], parts[i + 1]
                    tot[key] = tot.get(key, 0) + int(val)
                    i += 2
    print(f"MALC lines summed: {lines} over {len(paths)} file(s)")
    for k in sorted(tot):
        print(f"  {k} {tot[k]}")
    rf = tot.get("rf_d1_8", 0) + tot.get("rf_d9p", 0)
    res = tot.get("res_d1_8", 0) + tot.get("res_d9p", 0)
    bg = tot.get("bg_d1_8", 0) + tot.get("bg_d9p", 0)
    bwr = tot.get("bwr_d1_8", 0) + tot.get("bwr_d9p", 0)
    np_ = tot.get("np_d1_8", 0) + tot.get("np_d9p", 0)
    e1 = tot.get("e1_calls", 0)
    n4p = tot.get("e1_n4_7", 0) + tot.get("e1_n8_15", 0) + tot.get("e1_n16p", 0)
    print(f"  CHECK rf+bg+np == res: {rf}+{bg}+{np_} = {rf+bg+np_} vs res {res} -> {'OK' if rf+bg+np_ == res else 'MISMATCH'}")
    print(f"  fail share of researched: {rf}/{res} = {rf/res if res else 0:.4f}")
    print(f"  n>=4 share of e1 calls: {n4p}/{e1} = {n4p/e1 if e1 else 0:.4f}")
    print(f"  bonus_without_research total: {bwr}")


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "cmp":
        cmp(sys.argv[2], sys.argv[3])
    elif mode == "boot":
        boot(sys.argv[2], sys.argv[3])
    elif mode == "malc":
        malc(sys.argv[2:])
