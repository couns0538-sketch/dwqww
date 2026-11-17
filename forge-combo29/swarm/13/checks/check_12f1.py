#!/usr/bin/env python3
"""Check of seat 12's 12-F1: does `ucinewgame` reset the board to startpos, and is it a COLD reset?

Two things are measured, and the second is the one that corrected my own job 16:

  A. BOARD RESET: `position fen <K+P>` then `ucinewgame` then `go` must search STARTPOS (d2d4, 26 nodes at
     depth 1) rather than the K+P position (e1d2, 10 nodes). Compared against the same sequence without
     ucinewgame, so the difference is attributable.

  B. TABLE RESET: three identical searches in one process, with and without ucinewgame between them. If
     ucinewgame clears the table the node counts stay identical; if not they collapse as the table warms.
     This is what makes ucinewgame a COLD-start control and NOT a warm one — which is why my job 16's
     "warm" arm was really cold, confirmed there by all 38 cold/warm pairs being identical.

Usage: check_12f1.py EXE OUTDIR
"""
import json
import os
import re
import subprocess
import sys

EXE = sys.argv[1]
OUTDIR = sys.argv[2]
os.makedirs(OUTDIR, exist_ok=True)
BAD = ("unknown option", "invalid value", "error")
KP = "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1"
MIDDLE = "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"
OPTS = [("Threads", "1"), ("Hash", "16"), ("OwnBook", "false")]


class Eng:
    def __init__(self):
        self.p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.send("uci")
        seen = []
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: died in uci handshake")
            l = l.rstrip("\n")
            if l.startswith("option name"):
                seen.append(l)
            if l == "uciok":
                break
        for n, v in OPTS:
            if not any(o.startswith("option name %s " % n) for o in seen):
                raise SystemExit("FAIL: option %r not advertised" % n)
            self.send("setoption name %s value %s" % (n, v))
            self.ready()

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def ready(self):
        self.send("isready")
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: engine died")
            l = l.rstrip("\n")
            if any(b in l.lower() for b in BAD):
                raise SystemExit("FAIL: bad line %r" % l)
            if l == "readyok":
                return

    def go(self, cmd="go depth 1"):
        self.send(cmd)
        last = None
        bm = None
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: engine died during search")
            l = l.rstrip("\n")
            if l.startswith("info depth"):
                last = l
            if l.startswith("bestmove"):
                bm = l
                break
        n = re.search(r"\bnodes (\d+)", last) if last else None
        return {"bestmove": (bm.split()[1] if bm and len(bm.split()) > 1 else None),
                "nodes": int(n.group(1)) if n else None}

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()


def main():
    out = {}

    # ---- A: board reset ----
    e = Eng()
    e.send("position fen " + KP); e.ready()
    without = e.go()                      # search the K+P position directly
    e.close()

    e = Eng()
    e.send("position fen " + KP); e.ready()
    e.send("ucinewgame"); e.ready()        # <-- the suspect command
    with_new = e.go()
    e.close()

    out["A_board_reset"] = {"position": KP, "without_ucinewgame": without,
                            "with_ucinewgame": with_new}
    print("A. board reset")
    print("   position fen K+P, then go          -> %s" % without)
    print("   position fen K+P, ucinewgame, go   -> %s" % with_new)

    # ---- B: table reset (cold vs warm) ----
    e = Eng()
    cold = []
    for _ in range(3):
        e.send("ucinewgame"); e.ready()
        e.send("position fen " + MIDDLE); e.ready()
        cold.append(e.go("go depth 12"))
    e.close()

    e = Eng()
    warm = []
    for _ in range(3):
        e.send("position fen " + MIDDLE); e.ready()
        warm.append(e.go("go depth 12"))
    e.close()

    out["B_table_reset"] = {"position": MIDDLE, "with_ucinewgame": cold, "without_ucinewgame": warm}
    print()
    print("B. table reset (three depth-12 searches in ONE process)")
    print("   with ucinewgame between : %s" % [c["nodes"] for c in cold])
    print("   without (warm table)    : %s" % [w["nodes"] for w in warm])

    cold_same = len({c["nodes"] for c in cold}) == 1
    warm_collapses = len({w["nodes"] for w in warm}) > 1
    board_reset = (with_new["bestmove"] != without["bestmove"]
                   and (with_new["nodes"] or 0) > (without["nodes"] or 0))
    summary = {
        "exe": os.path.abspath(EXE),
        "board_reset_confirmed": board_reset,
        "ucinewgame_is_a_cold_reset": cold_same and warm_collapses,
        "interpretation": ("ucinewgame resets the board to startpos AND clears the table, so it is a "
                           "COLD-start control, not a way to get a warm search"),
    }
    out["summary"] = summary
    json.dump(out, open(os.path.join(OUTDIR, "ucinewgame.json"), "w"), indent=1)
    print()
    for k, v in summary.items():
        print("%-34s %s" % (k, v))


main()
