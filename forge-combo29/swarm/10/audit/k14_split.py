#!/usr/bin/env python3
"""k14_split.py -- Is the restricted-root unsoundness the SAME cause as the table contamination,
or a SEPARATE defect?

The question, as posed: run restricted with `Clear Hash` in a fresh process, then restricted again.
  - if the restricted score stays cp 23 while the cold unrestricted is cp 30, the restricted root
    computes wrongly ON ITS OWN, and the contamination is a second defect;
  - if the restricted score becomes cp 30, there is ONE defect and it is the table write.

Additions that make the answer sharper (each is a fresh process unless said otherwise):
  A  cold unrestricted                          -> baseline nodes/score/move
  B  cold restricted to all 20                  -> is it already wrong with nothing in the table?
  C  Clear Hash, restricted, restricted again    -> does Clear Hash rescue the score?
  D  restricted to ONLY the unrestricted bestmove (e2e4) -> is that move scored correctly at the root?
  E  restricted to {e2e4, d2d4}                  -> does adding d2d4 change e2e4's score?
  F  unrestricted, then Clear Hash, then restricted (same process) -> is the wrong score still there
     when the table is empty in a WARM process?
  G  MultiPV 3 unrestricted (what does the engine itself think of the top moves?)

Every search records nodes, the last `info ... score`, and bestmove. Nothing is inferred from a missing
line: a search with no score line is reported as `score None`.

Usage: k14_split.py OUTDIR
"""
import json
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drv import Drv

EXE = os.environ.get("FORGE_EXE", "/home/ubuntu/builds/release/forge")
OUT = os.path.abspath(sys.argv[1])
os.makedirs(os.path.join(OUT, "K14split"), exist_ok=True)
DEPTH = 12
ALL = " ".join(m.uci() for m in chess.Board().legal_moves)


def score_of(lines):
    for l in reversed(lines):
        if l.startswith("info") and " score cp " in l:
            return int(l.split(" score cp ")[1].split()[0])
        if l.startswith("info") and " score mate " in l:
            return "mate " + l.split(" score mate ")[1].split()[0]
    return None


def fresh(plan, multipv=None):
    """plan: list of ('go', cmdstr) or ('clear', None). One process, results per go."""
    d = Drv(EXE)
    d.uci()
    d.isready()
    d.opt("OwnBook", "false")
    d.opt("Threads", "1")
    d.opt("Hash", "16")
    if multipv:
        d.opt("MultiPV", str(multipv))
    d.isready()
    d.write("ucinewgame")
    d.isready()
    d.pos("position startpos")
    rows = []
    for kind, cmd in plan:
        if kind == "clear":
            d.write("setoption name Clear Hash")
            d.isready()
            rows.append({"kind": "clear"})
        else:
            nodes, best, lines = d.go(cmd)
            rows.append({"kind": "go", "cmd": cmd, "nodes": nodes, "bestmove": best,
                         "score": score_of(lines),
                         "last_info": next((l for l in reversed(lines)
                                            if l.startswith("info depth")), None)})
    d.quit()
    return rows


R = "go depth %d searchmoves %s" % (DEPTH, ALL)
U = "go depth %d" % DEPTH

res = {}
res["A_cold_unrestricted"] = fresh([("go", U)])
res["B_cold_restricted"] = fresh([("go", R)])
res["C_clear_then_R_then_R"] = fresh([("clear", None), ("go", R), ("go", R)])
res["D_restricted_only_e2e4"] = fresh([("go", "go depth %d searchmoves e2e4" % DEPTH)])
res["E_restricted_e2e4_d2d4"] = fresh([("go", "go depth %d searchmoves e2e4 d2d4" % DEPTH)])
res["F_warm_clear_restricted"] = fresh([("go", U), ("clear", None), ("go", R)])
res["G_multipv3_unrestricted"] = fresh([("go", U)], multipv=3)

with open(os.path.join(OUT, "K14split", "all.json"), "w") as f:
    json.dump(res, f, indent=2)
    f.write("\n")


def pick(key, idx=0):
    gos = [r for r in res[key] if r.get("kind") == "go"]
    return gos[idx]


summary = {
    "A_cold_unrestricted": {k: pick("A_cold_unrestricted")[k] for k in ("nodes", "score", "bestmove")},
    "B_cold_restricted_ALL20": {k: pick("B_cold_restricted")[k] for k in ("nodes", "score", "bestmove")},
    "C_restricted_after_ClearHash": {k: pick("C_clear_then_R_then_R", 0)[k] for k in ("nodes", "score", "bestmove")},
    "C_restricted_again": {k: pick("C_clear_then_R_then_R", 1)[k] for k in ("nodes", "score", "bestmove")},
    "D_restricted_only_e2e4": {k: pick("D_restricted_only_e2e4")[k] for k in ("nodes", "score", "bestmove")},
    "E_restricted_e2e4_d2d4": {k: pick("E_restricted_e2e4_d2d4")[k] for k in ("nodes", "score", "bestmove")},
    "F_unrestricted_then_clear_then_restricted": {k: pick("F_warm_clear_restricted", 1)[k]
                                                  for k in ("nodes", "score", "bestmove")},
    "G_multipv3": [{"nodes": r["nodes"], "score": r["score"], "bestmove": r["bestmove"]}
                   for r in res["G_multipv3_unrestricted"] if r.get("kind") == "go"],
}
u = summary["A_cold_unrestricted"]["score"]
b = summary["B_cold_restricted_ALL20"]["score"]
c = summary["C_restricted_after_ClearHash"]["score"]
summary["restricted_wrong_when_COLD_and_table_empty"] = (b is not None and u is not None and b != u)
summary["clear_hash_does_NOT_rescue_it"] = (c is not None and u is not None and c != u)
if summary["restricted_wrong_when_COLD_and_table_empty"] and summary["clear_hash_does_NOT_rescue_it"]:
    summary["answer"] = ("TWO SEPARATE DEFECTS. The restricted root is already wrong in a cold process with "
                         "an empty table (score %s vs the cold unrestricted %s), and Clear Hash does not "
                         "rescue it (score %s). Table contamination is therefore a SECOND, independent "
                         "defect." % (b, u, c))
elif summary["restricted_wrong_when_COLD_and_table_empty"]:
    summary["answer"] = "ONE defect: the restricted root computes wrongly on its own; contamination follows from it"
else:
    summary["answer"] = "ONE defect: the table write (Clear Hash rescued the score)"
with open(os.path.join(OUT, "K14split", "summary.json"), "w") as f:
    json.dump(summary, f, indent=2)
    f.write("\n")
print(json.dumps(summary, indent=2))
