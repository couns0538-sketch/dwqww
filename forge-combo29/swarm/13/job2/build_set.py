#!/usr/bin/env python3
"""Rebuild the 500-position special set using classes.py, from a dense-pool hit file.

Each hit line's FEN is RE-CLASSIFIED with classes.py; a hit whose FEN no longer belongs to any
class is dropped and counted. The FENs written out are the class function's own view of the board,
so the set cannot drift from the definitions.

Usage: build_set.py dense_hits.tsv OUT.fens OUT.tsv TARGET FLOOR
"""
import sys

import chess

import classes

HITS, OUT_FENS, OUT_TSV, TARGET, FLOOR = (sys.argv[1], sys.argv[2], sys.argv[3],
                                          int(sys.argv[4]), int(sys.argv[5]))

rows = []
dropped = 0
for line in open(HITS):
    if line.startswith("#") or not line.strip():
        continue
    _cls, game, ply, fen, _detail = line.rstrip("\n").split("\t")
    try:
        b = chess.Board(fen)
    except ValueError:
        dropped += 1
        continue
    found = None
    for name in classes.ORDER:
        facts = classes.CLASSES[name](b)
        if facts:
            found = (name, facts)
            break
    if not found:
        dropped += 1
        continue
    rows.append((found[0], b.fen(en_passant="fen"), found[1], int(game), int(ply)))

by_class = {c: [] for c in classes.ORDER}
for r in rows:
    by_class[r[0]].append(r)

picked = []
for c in classes.ORDER:
    picked.extend(by_class[c][:FLOOR])
idx = {c: len(by_class[c][:FLOOR]) for c in classes.ORDER}
k = 0
while len(picked) < TARGET and k < 100000:
    c = classes.ORDER[k % len(classes.ORDER)]
    k += 1
    if idx[c] < len(by_class[c]):
        picked.append(by_class[c][idx[c]])
        idx[c] += 1
    elif all(idx[x] >= len(by_class[x]) for x in classes.ORDER):
        break

seen = set()
final = []
for r in picked:
    if r[1] in seen:
        continue
    seen.add(r[1])
    final.append(r)

with open(OUT_FENS, "w") as f:
    for r in final:
        f.write(r[1] + "\n")
with open(OUT_TSV, "w") as f:
    f.write("# class\tfen\tfacts\tgame\tply\n")
    for cls, fen, facts, g, p in final:
        f.write("%s\t%s\t%s\t%d\t%d\n" % (cls, fen, ",".join(facts), g, p))

print("hits reclassified %d, dropped %d, set size %d" % (len(rows), dropped, len(final)))
for c in classes.ORDER:
    print(" ", c, sum(1 for r in final if r[0] == c))
