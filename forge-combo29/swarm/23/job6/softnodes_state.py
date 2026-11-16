#!/usr/bin/env python3
"""softnodes_state.py : WHY do in-process repeats of `go softnodes N` differ?

Question: is it the transposition table persisting between searches, and do `ucinewgame` / `Clear Hash`
restore the fresh-process behaviour?

Design (one process, one position, so nothing else can vary):
  1 first search in a fresh process   (reference: the fresh-process value)
  2 same search again, nothing between
  3 after ucinewgame + isready
  4 after `setoption name Clear Hash` (a button)
  5 after ucinewgame AND Clear Hash
  6 after another position in between
  7 once more immediately
Run twice in two separate processes, so a pattern can be told from noise.
"""
import hashlib
import json
import re
import subprocess
import sys

EXE = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/pcbuild/forge"
OPTFILE = sys.argv[2] if len(sys.argv) > 2 else "pc20_opts.txt"
FEN = sys.argv[3] if len(sys.argv) > 3 else "2r4r/pp4k1/3q2p1/3ppn2/1P4QP/P2P1N2/1PP3PP/2KR3R w - - 1 22"
N = int(sys.argv[4]) if len(sys.argv) > 4 else 2000
OUT = sys.argv[5] if len(sys.argv) > 5 else "state.json"

INFO = re.compile(r"^info depth (\d+).*?nodes (\d+)")


def run_sequence(label):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    opts = [l.strip() for l in open(OPTFILE) if l.strip() and not l.startswith("#")]
    p.stdin.write("uci\n"); p.stdin.flush()
    names = set()
    while True:
        line = p.stdout.readline()
        if not line:
            raise RuntimeError("died in uci")
        line = line.strip()
        if line.startswith("option name "):
            names.add(line.split("option name ")[1].split(" type ")[0])
        if line == "uciok":
            break
    for line in opts:
        name = line.split("name ")[1].split(" value ")[0]
        if name not in names:
            raise RuntimeError("STOP: %r not in uci list" % name)
        p.stdin.write(line + "\n"); p.stdin.flush()
        p.stdin.write("isready\n"); p.stdin.flush()
        while p.stdout.readline().strip() != "readyok":
            pass

    rec = []

    def sync():
        p.stdin.write("isready\n"); p.stdin.flush()
        while p.stdout.readline().strip() != "readyok":
            pass

    def do(tag):
        p.stdin.write("position fen %s\n" % FEN); sync()
        p.stdin.write("go softnodes %d\n" % N); p.stdin.flush()
        depths = []
        while True:
            line = p.stdout.readline()
            if not line:
                raise RuntimeError("died in search")
            line = line.strip()
            m = INFO.match(line)
            if m:
                depths.append([int(m.group(1)), int(m.group(2))])
            if line.startswith("bestmove"):
                rec.append({"tag": tag, "bestmove": line.split()[1],
                            "last_nodes": depths[-1][1] if depths else 0,
                            "depths": depths})
                return

    do("1 first search (fresh)")
    do("2 again, nothing between")
    p.stdin.write("ucinewgame\n"); p.stdin.flush(); sync()
    do("3 after ucinewgame")
    p.stdin.write("setoption name Clear Hash\n"); p.stdin.flush(); sync()
    do("4 after Clear Hash")
    p.stdin.write("ucinewgame\n"); p.stdin.flush(); sync()
    p.stdin.write("setoption name Clear Hash\n"); p.stdin.flush(); sync()
    do("5 after ucinewgame + Clear Hash")
    p.stdin.write("position startpos\n"); sync()
    do("6 after another position")
    do("7 once more immediately")
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    return {"process": label, "records": rec}


out = {"exe": EXE, "sha256": hashlib.sha256(open(EXE, "rb").read()).hexdigest(),
       "fen": FEN, "n": N, "sequences": [run_sequence("A"), run_sequence("B")]}
json.dump(out, open(OUT, "w"), indent=1)

for seq in out["sequences"]:
    print("== process %s" % seq["process"])
    for r in seq["records"]:
        print("   %-32s bestmove=%-6s nodes=%-6d ladder=%s" %
              (r["tag"], r["bestmove"], r["last_nodes"], r["depths"]))
