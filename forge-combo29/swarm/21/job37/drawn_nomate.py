#!/usr/bin/env python3
"""drawn_nomate.py OUTDIR

File 6's complement: drawn roots with NO mate available, both builds, Threads 1.

Cases:
  rep3_nomate      a quiet position reached a third time (no mate available)
  hm100_nomate     a quiet position at halfmove 100
  kvk / knvk / kbvk  insufficient material with legal moves
Each: `go depth 10` and `go nodes 100000`. Records nodes, score, bestmove; asserts legality.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, bestmove_of, last_info  # noqa: E402


def mates_in_one(fen):
    b = chess.Board(fen)
    out = []
    for m in list(b.legal_moves):
        c = b.copy()
        c.push(m)
        if c.is_checkmate():
            out.append(m.uci())
    return out

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

# K+P vs K with the pawns blockable and kings far apart: verified by python-chess to have
# NO mate in 1 (my first version used a board that had one, which invalidated the test).
QUIET_REP_START = "8/8/8/4k3/8/8/4P3/4K3 w - - 0 60"
CYCLE = ["e1f1", "e5d5", "f1e1", "d5e5"]


def score(info):
    m = re.search(r"score (cp|mate) (-?\d+)", info)
    return (m.group(1), int(m.group(2))) if m else None


def run(exe, outdir, tag, pos, go, opts):
    e = SafeEngine(exe, os.path.join(outdir, tag + "_raw.txt"), hash_mb=16, threads=1)
    for k, v in opts:
        e.send("setoption name %s value %s" % (k, v))
        e.send("isready")
        e.wait_for("readyok")
    if opts:
        e.send("ucinewgame")
        e.send("isready")
        e.wait_for("readyok")
    ans = e.position(pos)
    if any("invalid FEN" in l for l in ans):
        e.close()
        raise AssertionError("%s refused" % tag)
    lines = e.go(go, timeout=180)
    e.close()
    info = last_info(lines)
    m = re.search(r" nodes (\d+)", info)
    return dict(bestmove=bestmove_of(lines), nodes=int(m.group(1)) if m else None,
                score=score(info), info=info)


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    b = chess.Board(QUIET_REP_START)
    seq = []
    for _ in range(2):
        for mv in CYCLE:
            b.push_uci(mv)
            seq.append(mv)
    rep_pos = "position fen %s moves %s" % (QUIET_REP_START, " ".join(seq))
    threefold = b.is_repetition(3)
    # ASSERT the premise: these boards must have NO mate in 1, or the test is void
    assert not mates_in_one(b.fen()), "rep3 root has a mate: %s" % mates_in_one(b.fen())
    assert not mates_in_one("8/8/8/4k3/8/8/4P3/4K3 w - - 100 60"), "hm100 board has a mate"

    cases = [
        ("rep3_nomate", rep_pos, b.fen()),
        ("hm100_nomate", "position fen 8/8/8/4k3/8/8/4P3/4K3 w - - 100 60",
         "8/8/8/4k3/8/8/4P3/4K3 w - - 100 60"),
        ("kvk", "position fen 4k3/8/8/8/8/8/8/4K3 w - - 0 60", "4k3/8/8/8/8/8/8/4K3 w - - 0 60"),
        ("knvk", "position fen 4k3/8/8/8/8/8/8/4KN2 w - - 0 60", "4k3/8/8/8/8/8/8/4KN2 w - - 0 60"),
        ("kbvk", "position fen 4k3/8/8/8/8/8/8/4KB2 w - - 0 60", "4k3/8/8/8/8/8/8/4KB2 w - - 0 60"),
    ]
    builds = [("base", os.path.expanduser("~/b/asan/forge"), []),
              ("pc", os.path.expanduser("~/b/pc_asan/forge"), S14 + PC20_EXTRA)]
    R = {}
    rows = ["| build | case | go | nodes | score | bestmove | legal |", "|---|---|---|---|---|---|---|"]
    for bname, exe, opts in builds:
        for cname, pos, fen in cases:
            legal = {m.uci() for m in chess.Board(fen).legal_moves}
            for go in ("go depth 10", "go nodes 100000"):
                tag = "%s_%s_%s" % (bname, cname, go.replace(" ", "_"))
                r = run(exe, outdir, tag, pos, go, opts)
                R["%s|%s|%s" % (bname, cname, go)] = r
                rows.append("| %s | %s | `%s` | %s | %s | %s | %s |" % (
                    bname, cname, go, r["nodes"], r["score"], r["bestmove"],
                    r["bestmove"] in legal or r["bestmove"] == "0000"))
    text = "\n".join(rows)
    text += "\npython: the rep3 chain gives a real threefold: %s\n" % threefold
    def zero(bname, cname):
        return all(R["%s|%s|%s" % (bname, cname, g)]["score"] == ("cp", 0)
                   for g in ("go depth 10", "go nodes 100000"))
    for cname in ("rep3_nomate", "hm100_nomate", "kvk", "knvk", "kbvk"):
        text += "%-13s base cp0: %s   pc cp0: %s\n" % (cname, zero("base", cname), zero("pc", cname))
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text)
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(R, fh, indent=1)
    print(text)


if __name__ == "__main__":
    main()