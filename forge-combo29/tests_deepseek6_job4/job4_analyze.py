#!/usr/bin/env python3
"""job4_analyze.py -- sum the lmrctr lines of each run and run the K1-K5 checks plus the
prediction measurements. Every table it prints starts with a header line."""
import math
import sys

J = "/tmp/ds6_work/forge-combo29/tests_deepseek6_job4"

def parse(path):
    q = [0]*8; n = [0]*8; ba = [0]*8; qt = [0]*8; bat = [0]*8
    bh = [[0]*8 for _ in range(14)]; bd = [[0]*8 for _ in range(15)]
    mm = 0; hs = []
    rows = 0
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        if not line.startswith("lmrctr "):
            print(f"{path}: BAD LINE {line[:50]}")
            sys.exit(3)
        rows += 1
        for part in line[7:].split(" "):
            if not part:
                continue
            k, _, v = part.partition("=")
            if k == "q":
                q = [a + b for a, b in zip(q, [int(x) for x in v.split(",")])]
            elif k == "n":
                n = [a + b for a, b in zip(n, [int(x) for x in v.split(",")])]
            elif k == "ba":
                ba = [a + b for a, b in zip(ba, [int(x) for x in v.split(",")])]
            elif k == "qt":
                qt = [a + b for a, b in zip(qt, [int(x) for x in v.split(",")])]
            elif k == "bat":
                bat = [a + b for a, b in zip(bat, [int(x) for x in v.split(",")])]
            elif k == "mm":
                mm += int(v)
            elif k == "bh":
                for b, cell in enumerate(v.split(";")):
                    bh[b] = [a + c for a, c in zip(bh[b], [int(x) for x in cell.lstrip("=").split(",")])]
            elif k == "bd":
                for d, cell in enumerate(v.split(";")):
                    bd[d] = [a + c for a, c in zip(bd[d], [int(x) for x in cell.lstrip("=").split(",")])]
            elif k == "hs_n":
                pass
            elif k == "hs":
                if v:
                    hs.extend(tuple(int(t) for t in p.split(":")) for p in v.split(","))
            else:
                print(f"{path}: unknown key {k!r}")
                sys.exit(3)
    return dict(rows=rows, q=q, n=n, ba=ba, qt=qt, bat=bat, bh=bh, bd=bd, mm=mm, hs=hs)

def slots_nonzero(arr):
    return {i - 3: c for i, c in enumerate(arr) if c}

runs = {}
for t in ("D0", "D1", "D2", "D3"):
    for s in ("O", "G"):
        runs[(t, s)] = parse(f"{J}/runs/{t}_{s}.lmrctr")

print("header: run | rows | q_sites by d(-3..3,other) | n_sites by d | mm")
for (t, s), r in runs.items():
    print(f"{t}_{s} rows={r['rows']} q={r['q']} n={r['n']} mm={r['mm']}")

print("\nheader: K1 (D1: every site d=0) -- q and n must have only slot d=0")
print("D1 O q-nonzero:", slots_nonzero(runs[("D1", "O")]["q"]), " n-nonzero:", slots_nonzero(runs[("D1", "O")]["n"]))
print("D1 G q-nonzero:", slots_nonzero(runs[("D1", "G")]["q"]), " n-nonzero:", slots_nonzero(runs[("D1", "G")]["n"]))

print("\nheader: K2 (every run: noisy sites d=0 only)")
for (t, s), r in runs.items():
    nz = slots_nonzero(r["n"])
    print(f"{t}_{s}: n-nonzero {nz} -> {'OK' if set(nz) <= {0} else 'FAIL'}")

print("\nheader: K5 (mismatch_used = 0 in every run)")
for (t, s), r in runs.items():
    print(f"{t}_{s}: mm={r['mm']} -> {'OK' if r['mm'] == 0 else 'FAIL'}")

print("\nheader: K3 (D2 = T1: observed d values per history bin, b = -6..5 plus two outer)")
names = {}
for idx in range(14):
    b = idx - 7
    label = "b<=-7" if b == -7 else ("b>=6" if b == 6 else f"b={b}")
    names[idx] = label
for idx in range(14):
    vals = {i - 3: c for i, c in enumerate(runs[("D2", "O")]["bh"][idx]) if c}
    total = sum(runs[("D2", "O")]["bh"][idx])
    if total:
        print(f"O {names[idx]}: total {total} d-values {vals}")

print("\nheader: K4 (D3 = T2: observed d values per history bin)")
for idx in range(14):
    vals = {i - 3: c for i, c in enumerate(runs[("D3", "O")]["bh"][idx]) if c}
    total = sum(runs[("D3", "O")]["bh"][idx])
    if total:
        print(f"O {names[idx]}: total {total} d-values {vals}")

print("\nheader: predictions")
r = runs[("D2", "O")]
tot_q = sum(r["q"])
dnz = sum(c for i, c in enumerate(r["q"]) if i != 3)
print(f"(a) D2 O quiet sites {tot_q}, d!=0 {dnz}, share {dnz/tot_q:.4f}")
m1 = r["q"][2]  # d=-1
p1 = r["q"][4]  # d=+1
print(f"(b) D2 O d=-1 {m1}, d=+1 {p1}, ratio {m1/max(p1,1):.2f}")
r0 = runs[("D0", "O")]
b_am1 = r0["bat"][2]; n_am1 = r0["qt"][2]
b_a0 = r0["bat"][3]; n_a0 = r0["qt"][3]
rate_m1 = b_am1 / max(n_am1, 1); rate_0 = b_a0 / max(n_a0, 1)
print(f"(c) D0 O would-be d=-1: {b_am1}/{n_am1} = {rate_m1:.4f}; d=0: {b_a0}/{n_a0} = {rate_0:.4f}; ratio {rate_m1/max(rate_0,1e-9):.2f}")

print("\nheader: the |history| >= 5643 recompute (D2 pairs; d_pred = floor((512-hterm)/1024) + trunc-clamp(history/5643))")
def trunc_div(a, b):
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q
def d_pred_t1(h):
    hterm = max(-2048, min(2048, trunc_div(h * 1024, 5643)))
    ci = max(-2, min(2, trunc_div(h, 5643)))
    return math.floor((512 - hterm) / 1024) + ci
bad = 0
for h, d in runs[("D2", "O")]["hs"]:
    if d_pred_t1(h) != d:
        bad += 1
print(f"D2 O pairs {len(runs[('D2','O')]['hs'])}, mismatches {bad}")
def d_pred_t2(h):
    hterm = max(-2048, min(2048, trunc_div(h * 1024, 5643)))
    ci = max(-2, min(2, trunc_div(h, 5643)))
    return math.floor((0 - hterm) / 1024) + ci
bad3 = 0
for h, d in runs[("D3", "O")]["hs"]:
    if d_pred_t2(h) != d:
        bad3 += 1
print(f"D3 O pairs {len(runs[('D3','O')]['hs'])}, mismatches {bad3}")
