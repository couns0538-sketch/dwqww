#!/usr/bin/env python3
"""check_s07f1.py EXE

Check of seat 07's finding 07-F1 from its stated command alone:
  `position fen 7k/5Q2/6K1/8/8/8/8/8 b - - 0 1` + `go depth 3 searchmoves a1a2`
  is claimed to answer `info depth 3 ... score cp 0 nodes 0 ...` + `bestmove 0000`.

Beyond the finding, this script asks a question the finding does not: does a root with no legal
move reached by `searchmoves` produce the SAME answer as a terminal root reached normally?
(My 15-F5 records `score mate 0` on a checkmated root, seat 07 records `score cp 0` here.)

Controls, because "0000" and "nodes 0" are exactly what a broken harness also produces:
  (1) a LIVE board with one named legal move must search (>0 nodes, that move as bestmove);
  (2) a LIVE board with a legal searchmoves name must reproduce a normal bestmove.
Reader thread, deadline, ABSENT != 0.
"""
import argparse
import queue
import subprocess
import threading
import time

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]


def run(exe, poscmd, go, limit=30):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    q = queue.Queue()
    log = []

    def reader():
        for line in p.stdout:
            q.put(line.rstrip("\n"))
        q.put(None)

    threading.Thread(target=reader, daemon=True).start()

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def wait(pred, lim):
        t0 = time.monotonic()
        while True:
            rem = lim - (time.monotonic() - t0)
            if rem <= 0:
                return "TIMEOUT"
            try:
                line = q.get(timeout=rem)
            except queue.Empty:
                return "TIMEOUT"
            if line is None:
                return "EOF"
            log.append(line)
            if pred(line):
                return line

    send("uci"); wait(lambda l: l.startswith("uciok"), 20)
    send("setoption name Threads value 1"); send("setoption name Hash value 16")
    for k, v in S14:
        send("setoption name %s value %s" % (k, v))
    send("isready"); wait(lambda l: l == "readyok", 20)
    send("ucinewgame"); send("isready"); wait(lambda l: l == "readyok", 20)
    send(poscmd); send("isready"); wait(lambda l: l == "readyok", 20)
    send("go " + go)
    bm = wait(lambda l: l.startswith("bestmove"), limit)
    try:
        send("quit"); p.wait(timeout=10)
    except Exception:
        p.kill()
    infos = [l for l in log if l.startswith("info depth")]
    strings = [l for l in log if l.startswith("info string")]
    return {"bestmove": bm, "infos": infos, "strings": strings, "log": log}


def show(label, r, want_infos=True):
    print("--- %s" % label)
    if r["bestmove"] in ("TIMEOUT", "EOF"):
        print("    bestmove: ABSENT (%s)" % r["bestmove"])
    else:
        print("    bestmove: %s" % r["bestmove"])
    print("    info depth lines: %d" % len(r["infos"]))
    if r["infos"]:
        print("    last: %s" % r["infos"][-1])
    for s in r["strings"]:
        print("    string: %s" % s)
    if not want_infos and r["infos"]:
        print("    !! UNEXPECTED info depth lines")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    a = ap.parse_args()
    E = a.exe
    TERM = "position fen 7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"   # stalemate, no legal move
    MATE = "position fen 7K/8/7q/8/8/8/bk4r1/8 w - - 0 1"  # checkmate, verified in job3
    START = "position startpos"

    print("exe: %s" % E, flush=True)
    print()
    print("=== 1. the finding's own case: terminal root + searchmoves naming an illegal move ===",
          flush=True)
    show("terminal stalemate, go depth 3 searchmoves a1a2",
         run(E, TERM, "depth 3 searchmoves a1a2"), want_infos=False)
    show("terminal stalemate, go depth 3 (no restriction)",
         run(E, TERM, "depth 3"), want_infos=False)
    show("checkmated root, go depth 3 searchmoves a1a2",
         run(E, MATE, "depth 3 searchmoves a1a2"), want_infos=False)
    print()
    print("=== 2. empty searchmoves list on a LIVE board (no legal root move in the restriction) ===",
          flush=True)
    show("startpos, go depth 4 searchmoves (empty list)",
         run(E, START, "depth 4 searchmoves"), want_infos=False)
    show("startpos, go depth 4 searchmoves e2e5 (illegal name only)",
         run(E, START, "depth 4 searchmoves e2e5"), want_infos=False)
    print()
    print("=== 3. CONTROLS: the harness must be able to see a real search ===", flush=True)
    show("startpos, go depth 4 (plain)", run(E, START, "depth 4"))
    show("startpos, go depth 4 searchmoves e2e4 (one legal name)",
         run(E, START, "depth 4 searchmoves e2e4"))


main()
