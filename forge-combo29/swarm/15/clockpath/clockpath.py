#!/usr/bin/env python3
"""clockpath.py EXE --reps 5

All FOUR budget modes on the same five boards, PC r15 under PC20, Threads 1, Hash 16:
  go nodes <N>          hard node ceiling
  go softnodes <N>       depth-complete soft node budget
  go movetime <ms>      time ceiling
  go wtime/btime/winc   the PC's match setting (6 s + 0.06)

For each: depth reached, nodes, bestmove, and WALL time from sending `go` to reading `bestmove`
(monotonic). Node budgets are chosen so the node modes land near the time modes' depth, so the four
are comparable: movetime 100 ms and wtime 6000+60 are measured, and `nodes 2000` / `softnodes 2000`
give the short-budget comparison.

A missing token is PARSE_FAIL, never 0. A refused FEN is reported, never counted.
"""
import argparse
import json
import queue
import re
import subprocess
import threading
import time

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

BOARDS = [
    ("startpos", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    ("G-mid-1", "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"),
    ("G-mid-2", "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1"),
    ("G-end-1", "8/8/6K1/1kr5/8/8/8/r7 w - - 0 1"),
    ("G-end-2", "k7/6R1/5N2/p4K1P/P7/8/8/8 b - - 0 1"),
]

MODES = [
    ("nodes 2000", "nodes 2000", "nodes"),
    ("softnodes 2000", "softnodes 2000", "softnodes"),
    ("movetime 100", "movetime 100", "time"),
    ("wtime 6000+60", "wtime 6000 btime 6000 winc 60 binc 60", "time"),
]


def one(exe, poscmd, goname, limit=60):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    q = queue.Queue()

    def rd():
        for line in p.stdout:
            q.put(line.rstrip("\n"))
        q.put(None)

    threading.Thread(target=rd, daemon=True).start()

    def send(c):
        p.stdin.write(c + "\n"); p.stdin.flush()

    def wait(pred, lim):
        t0 = time.monotonic()
        while True:
            rem = lim - (time.monotonic() - t0)
            if rem <= 0:
                return "TIMEOUT", None
            try:
                line = q.get(timeout=rem)
            except queue.Empty:
                return "TIMEOUT", None
            if line is None:
                return "EOF", None
            if pred(line):
                return "OK", line

    send("uci"); wait(lambda l: l.startswith("uciok"), 30)
    send("setoption name Threads value 1"); send("setoption name Hash value 16")
    for k, v in PC20:
        send("setoption name %s value %s" % (k, v))
    send("isready"); wait(lambda l: l == "readyok", 30)
    send("ucinewgame"); send("isready"); wait(lambda l: l == "readyok", 30)
    send("position fen " + poscmd); send("isready")
    refused = []
    t0 = time.monotonic()
    while time.monotonic() - t0 < 20:
        try:
            line = q.get(timeout=0.5)
        except queue.Empty:
            continue
        if line is None:
            break
        if any(b in line for b in ("invalid FEN", "invalid value", "illegal move", "unknown option")):
            refused.append(line)
        if line.strip() == "readyok":
            break
    if refused:
        try:
            send("quit"); p.wait(timeout=10)
        except Exception:
            p.kill()
        return {"refused": refused}
    t_go = time.monotonic()
    send("go " + goname)
    infos, bm = [], None
    while time.monotonic() - t_go < limit:
        try:
            line = q.get(timeout=0.5)
        except queue.Empty:
            continue
        if line is None:
            break
        if line.startswith("info depth"):
            infos.append(line)
        if line.startswith("bestmove"):
            bm = line
            break
    wall = time.monotonic() - t_go
    try:
        send("quit"); p.wait(timeout=10)
    except Exception:
        p.kill()
    depths = []
    for l in infos:
        m = re.match(r"info depth (\d+)", l)
        if m:
            depths.append(int(m.group(1)))
    last = infos[-1] if infos else None
    score = nodes = None
    if last:
        m = re.search(r"score (cp|mate) (-?\d+)", last)
        score = ("%s %s" % (m.group(1), m.group(2))) if m else "PARSE_FAIL"
        m2 = re.search(r"\bnodes (\d+)", last)
        nodes = int(m2.group(1)) if m2 else "PARSE_FAIL"
    tok = bm.split() if bm else []
    return {"score": score, "nodes": nodes, "depth": max(depths) if depths else None,
            "bestmove": tok[1] if len(tok) > 1 else None, "wall_ms": int(wall * 1000),
            "gap": bool(depths) and sorted(set(range(1, max(depths) + 1)) - set(depths))}


def legal(fen, uci):
    if not uci or uci == "0000":
        return None
    try:
        return chess.Move.from_uci(uci) in chess.Board(fen).legal_moves
    except ValueError:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--out", default="clock.jsonl")
    a = ap.parse_args()
    print("exe: %s  PC20  Threads 1  Hash 16  reps %d" % (a.exe, a.reps), flush=True)
    print("%-9s %-16s %-3s %-6s %-9s %-8s %-8s %s" %
          ("board", "mode", "n", "depth", "nodes", "wall_ms", "gap", "score / move"), flush=True)
    rows = []
    for label, fen in BOARDS:
        for mname, goname, kind in MODES:
            runs = []
            for r in range(a.reps):
                res = one(a.exe, fen, goname)
                if "refused" in res:
                    print("  REFUSED %s" % res["refused"], flush=True)
                    break
                runs.append(res)
            if not runs:
                continue
            walls = sorted(x["wall_ms"] for x in runs)
            depths = sorted({x["depth"] for x in runs})
            nodes = sorted(x["nodes"] for x in runs if isinstance(x["nodes"], int))
            moves = sorted({x["bestmove"] for x in runs})
            scores = sorted({x["score"] for x in runs})
            print("%-9s %-16s %-3d %-6s %-9s %-8s %-8s %s | %s" %
                  (label, mname, a.reps,
                   "/".join(str(d) for d in depths),
                   (str(nodes[0]) + "-" + str(nodes[-1])) if len(nodes) > 1 else str(nodes[0] if nodes else "?"),
                   str(walls[len(walls) // 2]),
                   "yes" if any(x["gap"] for x in runs) else "no",
                   ",".join(scores), ",".join(str(m) for m in moves)), flush=True)
            rows.append({"board": label, "mode": mname, "kind": kind, "runs": runs,
                         "depths": depths, "nodes": nodes, "walls": walls,
                         "moves": moves, "scores": scores})
    with open(a.out, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    print("\nwrote %s (%d rows)" % (a.out, len(rows)), flush=True)


if __name__ == "__main__":
    main()
