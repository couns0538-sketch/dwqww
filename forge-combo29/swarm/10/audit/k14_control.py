#!/usr/bin/env python3
"""k14_control.py -- THE control for 10-F20: does a REPEATED IDENTICAL unrestricted search in one
process give the same measurement as the first one?

If two unrestricted searches with NOTHING between them differ, then 10-F20 is not about searchmoves
at all: it is about process/search state, and every "second search" number in the swarm is suspect.

Design (each line is one fresh process):
  U2    unrestricted, unrestricted                      -> are the two equal?
  U3    unrestricted x3                                  -> does it settle after the first?
  U2C   unrestricted, Clear Hash, unrestricted            -> does Clear Hash make them equal?
  U2N   unrestricted, ucinewgame, unrestricted            -> does ucinewgame make them equal?
  U2P   unrestricted, position startpos again, unrestricted-> does re-sending the position make them equal?
  R2    restricted(all 20), restricted(all 20)            -> the restricted analogue
  U1_rep  unrestricted alone, three separate processes    -> the cross-PROCESS repeatability baseline

The same depth/options throughout: depth 12, Threads 1, Hash 16, OwnBook false, ucinewgame+position
BEFORE the first search only (the brief's order), one `go` at a time, reading to bestmove.

Usage: k14_control.py OUTDIR
"""
import json
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drv import Drv

EXE = os.environ.get("FORGE_EXE", "/home/ubuntu/builds/release/forge")
OUT = os.path.abspath(sys.argv[1])
os.makedirs(os.path.join(OUT, "K14control"), exist_ok=True)
DEPTH = 12
ALL = " ".join(m.uci() for m in chess.Board().legal_moves)
U = "go depth %d" % DEPTH
R = "go depth %d searchmoves %s" % (DEPTH, ALL)


def score_of(lines):
    for l in reversed(lines):
        if l.startswith("info") and " score cp " in l:
            return int(l.split(" score cp ")[1].split()[0])
        if l.startswith("info") and " score mate " in l:
            return "mate " + l.split(" score mate ")[1].split()[0]
    return None


def session(plan, tag):
    """plan entries: 'U' / 'R' searches, 'C' Clear Hash, 'N' ucinewgame, 'P' re-send position."""
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
    for step in plan:
        if step == "C":
            d.write("setoption name Clear Hash")
            d.isready()
            rows.append({"step": "ClearHash"})
        elif step == "N":
            d.write("ucinewgame")
            d.isready()
            rows.append({"step": "ucinewgame"})
        elif step == "P":
            d.pos("position startpos")
            rows.append({"step": "position startpos"})
        else:
            nodes, best, lines = d.go(U if step == "U" else R)
            rows.append({"step": "go", "kind": step, "nodes": nodes, "bestmove": best,
                         "score": score_of(lines)})
    d.quit()
    with open(os.path.join(OUT, "K14control", tag + ".json"), "w") as f:
        json.dump(rows, f, indent=2)
        f.write("\n")
    return rows


def gos(rows):
    return [r for r in rows if r.get("step") == "go"]


res = {}
res["U2"] = session(["U", "U"], "U2")
res["U3"] = session(["U", "U", "U"], "U3")
res["U2C"] = session(["U", "C", "U"], "U2C")
res["U2N"] = session(["U", "N", "U"], "U2N")
res["U2P"] = session(["U", "P", "U"], "U2P")
res["R2"] = session(["R", "R"], "R2")
res["U1_rep"] = session(["U"], "U1_rep0") + session(["U"], "U1_rep1") + session(["U"], "U1_rep2")


def summ(tag):
    g = gos(res[tag])
    return [{"nodes": r["nodes"], "score": r["score"], "bestmove": r["bestmove"]} for r in g]


out = {k: summ(k) for k in res}
u2 = summ("U2")
u2n = summ("U2N")
u2c = summ("U2C")
u2p = summ("U2P")
r2 = summ("R2")
u3 = summ("U3")
u1rep = summ("U1_rep")

summary = {
    "U2_unrestricted_twice": u2,
    "U3_unrestricted_thrice": u3,
    "U2C_unrestricted_clearhash_unrestricted": u2c,
    "U2N_unrestricted_ucinewgame_unrestricted": u2n,
    "U2P_unrestricted_position_again_unrestricted": u2p,
    "R2_restricted_twice": r2,
    "U1_alone_three_processes": u1rep,
    "two_identical_unrestricted_searches_DIFFER": u2[0]["nodes"] != u2[1]["nodes"],
    "difference_1st_to_2nd": (u2[0]["nodes"] - u2[1]["nodes"]) if len(u2) > 1 else None,
    "score_changed_1st_to_2nd": u2[0]["score"] != u2[1]["score"],
    "ucinewgame_makes_them_equal": u2n[0]["nodes"] == u2n[1]["nodes"],
    "clearhash_makes_them_equal": u2c[0]["nodes"] == u2c[1]["nodes"],
    "position_resend_makes_them_equal": u2p[0]["nodes"] == u2p[1]["nodes"],
    "third_search_vs_second": [u3[1]["nodes"], u3[2]["nodes"]] if len(u3) > 2 else None,
    "alone_across_3_processes_equal": len({r["nodes"] for r in u1rep}) == 1,
}
if summary["two_identical_unrestricted_searches_DIFFER"]:
    summary["verdict"] = (
        "10-F20 IS NOT ABOUT searchmoves. Two IDENTICAL unrestricted searches in one process differ "
        "(%s -> %s nodes); 'searchmoves' was incidental. The observation is about search/process state."
        % (u2[0]["nodes"], u2[1]["nodes"]))
else:
    summary["verdict"] = "10-F20 stands as a searchmoves-specific effect (two unrestricted searches agree)"
with open(os.path.join(OUT, "K14control", "summary.json"), "w") as f:
    json.dump(summary, f, indent=2)
    f.write("\n")
print(json.dumps(summary, indent=2))
