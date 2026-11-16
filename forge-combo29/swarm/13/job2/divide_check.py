#!/usr/bin/env python3
"""Divide check (perft 2, per root move) on the job 2 special set.

Two independent comparisons per position:
  1. MOVE SET + COUNTS: the engine's `go perft 2` divide (one line per root move) against
     python-chess's per-move subtree counts. Any missing move, extra move or different count is a
     difference. This is sharp where an equal TOTAL could hide two compensating errors.
  2. CLASS PROPERTY: classes.py is re-run on the FEN and must still report the class, and the
     class's characteristic move must be present (or absent, for the illegal-ep class) in the
     engine's move set. This stops "0 differences" from being an empty-class artefact.

classes.py is the single definition of every class, so this file cannot drift from the set builder.

Usage: divide_check.py EXE FENS TSV OUTDIR
"""
import os
import re
import subprocess
import sys

import chess

import classes

EXE, FENS, TSV, OUTDIR = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
os.makedirs(OUTDIR, exist_ok=True)
DEPTH = 2


def perft(board, d):
    if d == 0:
        return 1
    n = 0
    for m in board.legal_moves:
        board.push(m)
        n += perft(board, d - 1)
        board.pop()
    return n


def py_divide(board):
    out = {}
    for m in board.legal_moves:
        board.push(m)
        out[m.uci()] = perft(board, DEPTH - 1)
        board.pop()
    return out


rows = []
for line in open(TSV):
    if line.startswith("#") or not line.strip():
        continue
    cls, fen, facts, game, ply = line.rstrip("\n").split("\t")
    rows.append((cls, fen))

fens = [r[1] for r in rows]
proc = subprocess.run(
    [EXE],
    input="".join("position fen %s\ngo perft %d\n" % (f, DEPTH) for f in fens) + "quit\n",
    text=True, capture_output=True, timeout=1800)
blocks = []
cur = None
for ln in proc.stdout.splitlines():
    m = re.match(r"^([a-h][1-8][a-h][1-8][qrbn]?): (\d+)$", ln)
    if m:
        if cur is None:
            cur = {}
        cur[m.group(1)] = int(m.group(2))
        continue
    if ln.startswith("nodes "):
        blocks.append(cur if cur is not None else {})
        cur = None

rep = []
rep.append("# divide check, perft %d, engine vs python-chess, %d positions" % (DEPTH, len(fens)))
rep.append("")
rep.append("engine produced %d divide blocks for %d positions" % (len(blocks), len(fens)))
rep.append("")

bad = []
prop_fail = []
for i, (cls, fen) in enumerate(rows):
    b = chess.Board(fen)
    ref = py_divide(b)
    eng = blocks[i] if i < len(blocks) else {}
    missing = sorted(set(ref) - set(eng))
    extra = sorted(set(eng) - set(ref))
    wrong = sorted(m for m in set(ref) & set(eng) if ref[m] != eng[m])
    if missing or extra or wrong:
        bad.append((i, cls, fen, missing, extra, wrong))

    # class property, recomputed from the FEN with the shared definitions
    still = classes.CLASSES[cls](b)
    ok = bool(still)
    note = "class still reports %s" % (bool(still))
    if ok:
        f = still[0]
        if cls == "ep_pseudo_but_illegal":
            illegal_move = f.split("_")[-1]
            ok = illegal_move not in eng
            note += "; illegal ep %s absent from engine moves: %s" % (illegal_move, illegal_move not in eng)
        elif cls == "ep_legal":
            mv = f.split("_")[-1]
            ok = mv in eng and mv in ref
            note += "; ep %s present both sides: %s" % (mv, mv in eng and mv in ref)
        elif cls in ("capture_promo_check", "pinned_captures_pinner"):
            mv = f.split("_")[-1]
            ok = mv in eng and mv in ref
            note += "; move %s present both sides: %s" % (mv, mv in eng and mv in ref)
        elif cls in ("castle_transit_attacked", "castle_rook_path_attacked"):
            if cls == "castle_transit_attacked":
                # only the castling whose transit square is attacked must be absent; the other
                # side's castling may legitimately be legal and present
                attacked = f.split("_")[1]
                bad_side = "e1g1" if attacked == "f1" else ("e1c1" if attacked == "d1" else
                                                             "e8g8" if attacked == "f8" else "e8c8")
                ok = bad_side not in eng
                note += "; castling over attacked transit %s absent from engine moves: %s" % (
                    bad_side, bad_side not in eng)
            else:
                mv = f.split("_")[-1]
                ok = mv in eng and mv in ref
                note += "; castling %s present both sides: %s" % (mv, mv in eng and mv in ref)
        elif cls == "double_check":
            ok = True
    if not ok:
        prop_fail.append((i, cls, fen, note))

rep.append("## move-set comparison")
rep.append("positions differing in root move set or counts: **%d of %d**" % (len(bad), len(fens)))
for i, cls, fen, missing, extra, wrong in bad:
    rep.append("")
    rep.append("### position %d, class %s" % (i, cls))
    rep.append("FEN `%s`" % fen)
    if missing:
        rep.append("- engine MISSING: %s" % ", ".join(missing))
    if extra:
        rep.append("- engine EXTRA: %s" % ", ".join(extra))
    if wrong:
        rep.append("- counts differ: %s" % ", ".join(
            "%s engine %d python %d" % (m, eng[m], ref[m]) for m in wrong))
rep.append("")
rep.append("## class properties")
rep.append("class-property assertions failed: **%d of %d**" % (len(prop_fail), len(fens)))
for i, cls, fen, note in prop_fail[:20]:
    rep.append("- position %d (%s) FEN `%s`: %s" % (i, cls, fen, note))
rep.append("")
counts = {}
for cls, fen in rows:
    counts[cls] = counts.get(cls, 0) + 1
rep.append("## positions per class")
for c in classes.ORDER:
    rep.append("- %s: %d" % (c, counts.get(c, 0)))

text = "\n".join(rep)
open(os.path.join(OUTDIR, "VERDICT.md"), "w").write(text)
print("\n".join(rep[:6]))
print("...")
print("differing:", len(bad), "property failures:", len(prop_fail))
