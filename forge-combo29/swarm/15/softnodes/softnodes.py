#!/usr/bin/env python3
"""softnodes.py EXE --ns 500,2000,20000 --reps 5

`go softnodes N` on the PC build under PC20, Threads 1, Hash 16.
File 6 says the PC's self-play uses `go softnodes 2000` and that it "stops at the end of the first
depth after 2,000 nodes". This measures, per (board, N):
  - determinism: are score / nodes / bestmove identical across REPS runs?
  - finished depth: is the printed depth sequence exactly 1..D with no gaps (so D was completed)?
  - overshoot: nodes / N, and how many nodes past N
  - legality of bestmove (python-chess)

A missing token is PARSE_FAIL, never 0. A refused FEN is reported and dropped.
"""
import argparse
import json
import os
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

# Five boards: startpos, two middlegames and two endgames, all from real games (set G) except startpos.
BOARDS = [
    ("startpos", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    ("G-mid-1", "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"),
    ("G-mid-2", "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1"),
    ("G-end-1", "8/8/6K1/1kr5/8/8/8/r7 w - - 0 1"),
    ("G-end-2", "k7/6R1/5N2/p4K1P/P7/8/8/8 b - - 0 1"),
]


def one(exe, poscmd, goname, limit=300):
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
    send(poscmd); send("isready")
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
    t_start = time.monotonic()
    send("go " + goname)
    infos, bm = [], None
    while time.monotonic() - t_start < limit:
        try:
            line = q.get(timeout=1.0)
        except queue.Empty:
            continue
        if line is None:
            break
        if line.startswith("info depth"):
            infos.append(line)
        if line.startswith("bestmove"):
            bm = line
            break
    wall = time.monotonic() - t_start
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
    return {"score": score, "nodes": nodes, "depth": depths[-1] if depths else None,
            "depths": depths, "bestmove": tok[1] if len(tok) > 1 else None,
            "wall_ms": int(wall * 1000),
            "gaps": (sorted(set(range(1, (depths[-1] if depths else 0) + 1))
                            - set(depths)))}


def legal(fen, uci):
    if not uci or uci == "0000":
        return True
    try:
        b = chess.Board(fen)
    except Exception:
        return True
    try:
        return chess.Move.from_uci(uci) in b.legal_moves
    except ValueError:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--ns", default="500,2000,20000")
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--out", default="softnodes.jsonl")
    a = ap.parse_args()
    ns = [int(x) for x in a.ns.split(",")]
    print("exe: %s   PC20   Threads 1   Hash 16   reps %d" % (a.exe, a.reps), flush=True)
    rows = []
    for label, fen in BOARDS:
        for n in ns:
            runs = []
            for r in range(a.reps):
                res = one(a.exe, "position fen " + fen, "softnodes %d" % n)
                if "refused" in res:
                    print("  %s N=%d REFUSED %s" % (label, n, res["refused"]), flush=True)
                    break
                runs.append(res)
            if not runs:
                continue
            keys = {(x["score"], x["nodes"], x["bestmove"]) for x in runs}
            det = len(keys) == 1
            x0 = runs[0]
            over = (x0["nodes"] / n - 1.0) * 100 if isinstance(x0["nodes"], int) and n else None
            ok_legal = all(legal(fen, x["bestmove"]) for x in runs)
            print("%-8s N=%-6d depth=%-3s nodes=%-8s overshoot=%7s%%  det=%-5s gaps=%-8s legal=%s  %s"
                  % (label, n, x0["depth"], x0["nodes"],
                     ("%+.1f" % over) if over is not None else "n/a",
                     det, x0["gaps"] if x0["gaps"] else "none", ok_legal,
                     x0["score"]), flush=True)
            if not det:
                for x in runs:
                    print("      run: %s  nodes=%s  bm=%s" % (x["score"], x["nodes"], x["bestmove"]),
                          flush=True)
            rows.append({"board": label, "fen": fen, "N": n, "deterministic": det,
                         "depth": x0["depth"], "nodes": x0["nodes"], "gaps": x0["gaps"],
                         "overshoot_pct": over, "score": x0["score"], "runs": runs})
    with open(a.out, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    print("\nwrote %s (%d rows)" % (a.out, len(rows)), flush=True)


if __name__ == "__main__":
    main()
