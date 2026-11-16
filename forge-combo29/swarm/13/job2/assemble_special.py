#!/usr/bin/env python3
"""Assemble the job 2 500-position set from dense_hits.tsv.

Seven classes are kept, all found by filtering random games with python-chess:
  castling_transit_attacked, castling_rook_attacked, capture_promo_check, double_check,
  pinned_captures_pinner, ep_pseudo_but_illegal, ep_legal

`ep_legal` is added because `ep_pseudo_but_illegal` (the classically dangerous case: an en-passant
capture that would expose the king) is genuinely rare -- only 7 exist in 3,000 random games at
every ply. `ep_legal` is the matching control: en passant available and legal, so the engine must
generate it. Both are reported as separate classes; neither is merged or hidden.

Fill order: 80 from every class that has 80+, everything from the rare class, then round-robin.
Usage: assemble_special.py dense_hits.tsv OUT.fens OUT.tsv
"""
import sys

HITS, OUT_FENS, OUT_TSV = sys.argv[1], sys.argv[2], sys.argv[3]
CLASSES = ["castling_transit_attacked", "ep_pseudo_but_illegal", "ep_legal",
           "capture_promo_check", "double_check", "pinned_captures_pinner",
           "castling_rook_attacked"]
TARGET = 500
FLOOR = 80

by_class = {c: [] for c in CLASSES}
for line in open(HITS):
    if line.startswith("#") or not line.strip():
        continue
    cls, game, ply, fen, detail = line.rstrip("\n").split("\t")
    if cls in by_class:
        by_class[cls].append((fen, detail, int(game), int(ply)))

picked = []
shortfall = []
for c in CLASSES:
    rows = by_class[c]
    take = min(len(rows), FLOOR)
    picked.extend([(c, *r) for r in rows[:take]])
    if take < FLOOR:
        shortfall.append((c, len(rows)))

idx = {c: len([1 for p in picked if p[0] == c]) for c in CLASSES}
c_i = 0
while len(picked) < TARGET:
    c = CLASSES[c_i % len(CLASSES)]
    c_i += 1
    if idx[c] < len(by_class[c]):
        picked.append((c, *by_class[c][idx[c]]))
        idx[c] += 1
    if all(idx[x] >= len(by_class[x]) for x in CLASSES):
        break

with open(OUT_FENS, "w") as f:
    for c, fen, detail, g, p in picked:
        f.write(fen + "\n")
with open(OUT_TSV, "w") as f:
    f.write("# class\tfen\tdetail\tgame\tply\n")
    for c, fen, detail, g, p in picked:
        f.write("%s\t%s\t%s\t%d\t%d\n" % (c, fen, detail, g, p))

print("picked", len(picked))
for c in CLASSES:
    print(" ", c, len([1 for p in picked if p[0] == c]))
print("shortfall (class, found):", shortfall)
