#!/usr/bin/env python3
"""deepseek6 long 43: the singular grid (SingularMargin x SingularDepth), ratios to S14.

Reads runs/O_m<margin>_d<depth>.rows (20 cells) and runs/G_m<margin>_d<depth>.rows (5 cells)
from long 43, prints the grid of ratios against the S14 cell (margin 2, depth 6), the two
marginal axes, the interaction check of prediction P5, and the corner orderings of P6/P7.

usage: grid43.py [runs dir]
"""
import os
import sys

R = sys.argv[1] if len(sys.argv) > 1 else "runs"
MARGINS = [0, 1, 2, 3, 4]
DEPTHS = [5, 6, 7, 8]
S14_CELL = (2, 6)
KNOWN_O_S14 = 9500069
KNOWN_G_S14 = 18466239


def total(setname, m, d):
    p = os.path.join(R, "%s_m%d_d%d.rows" % (setname, m, d))
    if not os.path.exists(p):
        return None
    n = 0
    rows = 0
    for line in open(p):
        line = line.strip()
        if line:
            n += int(line.split("|")[1])
            rows += 1
    return (rows, n)


def bestmoves(setname, m, d):
    p = os.path.join(R, "%s_m%d_d%d.rows" % (setname, m, d))
    return [l.strip().split("|")[2] for l in open(p) if l.strip()]


O = {}
for m in MARGINS:
    for d in DEPTHS:
        t = total("O", m, d)
        if t:
            O[(m, d)] = t

base = O[S14_CELL][1]
print("== PINS")
print("O S14 cell (margin 2, depth 6): %d rows %d nodes  -> %s (known %d)" % (
    O[S14_CELL][0], base, "EXACT" if base == KNOWN_O_S14 else "MISMATCH", KNOWN_O_S14))
gt = total("G", *S14_CELL)
print("G S14 cell: %d rows %d nodes  -> %s (known %d)" % (
    gt[0], gt[1], "EXACT" if gt[1] == KNOWN_G_S14 else "MISMATCH", KNOWN_G_S14))
Gbase = gt[1]

print()
print("== THE GRID: O node sums, ratio to S14 in brackets (rows = SingularMargin, cols = SingularDepth)")
print("| margin | depth 5 | depth 6 | depth 7 | depth 8 |")
print("|---|---|---|---|---|")
for m in MARGINS:
    cells = []
    for d in DEPTHS:
        t = O.get((m, d))
        cells.append("%d (%.4f)" % (t[1], t[1] / base) if t else "-")
    print("| %d | %s |" % (m, " | ".join(cells)))

print()
print("== MARGINAL: depth at fixed margin (ratio)")
print("| margin | d5 | d6 | d7 | d8 | d5/d8 span |")
print("|---|---|---|---|---|---|")
for m in MARGINS:
    r = [O[(m, d)][1] / base for d in DEPTHS]
    print("| %d | %.4f | %.4f | %.4f | %.4f | %.4f |" % (m, r[0], r[1], r[2], r[3], r[0] / r[3]))

print()
print("== MARGINAL: margin at fixed depth (ratio)")
print("| depth | m0 | m1 | m2 | m3 | m4 | m0/m4 span |")
print("|---|---|---|---|---|---|---|")
for d in DEPTHS:
    r = [O[(m, d)][1] / base for m in MARGINS]
    print("| %d | %.4f | %.4f | %.4f | %.4f | %.4f | %.4f |" % (d, r[0], r[1], r[2], r[3], r[4], r[0] / r[4]))

print()
print("== P5 INTERACTION: measured / product-of-singles, every cell")
print("   product(m,d) = ratio(m,6) * ratio(2,d) / ratio(2,6)")
print("| margin | depth | measured | product | mea/prod |")
print("|---|---|---|---|---|")
worst = 0.0
for m in MARGINS:
    for d in DEPTHS:
        if (m, d) == S14_CELL:
            continue
        measured = O[(m, d)][1] / base
        prod = (O[(m, 6)][1] / base) * (O[(2, d)][1] / base)
        ratio = measured / prod
        worst = max(worst, abs(ratio - 1))
        print("| %d | %d | %.4f | %.4f | %.4f |" % (m, d, measured, prod, ratio))
print("worst |mea/prod - 1| = %.4f  -> P5 (%s 5%%) %s" % (
    worst, "within" if worst <= 0.05 else "NOT within",
    "HELD" if worst <= 0.05 else "KILLED"))

print()
print("== P6: cheapest and most expensive cell of the grid")
cells = sorted(((O[k][1], k) for k in O))
print("cheapest: margin %d depth %d = %d (ratio %.4f)" % (cells[0][1][0], cells[0][1][1], cells[0][0], cells[0][0] / base))
print("dearest : margin %d depth %d = %d (ratio %.4f)" % (cells[-1][1][0], cells[-1][1][1], cells[-1][0], cells[-1][0] / base))

print()
print("== G CORNERS")
print("| cell | G sum | G ratio |")
print("|---|---|---|")
gc = {}
for m, d in [(0, 5), (0, 8), (4, 5), (4, 8), (2, 6)]:
    t = total("G", m, d)
    if t:
        gc[(m, d)] = t[1]
        print("| margin %d, depth %d | %d | %.4f |" % (m, d, t[1], t[1] / Gbase))

print()
print("== P6/P7 corner ordering check (O against G)")
corners = [(0, 5), (0, 8), (4, 5), (4, 8)]
o_order = sorted(corners, key=lambda k: O[k][1] / base)
g_order = sorted(corners, key=lambda k: gc.get(k, 0) / Gbase)
print("O corner order (cheapest first):", ["m%d_d%d" % k for k in o_order])
print("G corner order (cheapest first):", ["m%d_d%d" % k for k in g_order])
print("rank correlation 1.0:", o_order == g_order)

print()
print("== BEST MOVES CHANGED against the S14 cell, O (of 200)")
b0 = bestmoves("O", *S14_CELL)
for m in MARGINS:
    row = []
    for d in DEPTHS:
        b = bestmoves("O", m, d)
        row.append("%d" % sum(1 for x, y in zip(b0, b) if x != y))
    print("margin %d: %s" % (m, " ".join("%3s" % x for x in row)))
