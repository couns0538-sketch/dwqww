#!/usr/bin/env python3
"""The PC's real search path: `go nodes` at the three match budgets, PC build, PC20, Threads 1.

FABLE_TO_swarm_6 says a find is worth most on the owner's actual path: PC build, PC20, Threads 1,
Hash 16, `go nodes` 20000 / 50000 / 250000 and `go softnodes 2000`, on positions from real games.

This measures, per position and budget:
  * determinism: the same request run twice in separate fresh processes must give identical
    depth, nodes, score and bestmove (Threads 1, so it should be exact);
  * whether the node budget is RESPECTED (`go nodes` is a hard limit, unlike softnodes);
  * the depth reached and the score, so a budget that buys an inconsistent depth is visible;
  * sanity of the move: it must be a legal move in the position.

LIMIT, stated up front: my positions are 12 from the G set (engine games), NOT the owner's own match
games, which I do not have. So this is "real-game-like", not "his games".

Usage: pcpath.py EXE FENS OUTDIR [NS]
"""
import hashlib
import json
import os
import re
import subprocess
import sys

import chess

EXE = sys.argv[1]
FENS = sys.argv[2]
OUTDIR = sys.argv[3]
NS = [int(x) for x in (sys.argv[4] if len(sys.argv) > 4 else "2000,20000,50000,250000").split(",")]
os.makedirs(OUTDIR, exist_ok=True)

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC6 = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
       ("MateAlphaGuard", "true"), ("OwnBook", "false")]
PC20 = [("Threads", "1"), ("Hash", "16")] + S14 + PC6
assert len(PC20) == 22, "PC20 must be 22 entries; a short list silently measures a different regime"
BAD = ("unknown option", "invalid value", "error")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def run(fen, go_cmd):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(pred, what):
        while True:
            l = p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: engine died waiting for %s" % what)
            l = l.rstrip("\n")
            if any(b in l.lower() for b in BAD):
                raise SystemExit("FAIL: bad line %r while waiting for %s" % (l, what))
            if pred(l):
                return l

    send("uci")
    opts = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise SystemExit("FAIL: died in uci handshake")
        l = l.rstrip("\n")
        if l.startswith("option name"):
            opts.append(l)
        if l == "uciok":
            break
    for n, v in PC20:
        if not any(o.startswith("option name %s " % n) for o in opts):
            raise SystemExit("FAIL: option %r not advertised" % n)
        send("setoption name %s value %s" % (n, v))
        send("isready")
        until(lambda s: s == "readyok", "readyok")
    send("position fen " + fen)
    send("isready")
    until(lambda s: s == "readyok", "readyok after position")
    send(go_cmd)

    infos = []
    bm = None
    softline = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise SystemExit("FAIL: engine died during search")
        l = l.rstrip("\n")
        if any(b in l.lower() for b in BAD):
            raise SystemExit("FAIL: bad line %r during search" % l)
        if l.startswith("bestmove"):
            bm = l
            break
        if l.startswith("info string softnodes"):
            softline = l
        elif l.startswith("info depth"):
            infos.append(l)
    send("quit")
    try:
        p.wait(timeout=15)
    except Exception:
        p.kill()

    def g(pat, l, cast=int):
        m = re.search(pat, l) if l else None
        return cast(m.group(1)) if m else None

    last = infos[-1] if infos else None
    return {
        "info_lines": len(infos),
        "depth": g(r"\bdepth (\d+)", last),
        "seldepth": g(r"\bseldepth (\d+)", last),
        "nodes": g(r"\bnodes (\d+)", last),
        "cp": g(r"\bscore cp (-?\d+)", last),
        "mate": g(r"\bscore mate (-?\d+)", last),
        "time_ms": g(r"\btime (\d+)", last),
        "pv": (re.search(r"\bpv (.+)$", last).group(1) if last and "pv " in last else None),
        "bestmove": bm,
        "softline": softline,
    }


def main():
    fens = [l.strip() for l in open(FENS) if l.strip()]
    rows = []
    for i, fen in enumerate(fens):
        b = chess.Board(fen)
        legal = {m.uci() for m in b.legal_moves}
        for N in NS:
            a = run(fen, "go nodes %d" % N)
            c = run(fen, "go nodes %d" % N)
            ident = (a["depth"], a["nodes"], a["cp"], a["mate"], a["bestmove"]) == \
                    (c["depth"], c["nodes"], c["cp"], c["mate"], c["bestmove"])
            mv = None
            if a["bestmove"] and a["bestmove"].startswith("bestmove "):
                parts = a["bestmove"].split()
                mv = parts[1] if len(parts) > 1 else None
            legal_move = (mv is None) or (mv in legal) or mv in ("(none)", "0000")
            over = (a["nodes"] - N) if a["nodes"] is not None else None
            row = {
                "position": i, "fen": fen, "N": N,
                "depth": a["depth"], "seldepth": a["seldepth"], "nodes": a["nodes"],
                "nodes_over_budget": over,
                "budget_respected": (over is not None and over <= 0),
                "cp": a["cp"], "mate": a["mate"], "time_ms": a["time_ms"],
                "bestmove": a["bestmove"], "bestmove_legal": legal_move,
                "deterministic": ident,
                "run_b_depth": c["depth"], "run_b_nodes": c["nodes"], "run_b_cp": c["cp"],
                "run_b_bestmove": c["bestmove"],
                "pv": a["pv"],
            }
            rows.append(row)
            print("pos %2d N %-7d depth %-3s nodes %-8s over %-6s legal %-5s det %-5s %s"
                  % (i, N, a["depth"], a["nodes"], over, legal_move, ident, a["bestmove"]),
                  flush=True)

    summary = {
        "build": os.path.abspath(EXE),
        "sha256": sha256(EXE),
        "settings": "PC20 (Threads 1, Hash 16, S14 + 6)",
        "positions": len(fens),
        "note": "positions are 12 from the G set (engine games), NOT the owner's match games",
        "budgets": NS,
        "runs": len(rows),
        "deterministic": sum(1 for r in rows if r["deterministic"]),
        "budget_respected": sum(1 for r in rows if r["budget_respected"]),
        "illegal_bestmoves": sum(1 for r in rows if not r["bestmove_legal"]),
        "max_nodes_over_budget": max((r["nodes_over_budget"] for r in rows
                                      if r["nodes_over_budget"] is not None), default=None),
        "depth_min": min((r["depth"] for r in rows if r["depth"] is not None), default=None),
        "depth_max": max((r["depth"] for r in rows if r["depth"] is not None), default=None),
    }
    with open(os.path.join(OUTDIR, "pcpath.json"), "w") as f:
        json.dump({"summary": summary, "rows": rows}, f, indent=1)
    print()
    for k, v in summary.items():
        print("%-28s %s" % (k, v))


main()
