#!/usr/bin/env python3
"""The depth-64 clamp: a latency-measurement trap, characterised.

FOUND while building job 9's mate harness. It is not an engine defect — it is a property of the UCI
output that makes depth-based latency comparisons meaningless whenever a mate is on the board, which
matters for anyone timing search or comparing "depth reached" across positions.

WHAT HAPPENS
When the search proves a mate, the engine keeps reporting increasing `info depth N` lines until
N = 64, adding a fixed ~18 nodes per line, and stops at depth 64 even with 20,000 nodes of budget
left. On a mate-in-1 board: 64 info lines, final line `depth 64 ... nodes 1152`, i.e. it used 5.8 % of
the budget and reported the maximum depth.

WHAT IT IS NOT
- Not caused by the PC patch or by MateAlphaGuard: identical (64 lines, 1152 nodes) on the base build
  6b98f217 and on PC r15 with MateAlphaGuard both true and false.
- Not a general behaviour: on a non-mate board the same budget gives 10 info lines and
  `depth 10 ... nodes 13102`, stopping on the node budget normally.

WHY IT IS TRAPPING
1. "Depth reached" comparisons are invalid across mate/non-mate positions: 64 is a sentinel, not a
   depth. A table that averages depth over a mixed set is comparing a real number with a constant.
2. Latency harnesses that wait for a DEPTH (e.g. "stop at depth 12") get a near-instant answer and
   record a falsely low time on exactly the positions where they think they are measuring deep search.
3. A harness that assumes "more nodes = deeper" sees 1152 nodes with depth 64 and may conclude the
   engine is fast on endgames when it has simply found a mate.

HOW TO AVOID IT
- Treat `depth >= 64` as "mate proven", not as a depth. Exclude it from depth statistics or bucket it
  separately.
- Time by nodes or by clock, not by waiting for a depth, on any mixed position set.
- When a claim about speed rests on endgame boards, check whether a mate was present.

Usage: clamp.py EXE  (prints the evidence table)
"""
import subprocess
import sys

EXE = sys.argv[1]
OPTS = [("Threads", "1"), ("Hash", "16")]
MATE1 = "6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1"
NONMATE = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def run(fen, go):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

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
    for n, v in OPTS:
        if not any(o.startswith("option name %s " % n) for o in opts):
            raise SystemExit("FAIL: option %r not advertised" % n)
        send("setoption name %s value %s" % (n, v))
        send("isready")
        while p.stdout.readline().rstrip("\n") != "readyok":
            pass
    send("position fen " + fen)
    send("isready")
    while p.stdout.readline().rstrip("\n") != "readyok":
        pass
    send(go)
    infos = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise SystemExit("FAIL: died during search")
        l = l.rstrip("\n")
        if l.startswith("bestmove"):
            break
        if l.startswith("info depth"):
            infos.append(l)
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    return infos


print("| board | go | info lines | last depth | nodes on last line | nodes budget |")
print("|---|---|---|---|---|---|")
for name, fen in (("mate-in-1", MATE1), ("non-mate startpos", NONMATE)):
    for go in ("go nodes 20000", "go depth 12"):
        infos = run(fen, go)
        if not infos:
            print("| %s | %s | 0 | - | - | |" % (name, go))
            continue
        last = infos[-1]
        d = [x for x in last.split() if x.isdigit()]
        depth = last.split("depth ")[1].split()[0]
        nodes = last.split("nodes ")[1].split()[0] if "nodes " in last else "-"
        print("| %s | %s | %d | %s | %s | %s |"
              % (name, go, len(infos), depth, nodes,
                 "20000" if "nodes" in go else "n/a"))
print()
print("VERDICT: depth 64 with a small node count means a mate was proven, not that the search went 64")
print("plies deep. Exclude depth>=64 from any depth statistic and never gate a latency measure on depth.")
