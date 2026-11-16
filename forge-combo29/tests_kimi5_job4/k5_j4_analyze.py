#!/usr/bin/env python3
"""kimi5 job4 analysis: K checks, Part 3 counter shares, Part 4 factors with
position-bootstrap intervals (4000 resamples, seed 20261116, percentile 95%,
plus the two halves of the 200-position list). Prints one summary; writes nothing.
Usage: k5_j4_analyze.py   (run inside tests_kimi5_job4)"""
import json
import random

def load(tag):
    with open(f"k5_j4_{tag}.json") as f:
        return json.load(f)

def recs(tag):
    return load(tag)["records"]

def nodes(tag):
    return [r["nodes"] for r in recs(tag)]

def bests(tag):
    return [r.get("bestmove") for r in recs(tag)]

def cmp200(a, b):
    na, nb = nodes(a), nodes(b)
    ba, bb = bests(a), bests(b)
    neq = sum(1 for x, y in zip(na, nb) if x == y)
    beq = sum(1 for x, y in zip(ba, bb) if x == y)
    return neq, beq

def boot_ratio(on, off, resamples=4000, seed=20261116):
    rnd = random.Random(seed)
    n = len(on)
    ratios = []
    for _ in range(resamples):
        so = soff = 0
        for _ in range(n):
            i = rnd.randrange(n)
            so += on[i]
            soff += off[i]
        ratios.append(so / soff)
    ratios.sort()
    return sum(on) / sum(off), ratios[int(0.025 * resamples)], ratios[int(0.975 * resamples)]

def factor(cfg_tag, off_tag):
    on, off = nodes(cfg_tag), nodes(off_tag)
    r, lo, hi = boot_ratio(on, off)
    h1 = sum(on[:100]) / sum(off[:100])
    h2 = sum(on[100:]) / sum(off[100:])
    bdiff = sum(1 for x, y in zip(bests(cfg_tag), bests(off_tag)) if x != y)
    return r, lo, hi, h1, h2, bdiff, sum(on), sum(off)

print("== K checks (d12, 200 positions, nodes AND bestmove) ==")
n, b = cmp200("off_d12_fresh_base", "off_d12_fresh_tun")
print(f"K1 tun-off vs base-off: nodes {n}/200 bestmove {b}/200")
n, b = cmp200("on_d12_fresh_base", "on_d12_fresh_tun")
print(f"K2 tun-on-defaults vs base-on: nodes {n}/200 bestmove {b}/200")
n, b = cmp200("k3_d12_fresh_tun", "off_d12_fresh_base")
print(f"K3 tun-k3 vs base-off: nodes {n}/200 bestmove {b}/200")
for k in ["k4a", "k4b", "k4c", "k4d"]:
    nd = sum(1 for x, y in zip(nodes(f"{k}_d12_fresh_tun"), nodes("on_d12_fresh_tun")) if x != y)
    print(f"K4 {k} vs K2(on): positions with differing nodes: {nd} (need > 0)")
n, b = cmp200("on_d12_fresh_tun", "on_d12_fresh_ctr")
print(f"Part3 proof ctr-on vs tun-on (d12): nodes {n}/200 bestmove {b}/200")

print("\n== Part 4 factors vs OFF (tun build), bootstrap 4000 seed 20261116 ==")
for d in [16, 12]:
    off_tag = f"off_d{d}_fresh_tun"
    for cfg, label in [("on", "both"), ("shal", "shallower only"), ("deep", "deeper only"),
                       ("half", "half margins"), ("dbl", "double margins"), ("flat", "flat shallower")]:
        r, lo, hi, h1, h2, bdiff, so, soff = factor(f"{cfg}_d{d}_fresh_tun", off_tag)
        print(f"d{d} {label:16s} {r:.4f} [{lo:.4f}, {hi:.4f}] halves {h1:.3f}/{h2:.3f} "
              f"bestmove-diff {bdiff}/200 (nodes {so} vs {soff})")

print("\n== Part 3 counters (ctr build, switch on, sums over 200 positions) ==")
for d in [12, 16]:
    tot = {}
    for r in recs(f"on_d{d}_fresh_ctr"):
        for k, v in r.get("ctr", {}).items():
            tot[k] = tot.get(k, 0) + v
    cand = tot.get("cand", 0)
    cls_sum = sum(tot.get(k, 0) for k in ["unch", "s1", "s2", "s3"])
    print(f"d{d}: candidates {cand} (cls sum {cls_sum}), nodes {sum(nodes(f'on_d{d}_fresh_ctr'))}")
    if cand:
        for c in ["s1", "s2", "s3", "unch"]:
            print(f"  {c}: {tot.get(c, 0)} = {1000.0 * tot.get(c, 0) / cand:.1f} per 1000 candidates")
        for c in ["s1", "s2", "s3", "unch"]:
            row = f"  {c} splits: pv/cut/oth " + "/".join(str(tot.get(f"{c}_{t}", 0)) for t in ["pv", "cut", "oth"])
            row += " ; quiet/cap " + "/".join(str(tot.get(f"{c}_{t}", 0)) for t in ["quiet", "cap"])
            row += " ; nd13/nd47/nd8p " + "/".join(str(tot.get(f"{c}_{t}", 0)) for t in ["d13", "d47", "d8p"])
            print(row)
        print(f"  s1_faillow {tot.get('s1_faillow', 0)} of s1 {tot.get('s1', 0)}"
              f" ; mate_best {tot.get('mate_best', 0)} ; inf_best {tot.get('inf_best', 0)}")
print("\n== per-1000-NODE fire rates (context vs job 3) ==")
for d in [12, 16]:
    tot = {}
    nn = sum(nodes(f"on_d{d}_fresh_ctr"))
    for r in recs(f"on_d{d}_fresh_ctr"):
        for k, v in r.get("ctr", {}).items():
            tot[k] = tot.get(k, 0) + v
    print(f"d{d}: deeper {1000.0 * tot.get('s3', 0) / nn:.2f} shallower {1000.0 * (tot.get('s1', 0) + tot.get('s2', 0)) / nn:.2f}"
          f" cand {1000.0 * tot.get('cand', 0) / nn:.2f} per 1000 nodes")
