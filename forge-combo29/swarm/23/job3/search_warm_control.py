#!/usr/bin/env python3
"""search_warm_control.py : the CONTROL for perft_repeat.sh case E, done correctly.

Case E in the bash script pipelined `go depth 12` twice and closed stdin, so it hit seat 19's
fabricated-bestmove path (two `bestmove a2a3`, 0 nodes) and proved nothing. A control must be
valid before it can control anything, so this drains stdout to `bestmove` before the next command
and reports the node count of each of the two searches in one process.

If the second search reports fewer nodes than the first, the harness can see warm state and
perft_repeat.sh's identical perft counts mean "perft is unaffected", not "the harness is blind".
"""
import re
import subprocess
import sys

EXE = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/build/forge"

p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT, text=True, bufsize=1)


def send(line):
    p.stdin.write(line + "\n")
    p.stdin.flush()


def drain_to_bestmove():
    nodes = []
    while True:
        line = p.stdout.readline()
        if not line:
            raise RuntimeError("engine closed stdout before bestmove")
        line = line.strip()
        m = re.search(r"\bnodes (\d+)", line)
        if m:
            nodes.append(int(m.group(1)))
        if line.startswith("bestmove"):
            return line, (nodes[-1] if nodes else None)


send("uci")
while p.stdout.readline().strip() != "uciok":
    pass
send("isready")
while p.stdout.readline().strip() != "readyok":
    pass
send("position startpos")
send("isready")
while p.stdout.readline().strip() != "readyok":
    pass

send("go depth 12")
bm1, n1 = drain_to_bestmove()
send("go depth 12")
bm2, n2 = drain_to_bestmove()

print("search 1: bestmove %s nodes %s" % (bm1.split()[-1], n1))
print("search 2: bestmove %s nodes %s" % (bm2.split()[-1], n2))
print("same node count:", n1 == n2)
print("VERDICT: this harness %s warm state" % ("CAN see" if n1 != n2 else "CANNOT see"))
send("quit")
p.wait(timeout=10)
