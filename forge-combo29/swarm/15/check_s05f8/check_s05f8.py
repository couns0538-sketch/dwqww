#!/usr/bin/env python3
"""check_s05f8.py EXE [--timeout 25]

Check of seat 05's finding S-F8: "`go infinite` at a terminal root produced no bestmove within
25 s and had to be killed, while every bounded command on the same board answered in 0.02-0.03 s".

Harness written from the finding's command alone (not copied). Keeps stdin open, waits for
`bestmove` up to TIMEOUT seconds, reports ABSENT when none arrives, and distinguishes
ABSENT from a zero. Control: the same `go infinite` on a NON-terminal board must produce a
bestmove after `stop`, proving the harness can see a bestmove at all.

Also tests, as a second experiment the finding does not cover: is `stop` sufficient to make
`go infinite` answer at a terminal root?
"""
import argparse
import queue
import threading
import subprocess
import sys
import time

def run(exe, fen, go, timeout, send_stop_after=None):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    def send(c):
        p.stdin.write(c + "\n"); p.stdin.flush()
    log = []
    q = queue.Queue()

    def reader():
        for line in p.stdout:
            q.put(line.rstrip("\n"))
        q.put(None)

    threading.Thread(target=reader, daemon=True).start()

    def wait_for(pred, limit):
        """Deadline on a queue fed by a reader THREAD.

        select() on a buffered TextIOWrapper is unreliable (data already in the Python
        buffer is invisible to select), which made an earlier version of this script report
        ABSENT for runs that do answer. A reader thread has no such blind spot.
        """
        t0 = time.monotonic()
        while True:
            remaining = limit - (time.monotonic() - t0)
            if remaining <= 0:
                return "TIMEOUT", log
            try:
                line = q.get(timeout=remaining)
            except queue.Empty:
                return "TIMEOUT", log
            if line is None:
                return None, log
            log.append(line)
            if pred(line):
                return line, log
    send("uci"); wait_for(lambda l: l.startswith("uciok"), 20)
    send("setoption name Threads value 1"); send("setoption name Hash value 16")
    send("isready"); wait_for(lambda l: l == "readyok", 20)
    send("ucinewgame"); send("isready"); wait_for(lambda l: l == "readyok", 20)
    send("position fen " + fen); send("isready"); wait_for(lambda l: l == "readyok", 20)
    t_go = time.monotonic()
    send("go " + go)
    if send_stop_after is not None:
        time.sleep(send_stop_after)
        send("stop")
        log.append("### stop sent at %.3f s" % (time.monotonic() - t_go))
    line, log = wait_for(lambda l: l.startswith("bestmove"), timeout)
    dt = time.monotonic() - t_go
    if line in (None, "TIMEOUT"):
        verdict = "ABSENT (no bestmove in %.0fs)" % timeout
        bm = None
    else:
        verdict = "bestmove after %.3f s: %s" % (dt, line)
        bm = line.split()[1] if len(line.split()) > 1 else None
    try:
        send("quit"); p.wait(timeout=10)
    except Exception:
        p.kill()
    return verdict, bm, log

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--timeout", type=float, default=25.0)
    a = ap.parse_args()
    STALE = "8/8/8/8/8/6K1/8/Q5k1 b - - 0 1"      # seat 05's position (black to move, stalemate)
    MATE  = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"      # my own stalemate root
    LIVE  = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    print("exe: %s" % a.exe, flush=True)
    print(flush=True)
    print("=== A. reproduce: go infinite at a terminal root, NO stop (finding's own command) ===")
    for name, fen in (("05 stale", STALE), ("15 stale", MATE)):
        v, bm, _ = run(a.exe, fen, "infinite", a.timeout)
        print("  %-10s %s" % (name, v), flush=True)
    print(flush=True)
    print("=== B. the same board, bounded go (must answer) ===")
    for name, fen in (("05 stale", STALE), ("15 stale", MATE)):
        for go in ("depth 5", "nodes 100", "movetime 50"):
            v, bm, _ = run(a.exe, fen, go, a.timeout)
            print("  %-10s %-12s %s" % (name, go, v), flush=True)
    print(flush=True)
    print("=== C. control: go infinite on a LIVE board, stop after 1 s ===")
    v, bm, _ = run(a.exe, LIVE, "infinite", a.timeout, send_stop_after=1.0)
    print("  live-board  %s" % v, flush=True)
    print(flush=True)
    print("=== D. new: go infinite at a terminal root, then STOP after 1 s ===")
    for name, fen in (("05 stale", STALE), ("15 stale", MATE)):
        v, bm, _ = run(a.exe, fen, "infinite", a.timeout, send_stop_after=1.0)
        print("  %-10s %s" % (name, v), flush=True)

main()
