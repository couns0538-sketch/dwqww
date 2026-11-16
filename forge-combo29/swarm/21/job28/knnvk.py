#!/usr/bin/env python3
"""knnvk.py OUTDIR

CHECK of 15-F3 with my own 20 KNN v K positions, on three configurations:
  base + S14                      (DeadMaterial off — the claim's configuration)
  base + S14 + DeadMaterial true  (the claimed fix)
  PC + PC20                       (DeadMaterial is not set by PC20, so off)

Each position: a white king, a black king, and two white knights, placed at random with a
minimum king distance so no king is in check and neither side is stalemated. Verified with
python-chess: both kings present, exactly two knights, insufficient material, not mate/stalemate,
and there is at least one legal move.

Threads 1. `go depth 10`, read to bestmove (19-F12).
"""
import json
import os
import random
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, bestmove_of, last_info  # noqa: E402

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
SEED = 2101


def make_positions(n=20):
    rng = random.Random(SEED)
    out = []
    while len(out) < n:
        b = chess.Board(None)
        squares = list(chess.SQUARES)
        wk, bk = rng.sample(squares, 2)
        if chess.square_distance(wk, bk) < 3:
            continue
        rest = [s for s in squares if s not in (wk, bk)]
        n1, n2 = rng.sample(rest, 2)
        b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        b.set_piece_at(n1, chess.Piece(chess.KNIGHT, chess.WHITE))
        b.set_piece_at(n2, chess.Piece(chess.KNIGHT, chess.WHITE))
        b.turn = rng.choice([chess.WHITE, chess.BLACK])
        if b.is_check() or b.is_checkmate() or b.is_stalemate():
            continue
        if not b.is_insufficient_material():
            continue
        if b.legal_moves.count() == 0:
            continue
        out.append(b.fen())
    return out


def score_of(info):
    m = re.search(r"score (cp|mate) (-?\d+)", info)
    return (m.group(1), int(m.group(2))) if m else None


def run(exe, outdir, tag, fen, opts):
    e = SafeEngine(exe, os.path.join(outdir, tag + "_raw.txt"), hash_mb=16, threads=1)
    for n, v in opts:
        e.send("setoption name %s value %s" % (n, v))
        e.send("isready")
        e.wait_for("readyok")
    if opts:
        e.send("ucinewgame")
        e.send("isready")
        e.wait_for("readyok")
    e.position("position fen " + fen)
    lines = e.go("go depth 10", timeout=120)
    e.close()
    return bestmove_of(lines), score_of(last_info(lines)), last_info(lines)


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    fens = make_positions(20)
    with open(os.path.join(outdir, "knnvk.fens"), "w") as fh:
        fh.write("\n".join(fens) + "\n")
    base = os.path.expanduser("~/b/asan/forge")
    pc = os.path.expanduser("~/b/pc_asan/forge")
    configs = [("base_S14", base, S14),
               ("base_S14_deadmat", base, S14 + [("DeadMaterial", "true")]),
               ("pc_PC20", pc, S14 + PC20_EXTRA)]
    R = {}
    rows = ["| cfg | # | score | bestmove |", "|---|---|---|---|"]
    for cname, exe, opts in configs:
        for i, fen in enumerate(fens):
            tag = "%s_%02d" % (cname, i)
            bm, sc, info = run(exe, outdir, tag, fen, opts)
            R["%s|%d" % (cname, i)] = dict(score=sc, bestmove=bm, fen=fen)
            rows.append("| %s | %d | %s | %s |" % (cname, i, sc, bm))

    def vals(cname):
        return [R["%s|%d" % (cname, i)]["score"] for i in range(len(fens))]

    def cp_high(cname, thresh=100):
        return sum(1 for s in vals(cname) if s and s[0] == "cp" and s[1] > thresh)

    def all_zero(cname):
        return all(s == ("cp", 0) for s in vals(cname))

    q = {
        "P1 base+S14 scores >=15 of 20 above +100 cp": cp_high("base_S14") >= 15,
        "P2 base+S14+DeadMaterial true: all 20 exactly cp 0": all_zero("base_S14_deadmat"),
        "P3 PC+PC20 behaves like P1 (>=15 above +100)": cp_high("pc_PC20") >= 15,
    }
    text = "\n".join(rows)
    text += "\n\n| measure | base+S14 | base+S14+DeadMaterial | PC+PC20 |\n|---|---|---|---|\n"
    for label, fn in (("positions above +100 cp", cp_high),
                      ("positions exactly cp 0", lambda c: all_zero(c))):
        def count_zero(c):
            return sum(1 for s in vals(c) if s == ("cp", 0))
        text += "| %s | %s | %s | %s |\n" % (
            label,
            fn("base_S14") if fn is cp_high else count_zero("base_S14"),
            fn("base_S14_deadmat") if fn is cp_high else count_zero("base_S14_deadmat"),
            fn("pc_PC20") if fn is cp_high else count_zero("pc_PC20"))
    text += "\n| question | outcome |\n|---|---|\n"
    for k, v in q.items():
        text += "| %s | %s |\n" % (k, "yes" if v else "NO")
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text)
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(R, fh, indent=1)
    print(text[-1200:])


if __name__ == "__main__":
    main()