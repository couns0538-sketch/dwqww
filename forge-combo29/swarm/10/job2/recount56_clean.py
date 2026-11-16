#!/usr/bin/env python3
"""recount56_clean.py -- seat 10's SOUND legality recount of deepseek6 long56.

Why a second pass: in the recorded sequences several `go`s overlap (go ponder / go infinite
before a later `position`), so a bestmove cannot be attributed to a go by order alone. This
script therefore takes every (position in force, finite go) pair out of the committed
sequences file and runs THAT PAIR ALONE in a fresh process, which makes the searched
position unambiguous. `go infinite` / `go ponder` are reported separately as
"no bestmove without stop" and are NOT legality-checked.

Usage: recount56_clean.py EXE OUTDIR [--limit N]
Writes OUTDIR/clean56_summary.json and OUTDIR/clean56_illegal.txt
"""
import concurrent.futures
import json
import os
import subprocess
import sys

import chess

EXE = os.path.abspath(sys.argv[1])
OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)
LIMIT = None
if "--limit" in sys.argv:
    LIMIT = int(sys.argv[sys.argv.index("--limit") + 1])

SEQF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "seqs56.txt")


def parse_seqs(path):
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


def pairs():
    """(seq_index, position line or None, go line) for finite go commands."""
    out = []
    for i, lines in enumerate(parse_seqs(SEQF)):
        pos = None
        for line in lines:
            if line.startswith("position "):
                pos = line
            elif line.startswith("go "):
                if any(k in line for k in ("depth", "nodes", "movetime")):
                    out.append((i, pos, line))
    return out


def one(job):
    idx, pos, go = job
    cmds = ["uci", "isready"]
    if pos:
        cmds.append(pos)
        cmds.append("isready")
    cmds.append(go)
    p = subprocess.run([EXE], input="\n".join(cmds) + "\nquit\n",
                       capture_output=True, text=True, timeout=60)
    best = None
    for l in p.stdout.splitlines():
        if l.startswith("bestmove"):
            best = l.split()[1]
    res = {"seq": idx, "pos": pos, "go": go, "bestmove": best,
           "rc": p.returncode, "check": "ok"}
    if best is None:
        res["check"] = "no bestmove"
        return res
    if best == "0000":
        res["check"] = "0000 (no legal moves)"
        return res
    b = board_after(pos) if pos else chess.Board()
    if b is None:
        res["check"] = "position unparseable by python-chess"
        return res
    try:
        m = chess.Move.from_uci(best)
    except ValueError:
        res["check"] = "ILLEGAL (unparseable move)"
        return res
    if m not in b.legal_moves:
        res["check"] = "ILLEGAL"
        res["fen"] = b.fen()
    return res


def main():
    jobs = pairs()
    if LIMIT:
        jobs = jobs[:LIMIT]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        res = list(ex.map(one, jobs))
    tot = {"pairs": len(res),
           "checked_legal": sum(1 for r in res if r["check"] == "ok"),
           "illegal": sum(1 for r in res if r["check"].startswith("ILLEGAL")),
           "bestmove_0000": sum(1 for r in res if r["check"].startswith("0000")),
           "no_bestmove": sum(1 for r in res if r["check"] == "no bestmove"),
           "position_unparseable": sum(1 for r in res
                                       if r["check"] == "position unparseable by python-chess"),
           "nonzero_exit": sum(1 for r in res if r["rc"] != 0)}
    with open(os.path.join(OUT, "clean56_summary.json"), "w") as f:
        json.dump(tot, f, indent=2)
        f.write("\n")
    with open(os.path.join(OUT, "clean56_illegal.txt"), "w") as f:
        for r in res:
            if r["check"].startswith("ILLEGAL"):
                f.write(json.dumps(r) + "\n")
    print(json.dumps(tot, indent=2))


main()
