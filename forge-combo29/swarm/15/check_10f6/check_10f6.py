#!/usr/bin/env python3
"""check_10f6.py EXE

Check of seat 10's 10-F6: "the brief's four honesty pins hold ONLY in the DEFAULT option regime:
with S14 setoptions applied first, bench 11/13/16 give 242,796 / 656,517 / 2,155,620 instead of
312,866 / 862,329 / 3,024,920 (perft 5 unchanged)."

Two regimes, each in its own fresh process, reading until the bench/perft terminator:
  A. plain: uci, isready, bench N
  B. S14:   uci, setoption Threads 1, Hash 16, the 14 S14 options, isready, bench N
Also perft 5 in both regimes via `position startpos` + `go perft 5`.
A parser that cannot find the number reports PARSE_FAIL, never 0.
"""
import argparse
import queue
import re
import subprocess
import threading

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]

WANT = {11: 312866, 13: 862329, 16: 3024920}


def run(exe, cmds, terminator, limit=600):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    q = queue.Queue()
    log = []

    def reader():
        for line in p.stdout:
            q.put(line.rstrip("\n"))
        q.put(None)

    threading.Thread(target=reader, daemon=True).start()
    for c in cmds:
        p.stdin.write(c + "\n")
    p.stdin.flush()
    import time
    t0 = time.monotonic()
    while True:
        rem = limit - (time.monotonic() - t0)
        if rem <= 0:
            break
        try:
            line = q.get(timeout=rem)
        except queue.Empty:
            break
        if line is None:
            break
        log.append(line)
        if terminator(log):
            break
    try:
        p.stdin.write("quit\n"); p.stdin.flush(); p.wait(timeout=10)
    except Exception:
        p.kill()
    return log


def bench_nodes(log, depth):
    """The bench prints a line carrying the node total. FAIL LOUDLY if it is absent."""
    cands = []
    for line in log:
        m = re.search(r"\bnodes\s+(\d+)", line)
        if m:
            cands.append(int(m.group(1)))
    if not cands:
        return None
    return cands[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    a = ap.parse_args()
    E = a.exe
    base = ["uci"]

    print("exe: %s" % E, flush=True)
    print(flush=True)
    print("%-6s %-8s %-14s %-14s %s" % ("bench", "regime", "nodes", "brief says", "verdict"), flush=True)

    results = {}
    for regime in ("plain", "S14"):
        for d in (11, 13, 16):
            cmds = list(base)
            if regime == "S14":
                cmds += ["setoption name Threads value 1", "setoption name Hash value 16"]
                cmds += ["setoption name %s value %s" % (k, v) for k, v in S14]
            cmds += ["isready", "bench %d" % d]
            log = run(E, cmds, lambda L: any("nodes" in x for x in L[-1:]) and
                      any(x.strip() == "" for x in L) is False and False or
                      (len(L) > 0 and re.search(r"\bnodes\s+\d+", L[-1]) is not None))
            n = bench_nodes(log, d)
            results[(regime, d)] = n
            verdict = "PARSE_FAIL" if n is None else ("MATCH" if n == WANT[d] else "DIFFERS")
            print("%-6d %-8s %-14s %-14d %s" % (d, regime, n if n is not None else "PARSE_FAIL",
                                                WANT[d], verdict), flush=True)

    print(flush=True)
    print("=== perft 5 in both regimes ===", flush=True)
    for regime in ("plain", "S14"):
        cmds = list(base)
        if regime == "S14":
            cmds += ["setoption name Threads value 1", "setoption name Hash value 16"]
            cmds += ["setoption name %s value %s" % (k, v) for k, v in S14]
        cmds += ["isready", "position startpos", "isready", "go perft 5"]
        log = run(E, cmds, lambda L: len(L) > 0 and re.search(r"\bnodes\s+\d+", L[-1]) is not None)
        n = bench_nodes(log, 5)
        print("%-6s %-8s %-14s %-14d %s" % ("perft5", regime, n if n is not None else "PARSE_FAIL",
                                            4865609, "MATCH" if n == 4865609 else "DIFFERS"),
              flush=True)


main()
