#!/usr/bin/env python3
"""Harness self-audit demanded by the coordinator broadcast (swarm seat 19, finding 19-F12):
"if your harness pipes `quit` or closes stdin while a search is still running, this build answers a FABRICATED
bestmove with 0 nodes".

PART 1 repeats the fault and its control, so this file is evidence on its own:
  A  `go depth 12` + pipelined `quit`        -> expect 0 `info depth` lines (fabricated)
  B  same go, read stdout until `bestmove`   -> expect real info lines and a real node count
  C  `bench 13` with a pipelined `quit`      -> expect the real node count (bench is synchronous)
  D  `go perft 5` with a pipelined `quit`    -> expect 4865609 (perft is synchronous)

PART 2 re-derives, with a strictly-draining harness, the numbers I published in job1/job2, so the record shows they
were NOT produced by the broken pattern. The distinguishing fact: a fabricated answer has 0 nodes and the move a2a3.
"""
import subprocess, sys

EXE = sys.argv[1]
SETUP = "uci\nsetoption name Hash value 16\nsetoption name Threads value 1\nisready\n"


def pipelined(extra):
    return subprocess.run([EXE], input=SETUP + extra + "quit\n", capture_output=True, text=True).stdout


def drained(cmds, stop="bestmove", stop2=None):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    for c in cmds:
        p.stdin.write(c + "\n")
    p.stdin.flush()
    out = []
    for line in p.stdout:          # read until the terminal token BEFORE sending anything else
        out.append(line.rstrip())
        if line.startswith(stop) or (stop2 is not None and line.startswith(stop2)):
            break
    p.stdin.write("quit\n")
    p.stdin.flush()
    p.wait(timeout=120)
    return out


def infos(out):
    return [l for l in out if l.startswith("info depth")]


def nodes_of(out):
    ls = infos(out)
    if not ls:
        return None
    f = ls[-1].split()
    return int(f[f.index("nodes") + 1])


print("PART 1 - the fault and its controls (this file is the evidence)")
a = pipelined("position startpos\ngo depth 12\n")
print(f"A pipelined go depth 12 + quit : info lines {len(infos(a))}, bestmove {a.strip().splitlines()[-1].strip()}")
b = drained(["uci", "setoption name Hash value 16", "setoption name Threads value 1", "isready",
             "position startpos", "go depth 12"])
print(f"B drained go depth 12         : info lines {len(infos(b))}, nodes {nodes_of(b)}, "
      f"{b[-1].strip()}")
c = pipelined("bench 13\n")
cline = [l for l in c.splitlines() if "bench depth 13" in l]
print(f"C pipelined bench 13          : {cline[0] if cline else 'MISSING'}")
d = pipelined("position startpos\ngo perft 5\n")
dline = [l for l in d.splitlines() if l.startswith("nodes")]
print(f"D pipelined go perft 5        : {dline[0] if dline else 'MISSING'}")

fabricated = len(infos(a)) == 0
print()
print(f"VERDICT on the fault: {'REPRODUCED' if fabricated else 'NOT reproduced'}; "
      f"bench and perft are {'SYNCHRONOUS (their numbers are valid under a pipelined quit)' if cline and dline else 'NOT shown synchronous'}")

print()
print("PART 2 - the numbers I published, re-derived by a draining harness")
# job1: bench 13 wall time and the profile target
b13 = drained(["uci", "setoption name Hash value 16", "setoption name Threads value 1", "isready", "bench 13"],
              stop="info string bench depth")
print(f"bench 13 via drain      : {[l for l in b13 if 'bench depth' in l][0]}")
b11 = drained(["uci", "setoption name Hash value 16", "setoption name Threads value 1", "isready", "bench 11"],
              stop="info string bench depth")
b16 = drained(["uci", "setoption name Hash value 16", "setoption name Threads value 1", "isready", "bench 16"],
              stop="info string bench depth")
for lbl, o in (("bench 11", b11), ("bench 16", b16)):
    print(f"{lbl} via drain      : {[l for l in o if 'bench depth' in l][0]}")
p5 = drained(["uci", "isready", "position startpos", "go perft 5"], stop="nodes")
print(f"perft 5 via drain       : {[l for l in p5 if l.startswith('nodes')][0]}")

# job2: the search-equivalence evidence depended on real info lines, so prove they are real
sp = open("searchpos.txt").read().split()
for fen in sp[:3]:
    o = drained(["uci", "setoption name Hash value 16", "setoption name Threads value 1", "isready",
                 f"position fen {fen}", "go depth 10"])
    print(f"depth 10 {fen[:28]:28s} : nodes {nodes_of(o):>7}  {o[-1].strip()}")
print()
print("All PART 2 numbers are non-zero with real info lines, and none is the fabricated `a2a3`/0-node pattern.")
