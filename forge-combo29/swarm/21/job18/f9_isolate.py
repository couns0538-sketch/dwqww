#!/usr/bin/env python3
"""f9_isolate.py OUTDIR

WHY does 21-F9 stop reproducing on the PC build? Two candidate causes, and they are separable:

  A  FORGE_FIX_ROOT_DRAWN (compile-time, default 1 in the PC patch): the drawn-root shortcut is
     gone, so a halfmove >= 100 root is searched like any other.
  B  the PC20 runtime options (CuckooRep/HistRework/TtPruneV2/CorrHistV2/MateAlphaGuard):
     an option could in principle change the root answer even under the old shortcut.

The test matrix, all Threads 1:
  PC build,   no setoption          (fix A ON,  options OFF)
  PC build,   PC20                  (fix A ON,  options ON)
  base build, no setoption          (fix A OFF, options OFF)
  base build, S14 only              (fix A OFF, options OFF, different search parameters)

If the mate is found in rows 1 AND 2 but missed in 3 and 4, cause A is established and B is not
needed. If row 1 misses and row 2 finds, cause B would be implicated instead.

Cases: the two mate-in-1 positions at halfmove 100 (White and Black) from job16.
"""
import json
import os
import subprocess
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

CASES = {
    "W_hm100": "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 100 60",
    "B_hm100": "r5k1/5ppp/8/8/8/8/5PPP/6K1 b - - 100 60",
    "W_hm99_control": "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 99 60",
}


def mates_in_one(fen):
    b = chess.Board(fen)
    out = []
    for m in list(b.legal_moves):
        c = b.copy()
        c.push(m)
        if c.is_checkmate():
            out.append(m.uci())
    return out


def run(exe, outdir, tag, fen, opts):
    e = SafeEngine(exe, os.path.join(outdir, tag + "_raw.txt"), hash_mb=16, threads=1)
    bad = []
    for n, v in opts:
        e.send("setoption name %s value %s" % (n, v))
        e.send("isready")
        bad += [l for l in e.wait_for("readyok")
                if any(b in l for b in ("unknown option", "invalid value", "ERROR"))]
    if opts:
        e.send("ucinewgame")
        e.send("isready")
        e.wait_for("readyok")
    e.position("position fen " + fen)
    lines = e.go("go depth 5")
    e.close()
    return bestmove_of(lines), last_info(lines), bad


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    configs = [
        ("pc_noopts", os.path.expanduser("~/b/pc_asan/forge"), []),
        ("pc_PC20", os.path.expanduser("~/b/pc_asan/forge"), S14 + PC20_EXTRA),
        ("base_noopts", os.path.expanduser("~/b/asan/forge"), []),
        ("base_S14", os.path.expanduser("~/b/asan/forge"), S14),
    ]
    R = {}
    rows = ["| config | case | mate | bestmove | nodes-carrying info |", "|---|---|---|---|---|"]
    for name, exe, opts in configs:
        for case, fen in CASES.items():
            bm, info, bad = run(exe, outdir, "%s_%s" % (name, case), fen, opts)
            mates = mates_in_one(fen)
            R["%s|%s" % (name, case)] = dict(bestmove=bm, info=info, mates=mates,
                                             found=bm in mates, bad=bad)
            rows.append("| %s | %s | %s | %s | %s |" % (
                name, case, ", ".join(mates), bm,
                ("FOUND" if bm in mates else "MISSED") + " " + info[-44:]))
    text = "\n".join(rows)
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text + "\n")
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(R, fh, indent=1)
    print(text)


if __name__ == "__main__":
    main()