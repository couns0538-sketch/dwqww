#!/usr/bin/env python3
"""drawn_root.py OUTDIR -- the one thing file 3 says genuinely differs between the base tree and the PC:
a drawn root (third occurrence, or halfmove counter >= 100) searches 0 nodes and plays its first legal
move on the base tree, while on the PC it is searched like any other root (only insufficient material is
still answered at once).

Design: build the SAME drawn position two ways, and check both builds on each, Threads 1.
  A  threefold by a real move list   (the position appears the third time)
  B  the same board via `position fen` with halfmove clock 100
  C  the same board via `position fen` with halfmove clock 0 (the CONTROL: not drawn, must be searched)
  D  K vs K (insufficient material; answered at once on BOTH builds per file 3)
  E  a SECOND occurrence only (file 3: `matches >= 2`, so a second one is searched normally) -- control
For each: nodes, bestmove, number of `info depth` lines, and whether the score looks like a real search.

The move list for A is a knight shuffle that returns to the same position three times:
   g1f3 g8f6 f3g1 f6g8  (2nd occurrence)  g1f3 g8f6 f3g1 f6g8  (3rd occurrence)
The root then has a repetition history the engine can see, unlike a bare FEN.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "audit"))
from drv import Drv

BASE = os.path.expanduser("~/builds/release/forge")
PC = os.path.expanduser("~/builds/pc/forge")
OUT = os.path.abspath(sys.argv[1])
os.makedirs(OUT, exist_ok=True)

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]

SHUF = "g1f3 g8f6 f3g1 f6g8"
CASES = {
    "A_third_occurrence": "position startpos moves " + " ".join([SHUF, SHUF]),
    "A2_second_occurrence": "position startpos moves " + SHUF,
    "B_fen_halfmove100": "position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 100 60",
    "C_fen_halfmove0_CONTROL": "position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "D_kvk_insufficient": "position fen 7k/8/8/8/8/8/8/7K w - - 0 1",
}


def one(exe, settings, poscmd, depth=10):
    d = Drv(exe)
    d.uci()
    d.isready()
    d.opt("Threads", "1")
    d.opt("Hash", "16")
    d.opt("OwnBook", "false")
    for k, v in settings:
        d.opt(k, v)
    d.isready()
    d.write("ucinewgame")
    d.isready()
    d.pos(poscmd)
    nodes, best, lines = d.go("go depth %d" % depth)
    d.quit()
    depth_lines = [l for l in lines if l.startswith("info depth")]
    return {"poscmd": poscmd, "depth": depth, "nodes": nodes, "bestmove": best,
            "info_depth_lines": len(depth_lines),
            "last_info": depth_lines[-1] if depth_lines else None,
            "searched": bool(depth_lines)}


out = {}
for label, poscmd in CASES.items():
    row = {}
    for bname, exe, settings in (("base_s14", BASE, S14), ("pc20", PC, S14 + [
            ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
            ("CorrHistV2", "true"), ("MateAlphaGuard", "true")])):
        try:
            row[bname] = one(exe, settings, poscmd)
        except Exception as e:                                  # noqa: BLE001
            row[bname] = {"error": "%s: %s" % (type(e).__name__, e)}
    out[label] = row
    with open(os.path.join(OUT, "drawn_root.json"), "w") as f:
        json.dump(out, f, indent=2)
        f.write("\n")
    b = row.get("base_s14", {})
    p = row.get("pc20", {})
    print("%-26s base nodes=%-8s searched=%-5s | pc nodes=%-8s searched=%-5s"
          % (label, b.get("nodes"), b.get("searched"), p.get("nodes"), p.get("searched")),
          flush=True)
print("done")
