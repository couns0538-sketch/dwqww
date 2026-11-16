#!/usr/bin/env python3
"""clean56_fixed.py -- RE-RUN of my job2 legality check with the EOF-safe driver.

WHY: my original recount56_clean.py drove each (position, go) pair through a plain pipe, which
triggers the EOF-abort trap (19-F12 / my 10-C5): the search is aborted and a fallback `bestmove`
is printed. A legality check on those moves is therefore near-vacuous -- it tests the fallback
move, not the search's choice. This version keeps stdin open and reads to `bestmove`.

Same pairs file (out/seqs56.txt), same finite-go selection, same legality test against python-chess.

Usage: clean56_fixed.py OUTDIR [LIMIT]
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
LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else None
SEQF = "/agent/repos/dwqww/forge-combo29/swarm/10/job2/out/seqs56.txt"


def parse(path):
    seqs, cur = [], None
    for line in open(path):
        line = line.rstrip("\n")
        if line.startswith("### seq "):
            cur = []
            seqs.append(cur)
        elif cur is not None:
            cur.append(line)
    return seqs


def board_after(pos_line):
    body = pos_line[len("position "):]
    try:
        if body.startswith("startpos"):
            b = chess.Board()
            if " moves " in body:
                for mv in body.split(" moves ", 1)[1].split():
                    try:
                        m = chess.Move.from_uci(mv)
                    except ValueError:
                        return b
                    if m not in b.legal_moves:
                        return b
                    b.push(m)
            return b
        if body.startswith("fen "):
            return chess.Board(body[4:].strip())
    except ValueError:
        return None
    return None


pairs = []
for i, lines in enumerate(parse(SEQF)):
    pos = None
    for line in lines:
        if line.startswith("position "):
            pos = line
        elif line.startswith("go ") and any(k in line for k in ("depth", "nodes", "movetime")):
            pairs.append((i, pos, line))
if LIMIT:
    pairs = pairs[:LIMIT]

d = Drv(EXE)
d.uci()
d.isready()
d.opt("OwnBook", "false")
d.isready()
res = []
for k, (idx, pos, go) in enumerate(pairs):
    d.write("ucinewgame")
    d.isready()
    if pos:
        d.pos(pos)
    else:
        d.pos("position startpos")
    nodes, best, lines = d.go(go)
    row = {"seq": idx, "go": go, "bestmove": best, "nodes": nodes, "check": "ok"}
    b = board_after(pos) if pos else chess.Board()
    if best is None:
        row["check"] = "no bestmove"
    elif best == "0000":
        row["check"] = "0000"
    elif b is None:
        row["check"] = "position unparseable"
    else:
        try:
            m = chess.Move.from_uci(best)
            if m not in b.legal_moves:
                row["check"] = "ILLEGAL"
                row["fen"] = b.fen()
        except ValueError:
            row["check"] = "ILLEGAL unparseable move"
    res.append(row)
    if k % 400 == 0:
        print("  %d/%d" % (k, len(pairs)), flush=True)
d.quit()

summary = {
    "pairs": len(res),
    "legal": sum(1 for r in res if r["check"] == "ok"),
    "illegal": sum(1 for r in res if r["check"].startswith("ILLEGAL")),
    "bestmove_0000": sum(1 for r in res if r["check"] == "0000"),
    "no_bestmove": sum(1 for r in res if r["check"] == "no bestmove"),
    "null_nodes": sum(1 for r in res if r["nodes"] is None),
}
with open(os.path.join(OUT, "clean56_fixed_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)
    f.write("\n")
with open(os.path.join(OUT, "clean56_fixed_all.json"), "w") as f:
    json.dump(res, f, indent=1)
    f.write("\n")
print(json.dumps(summary, indent=2))
