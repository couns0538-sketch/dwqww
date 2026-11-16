#!/usr/bin/env python3
"""boundary.py OUTDIR

Two questions about 21-F19:
  A  size: 10 drawn roots with no mate, both builds, depth 10. Is the PC score consistently non-zero?
  B  boundary: at a drawn root, are mates in 1, 2 and 3 found on the PC build, and not on the base?

Mate-in-N boards are constructed and VERIFIED with python-chess (every candidate line checked; the
board's true mate distance comes from a small exact search). Every drawn board is ASSERTED to have
no mate in <= 3 before it is used, so the "drawn" premise cannot be false again (the job37 lesson).
"""
import json
import os
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

DRAWN = [
    "8/8/8/4k3/8/8/4P3/4K3 w - - 100 60",
    "8/8/8/3k4/8/8/3P4/3K4 w - - 100 60",
    "8/8/4k3/8/8/8/4P3/4K3 w - - 120 60",
    "8/8/8/4k3/8/8/5P2/5K2 w - - 100 60",
    "8/2k5/8/8/8/8/4P3/4K3 w - - 100 60",
    "8/8/8/8/4k3/8/4P3/4K3 w - - 100 60",
    "8/8/8/4k3/8/8/4P3/6K1 w - - 100 60",
    "8/8/3k4/8/8/8/3P4/6K1 w - - 100 60",
    "8/8/8/3k4/8/8/3P4/1K6 w - - 100 60",
    "8/8/8/5k2/8/8/5P2/5K2 w - - 100 60",
]


def mate_in(fen, maxd=3):
    """Exact smallest mate distance for the side to move, up to maxd plies; None if deeper."""
    b = chess.Board(fen)

    def rec(bd, depth):
        if bd.is_checkmate():
            return 0
        if depth == 0:
            return None
        best = None
        for m in bd.legal_moves:
            c = bd.copy()
            c.push(m)
            if c.is_checkmate():
                return 1
            if depth > 1:
                # opponent replies; the mate must hold against EVERY reply
                sub = []
                for r in c.legal_moves:
                    d = c.copy()
                    d.push(r)
                    v = rec(d, depth - 2)
                    sub.append(v)
                if sub and all(v is not None for v in sub):
                    cand = 1 + max(sub) + 1
                    if best is None or cand < best:
                        best = cand
        return best

    return rec(b, maxd)


def score(info):
    m = re.search(r"score (cp|mate) (-?\d+)", info)
    return (m.group(1), int(m.group(2))) if m else None


def run(exe, outdir, tag, fen, opts, go="go depth 10"):
    e = SafeEngine(exe, os.path.join(outdir, tag + "_raw.txt"), hash_mb=16, threads=1)
    for k, v in opts:
        e.send("setoption name %s value %s" % (k, v))
        e.send("isready")
        e.wait_for("readyok")
    if opts:
        e.send("ucinewgame")
        e.send("isready")
        e.wait_for("readyok")
    e.position("position fen " + fen)
    lines = e.go(go, timeout=180)
    e.close()
    info = last_info(lines)
    m = re.search(r" nodes (\d+)", info)
    return dict(bestmove=bestmove_of(lines), nodes=int(m.group(1)) if m else None,
                score=score(info), info=info)


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    base = os.path.expanduser("~/b/asan/forge")
    pc = os.path.expanduser("~/b/pc_asan/forge")

    # ---- A: size across 10 drawn roots (premise asserted)
    rows = ["| # | board | mate<=3? | base score | pc score |", "|---|---|---|---|---|"]
    sizes = []
    for i, fen in enumerate(DRAWN):
        assert mate_in(fen, 3) is None, "drawn board %d has a mate: %s" % (i, fen)
        rb = run(base, outdir, "A%d_base" % i, fen, [])
        rp = run(pc, outdir, "A%d_pc" % i, fen, S14 + PC20_EXTRA)
        if rp["score"] and rp["score"][0] == "cp":
            sizes.append(rp["score"][1])
        rows.append("| %d | `%s` | no | %s | %s |" % (i, fen, rb["score"], rp["score"]))

    # ---- B: the mate boundary at a drawn root
    mate_boards = {
        "mate1": "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 100 60",
        "mate2": "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 100 60",
        "mate3": "7k/8/6Q1/8/8/8/8/R5K1 w - - 100 60",
    }
    brows = ["| board | true mate len | base score | pc score | pc bestmove |",
             "|---|---|---|---|---|"]
    B = {}
    for name, fen in mate_boards.items():
        mi = mate_in(fen, 3)
        rb = run(base, outdir, "B_%s_base" % name, fen, [])
        rp = run(pc, outdir, "B_%s_pc" % name, fen, S14 + PC20_EXTRA)
        B[name] = dict(true=mi, base=rb, pc=rp, fen=fen)
        brows.append("| %s | %s | %s | %s | %s |" % (
            name, mi, rb["score"], rp["score"], rp["bestmove"]))

    text = "\n".join(rows) + "\n\nA) sizes on the PC build: %s\n" % sizes
    text += "mean %.0f cp, min %s, max %s\n\n" % (
        sum(sizes) / len(sizes) if sizes else 0, min(sizes) if sizes else "-",
        max(sizes) if sizes else "-")
    text += "\n".join(brows)
    text += "\n\nB) PC found mate: %s\n" % {
        k: (v["pc"]["score"] or ("?",))[0] == "mate" for k, v in B.items()}
    text += "B) base found mate: %s\n" % {
        k: (v["base"]["score"] or ("?",))[0] == "mate" for k, v in B.items()}
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text)
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(dict(A=DRAWN, B=B, sizes=sizes), fh, indent=1)
    print(text)


if __name__ == "__main__":
    main()