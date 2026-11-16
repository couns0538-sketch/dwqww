#!/usr/bin/env python3
"""k14_tt.py -- Is the restricted-root hash entry a genuine DEFECT (a restricted search polluting
the table for LATER unrestricted searches) or intended behaviour (the root is searched differently
and its result is legitimately reusable)?

The brief's claim under test: "no hash entry is stored for a restricted root". I already showed a
repeat shrink (21,640 -> 17,847), so an entry IS reused by the NEXT restricted search. But that is
consistent with two very different things:

  H_DEFECT   the restricted search stores an entry that is WRONG for the unrestricted tree, so a
             LATER UNRESTRICTED search is corrupted by it (different nodes, possibly different move)
  H_INTENDED the restricted search's entry is correct for its own (restricted) tree and reuse is
             sound; an unrestricted search after it is unaffected

The discriminating experiment is CROSS-ORDER contamination:
  U1  unrestricted alone, fresh process                     -> nodes_U
  U2  restricted first, then unrestricted, ONE process      -> nodes_U_after_R
  U3  unrestricted, then unrestricted, ONE process          -> nodes_U_after_U   (control)
If H_DEFECT, nodes_U_after_R differs from nodes_U in a way nodes_U_after_U does not, and the
bestmove may change. If H_INTENDED, nodes_U_after_R == nodes_U_after_U and both are the expected
second-search value.

Also measured: does a restricted search change the SCORE of a later unrestricted search (a wrong
entry would), and does `ucinewgame` clear it (clearing behaviour tells us whose entry it is).

Usage: k14_tt.py OUTDIR
"""
import json
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drv import Drv

EXE = os.environ.get("FORGE_EXE", "/home/ubuntu/builds/release/forge")
OUT = os.path.abspath(sys.argv[1])
os.makedirs(OUT, exist_ok=True)
DEPTH = 12
ALL = " ".join(m.uci() for m in chess.Board().legal_moves)
RESTRICT = "go depth %d searchmoves %s" % (DEPTH, ALL)
UNRESTRICT = "go depth %d" % DEPTH


def score_of(lines):
    for l in reversed(lines):
        if l.startswith("info") and " score cp " in l:
            return int(l.split(" score cp ")[1].split()[0])
        if l.startswith("info") and " score mate " in l:
            return "mate " + l.split(" score mate ")[1].split()[0]
    return None


def session(tag, plan, newgame_between=False):
    """plan: list of 'R' or 'U'. Returns the per-search node/best/score list."""
    d = Drv(EXE)
    d.uci()
    d.isready()
    d.opt("OwnBook", "false")
    d.opt("Threads", "1")
    d.opt("Hash", "16")
    d.isready()
    d.write("ucinewgame")
    d.isready()
    d.pos("position startpos")
    rows = []
    for kind in plan:
        if newgame_between and rows:
            d.write("ucinewgame")
            d.isready()
            d.pos("position startpos")
        nodes, best, lines = d.go(RESTRICT if kind == "R" else UNRESTRICT)
        rows.append({"kind": kind, "nodes": nodes, "bestmove": best, "score": score_of(lines),
                     "pv_line": next((l for l in reversed(lines) if l.startswith("info depth")), None)})
    d.quit()
    with open(os.path.join(OUT, "k14_tt_%s.json" % tag), "w") as f:
        json.dump(rows, f, indent=2)
        f.write("\n")
    return rows


res = {}
res["U1_alone"] = session("U1", ["U"])
res["U3_U_then_U"] = session("U3", ["U", "U"])
res["U2_R_then_U"] = session("U2", ["R", "U"])
res["R_then_R"] = session("RR", ["R", "R"])
res["R_then_U_with_newgame"] = session("RnU", ["R", "U"], newgame_between=True)
res["U_then_R"] = session("UR", ["U", "R"])

u1 = res["U1_alone"][0]["nodes"]
u_after_u = res["U3_U_then_U"][1]["nodes"]
u_after_r = res["U2_R_then_U"][1]["nodes"]
u_after_r_newgame = res["R_then_U_with_newgame"][1]["nodes"]
r1 = res["R_then_R"][0]["nodes"]
r2 = res["R_then_R"][1]["nodes"]

summary = {
    "depth": DEPTH,
    "U1_unrestricted_alone": u1,
    "U3_second_unrestricted_after_unrestricted": u_after_u,
    "U2_unrestricted_after_restricted": u_after_r,
    "U_after_restricted_with_ucinewgame_between": u_after_r_newgame,
    "restricted_alone": r1,
    "restricted_repeat": r2,
    "restricted_repeat_shrinks": r2 < r1,
    "U2_vs_U3_same_nodes": u_after_r == u_after_u,
    "U2_equals_U1": u_after_r == u1,
    "bestmove_U_after_R_vs_U_after_U": [res["U2_R_then_U"][1]["bestmove"],
                                        res["U3_U_then_U"][1]["bestmove"]],
    "score_U_after_R_vs_U_after_U": [res["U2_R_then_U"][1]["score"],
                                     res["U3_U_then_U"][1]["score"]],
}
# verdict logic, stated before interpretation
if summary["U2_vs_U3_same_nodes"]:
    summary["verdict"] = ("INTENDED (not a defect): an unrestricted search after a restricted one behaves "
                          "EXACTLY like an unrestricted search after another unrestricted one, so the "
                          "restricted search does not corrupt the unrestricted tree")
else:
    summary["verdict"] = "DEFECT: the restricted search changed a later unrestricted search's tree"
with open(os.path.join(OUT, "k14_tt_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)
    f.write("\n")
print(json.dumps(summary, indent=2))
