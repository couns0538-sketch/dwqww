#!/usr/bin/env python3
"""deepseek6 long 32: the ratio table over the 22 runs, printed from the rows files.

Base for both halves is the DEFAULT build's rows (kimi5's base is defaults, not S14 — my
long-10 lesson), so a ratio here is "this setting against the plain engine at depth 12".
The SoundSteps half is measured on the Arms+Regret+Steps chain, whose own default is also
checked against the same plain rows (mask0's sum must equal the plain sum: its K1 check).

usage: table32.py
"""
import os

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs")


def load(tag):
    rows = []
    for line in open(os.path.join(R, tag + ".rows")):
        line = line.strip()
        if line:
            f = line.split("|")
            rows.append((int(f[1]), f[2]))
    return rows


def total(tag):
    return sum(n for n, _ in load(tag))


ARMS = [("A_defaults", "none (K1)"), ("A_smp", "SoundMatePruning true (K2)"),
        ("A_pv", "SoundPvArm 1 (K3)"), ("A_chk", "SoundInCheckArm 1 (K4)"),
        ("A_mat", "SoundMateAlphaArm 1 (K5)"), ("A_pvchk", "SoundPvArm 1 + SoundInCheckArm 1 (K6)"),
        ("A_off7", "smp + three arms -1 (K7)")]

MASKS = [("B_mask0", "SoundMatePruning + mask 0"), ("B_mask1", "SoundMatePruning + mask 1"),
         ("B_mask15", "SoundMatePruning + mask 15"), ("B_mask33", "SoundMatePruning + mask 33"),
         ("B_mask48", "SoundMatePruning + mask 48"), ("B_mask51", "SoundMatePruning + mask 51"),
         ("B_mask60", "SoundMatePruning + mask 60"), ("B_mask62", "SoundMatePruning + mask 62"),
         ("B_pvmask1", "SoundPvArm 1 + mask 1"), ("B_pvmask15", "SoundPvArm 1 + mask 15"),
         ("B_pvmask33", "SoundPvArm 1 + mask 33"), ("B_pvmask48", "SoundPvArm 1 + mask 48"),
         ("B_pvmask51", "SoundPvArm 1 + mask 51"), ("B_pvmask60", "SoundPvArm 1 + mask 60"),
         ("B_pvmask62", "SoundPvArm 1 + mask 62")]

base_rows = load("A_defaults")
base = sum(n for n, _ in base_rows)
print("base = the plain build's DEFAULT options, depth 12 on O, 200 positions: %d nodes" % base)
print("(standing known sum under S14 is 9,500,069; kimi5's base is defaults, whose O sum is %d)" % base)
print()

print("== SOUNDARMS (patch alone on the plain tree): %d settings" % len(ARMS))
print("| setting | O sum | ratio to default | nodes changed | best moves changed |")
print("|---|---|---|---|---|")
for tag, name in ARMS:
    rows = load(tag)
    s = sum(n for n, _ in rows)
    ch = sum(1 for a, b in zip(base_rows, rows) if a[0] != b[0])
    bm = sum(1 for a, b in zip(base_rows, rows) if a[1] != b[1])
    print("| %s | %d | %.4f | %d/200 | %d/200 |" % (name, s, s / base, ch, bm))

print()
print("== SOUNDSTEPS (Arms+Regret+Steps chain): %d settings" % len(MASKS))
print("| setting | O sum | ratio to default | nodes changed | best moves changed |")
print("|---|---|---|---|---|")
for tag, name in MASKS:
    rows = load(tag)
    s = sum(n for n, _ in rows)
    ch = sum(1 for a, b in zip(base_rows, rows) if a[0] != b[0])
    bm = sum(1 for a, b in zip(base_rows, rows) if a[1] != b[1])
    print("| %s | %d | %.4f | %d/200 | %d/200 |" % (name, s, s / base, ch, bm))

print()
print("== CHECKS")
smp = total("A_smp")
print("P7 mask0 == smp: %d vs %d -> %s   (mask0 vs the PLAIN default: %s)" % (total("B_mask0"), smp,
      "EQUAL" if load("B_mask0") == load("A_smp") else "DIFFERS",
      "EQUAL" if load("B_mask0") == base_rows else "DIFFERS"))
print("mask1 / smp = %.4f" % (total("B_mask1") / smp))
print("mask62 / smp = %.4f" % (total("B_mask62") / smp))
print("largest Arms tree: %d (%s)" % max((total(t), n) for t, n in ARMS))
print("smallest Arms tree: %d (%s)" % min((total(t), n) for t, n in ARMS))
