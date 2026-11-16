#!/usr/bin/env python3
"""f3_all20_mechanism.py <exe> <outdir> [--label NAME]

The all-20 restriction is the clean like-for-like case (it excludes nothing), and it isolates the
mechanism of the restricted-root score defect:

  startpos has 20 legal moves. `go depth 12 searchmoves <all 20>` must, logically, equal `go depth 12`.
  On the base build it does not: cp 23 / 21640 nodes / d2d4 against cp 30 / 56720 / e2e4.

This script takes ANY build and prints that comparison, so the mechanism can be re-checked after a
candidate fix. Run it on:
  build-release   base                       -> gap (the defect)
  build-sm        IIR stopped at a restricted root
  build-sm2       IIR stopped AND the root TT store restored   -> for the all-20 case: exact

Also prints the `searchmoves d2d4 e2e4` case, which is NOT exact even on build-sm2 — the honest limit
of the mechanism.

Every cell is a fresh process, paced (waits for bestmove), and asserts its `info depth N` line.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

ALL20 = "a2a3 b2b3 c2c3 d2d3 e2e3 f2f3 g2g3 h2h3 a2a4 b2b4 c2c4 d2d4 e2e4 f2f4 g2g4 h2h4 b1a3 b1c3 g1f3 g1h3"
DEPTH = 12


class Missing(Exception):
    pass


def run(exe, limit, timeout=300):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n"); p.stdin.flush()

    def until(pred, tmo=timeout):
        t0 = time.monotonic(); out = []
        while time.monotonic() - t0 < tmo:
            ln = p.stdout.readline()
            if not ln:
                break
            s = ln.rstrip("\n"); out.append(s)
            if pred(s):
                return out, True
        return out, False

    try:
        send("uci")
        _, ok = until(lambda s: s.strip() == "uciok")
        if not ok:
            raise Missing("no uciok")
        send("setoption name Hash value 16"); send("isready")
        until(lambda s: s.strip() == "readyok")
        send("setoption name Threads value 1"); send("isready")
        until(lambda s: s.strip() == "readyok")
        send("ucinewgame"); send("isready")
        until(lambda s: s.strip() == "readyok")
        send("position startpos"); send("isready")
        until(lambda s: s.strip() == "readyok")
        send(limit)
        lines, ok = until(lambda s: s.startswith("bestmove"))
        if not ok:
            raise Missing("no bestmove for %r" % limit)
        infos = [l for l in lines if l.startswith("info depth %d " % DEPTH)]
        if not infos:
            raise Missing("no 'info depth %d' line for %r (19-F12 signature)" % (DEPTH, limit))
        last = infos[-1]
        n = re.search(r"nodes (\d+)", last)
        sc = re.search(r"score (cp|mate) (-?\d+)", last)
        if not n or not sc:
            raise Missing("info line lacks nodes/score: %r" % last)
        bm = next(l for l in lines if l.startswith("bestmove")).split()[1]
        return {"limit": limit, "score": (sc.group(1), int(sc.group(2))),
                "nodes": int(n.group(1)), "bestmove": bm}
    finally:
        try:
            send("quit"); p.wait(timeout=20)
        except Exception:
            p.kill()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe"); ap.add_argument("outdir")
    ap.add_argument("--label", default="")
    a = ap.parse_args()
    exe = os.path.realpath(a.exe)
    os.makedirs(a.outdir, exist_ok=True)

    # EACH SEARCH IS ITS OWN FRESH PROCESS (run() opens a new Popen and closes it per call -- verified
    # by reading run() below, not assumed). Seat 10's rule is why that matters: two identical
    # unrestricted searches in ONE process give 56,720 then 4,951 then 4,516 nodes, `ucinewgame`
    # restores cold exactly while `Clear Hash` does NOT (a third value, 40,569). So a cold baseline is
    # a fresh process or `ucinewgame`, never `Clear Hash`, and node counts must never be compared
    # across searches that shared a process. This script has always used one process per row; the note
    # is here so the property stays visible if anyone refactors it into a single session.
    plain = run(exe, "go depth %d" % DEPTH)                      # fresh process
    all20 = run(exe, "go depth %d searchmoves %s" % (DEPTH, ALL20))   # fresh process
    two = run(exe, "go depth %d searchmoves d2d4 e2e4" % DEPTH)       # fresh process
    one = run(exe, "go depth %d searchmoves e2e4" % DEPTH)            # fresh process

    same_as_plain = (all20["score"] == plain["score"] and all20["nodes"] == plain["nodes"]
                     and all20["bestmove"] == plain["bestmove"])
    out = {"exe": exe,
           "sha256": subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0],
           "label": a.label,
           "date_utc": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                      capture_output=True, text=True).stdout.strip(),
           "plain": plain, "all20": all20, "two_moves": two, "one_move": one,
           "all20_equals_plain": same_as_plain,
           "process_policy": "one fresh process per search (no shared table between rows)"}
    with open(os.path.join(a.outdir, "all20_%s.json" % (a.label or "run")), "w") as f:
        json.dump(out, f, indent=2)
    print("%-14s plain cp %s / %s nodes / %s" % ("unrestricted", plain["score"][1],
                                                 plain["nodes"], plain["bestmove"]))
    print("%-14s cp %s / %s nodes / %s  -> %s" % ("all 20", all20["score"][1], all20["nodes"],
                                                  all20["bestmove"],
                                                  "EQUALS unrestricted" if same_as_plain else "DIFFERS"))
    print("%-14s cp %s / %s nodes / %s" % ("d2d4 e2e4", two["score"][1], two["nodes"], two["bestmove"]))
    print("%-14s cp %s / %s nodes / %s" % ("e2e4", one["score"][1], one["nodes"], one["bestmove"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
