#!/usr/bin/env python3
"""switches.py EXE FEN --depths 12,16 --regime-base s14

Tests the two switch claims on ONE board, one option at a time on top of S14:
  baseline S14 only
  CuckooRep true alone        (claim 1: makes the mate distance WORSE)
  MateAlphaGuard true alone   (claim 2: FIXES it)

For each: score, nodes, PV length, whether the PV ends in checkmate, and whether the plies match the
score. The TRUE mate distance is supplied by the caller (from the solver) and printed for comparison.

Threads 1. Every option name asserted against the exe's uci list. A refused FEN is reported, never
counted. A missing token is PARSE_FAIL, never 0.
"""
import argparse
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
# MateAlphaGuard must exist in the build (needs -DFORGE_MATE_ALPHA_GUARD=1)
GUARD_ON = [("MateAlphaGuard", "true")]
CUCKOO_ON = [("CuckooRep", "true")]


def one(exe, opts, fen, depth, limit=600):
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
    for k, v in opts:
        send("setoption name %s value %s" % (k, v))
    send("isready"); wait(lambda l: l == "readyok", 30)
    send("ucinewgame"); send("isready"); wait(lambda l: l == "readyok", 30)
    send("position fen " + fen); send("isready")
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
    send("go depth %d" % depth)
    infos, bm = [], None
    t0 = time.monotonic()
    while time.monotonic() - t0 < limit:
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
    try:
        send("quit"); p.wait(timeout=10)
    except Exception:
        p.kill()
    if not infos:
        return {"score": "NO_INFO_LINE", "nodes": None, "pv": [], "bestmove": None}
    last = infos[-1]
    m = re.search(r"score (cp|mate) (-?\d+)", last)
    m2 = re.search(r"\bnodes (\d+)", last)
    pv = last.split()[last.split().index("pv") + 1:] if " pv" in last else []
    return {"score": ("%s %s" % (m.group(1), m.group(2))) if m else "PARSE_FAIL",
            "nodes": int(m2.group(1)) if m2 else "PARSE_FAIL",
            "pv": pv, "bestmove": bm.split()[1] if bm and len(bm.split()) > 1 else None}


def judge(fen, res):
    """-> (pv_plies, ends_in_mate, plies_match_score)"""
    b = chess.Board(fen)
    ok = True
    for u in res["pv"]:
        try:
            mv = chess.Move.from_uci(u)
        except ValueError:
            ok = False; break
        if mv not in b.legal_moves:
            ok = False; break
        b.push(mv)
    if not ok:
        return len(res["pv"]), "ILLEGAL_PV", "n/a"
    ends = b.is_checkmate()
    sc = res["score"]
    if not sc.startswith("mate"):
        return len(res["pv"]), ends, "no mate score"
    v = int(sc.split()[1])
    want = (2 * v - 1) if v > 0 else 2 * abs(v)
    return len(res["pv"]), ends, ("plies==want" if len(res["pv"]) == want
                                  else "plies %d != want %d" % (len(res["pv"]), want))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("fen")
    ap.add_argument("--depths", default="12,16")
    ap.add_argument("--truth", default="", help="e.g. 'mated in 8 plies => mate -4'")
    a = ap.parse_args()
    depths = [int(x) for x in a.depths.split(",")]
    uciout = subprocess.run([a.exe], input="uci\nquit\n", capture_output=True, text=True).stdout
    names = set(re.findall(r"^option name (.+?) type ", uciout, re.M))
    arms = [("S14 baseline", S14), ("+ CuckooRep true ALONE", S14 + CUCKOO_ON),
            ("+ MateAlphaGuard true ALONE", S14 + GUARD_ON)]
    for label, opts in arms:
        for k, _ in opts:
            if k not in names:
                raise SystemExit("STOP: %r not in the exe's uci list (%s)" % (k, label))
    print("exe: %s   Threads 1   Hash 16" % a.exe)
    print("board: %s" % a.fen)
    if a.truth:
        print("TRUE distance (from python-chess solvers): %s" % a.truth)
    print()
    print("%-28s %-4s %-10s %-9s %-5s %-6s %s" %
          ("arm", "d", "score", "nodes", "pv", "mate?", "consistency"))
    for label, opts in arms:
        for d in depths:
            r = one(a.exe, opts, a.fen, d)
            if "refused" in r:
                print("%-28s %-4d REFUSED: %s" % (label, d, r["refused"]))
                continue
            plies, ends, cons = judge(a.fen, r)
            print("%-28s %-4d %-10s %-9s %-5d %-6s %s" %
                  (label, d, r["score"], r["nodes"], plies, ends, cons), flush=True)


if __name__ == "__main__":
    main()
