#!/usr/bin/env python3
"""terminal_root_probe.py EXE FEN -- at a TERMINAL root (checkmate or stalemate), run several go commands and
print, for each: how many info lines came back, the deepest depth reported, the total nodes reported, the
score, and the wall time. This measures whether the engine loops on depth instead of stopping.
"""
import re
import subprocess
import sys
import time

EXE = sys.argv[1]
FEN = sys.argv[2]
GOS = sys.argv[3:] or ["go depth 1", "go depth 5", "go depth 64", "go nodes 100", "go movetime 50",
                       "go infinite"]
S14 = ["setoption name Threads value 1", "setoption name Hash value 16"]


def run(go, limit=20):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    send("uci")
    send("isready")
    for o in S14:
        send(o); send("isready")
    send("ucinewgame"); send("isready")
    send(f"position fen {FEN}"); send("isready")
    t0 = time.monotonic()
    send(go)
    lines = []
    best = None
    deadline = time.time() + limit
    while time.time() < deadline:
        line = p.stdout.readline()
        if line == "":
            break
        line = line.rstrip("\n")
        lines.append(line)
        if line.startswith("bestmove"):
            best = line
            break
    wall = time.monotonic() - t0
    if best is None:
        send("stop")
        while True:
            line = p.stdout.readline()
            if line == "":
                break
            line = line.rstrip("\n")
            lines.append(line)
            if line.startswith("bestmove"):
                best = line
                break
            if time.time() > deadline + 5:
                break
        wall = time.monotonic() - t0
        timed_out = True
    else:
        timed_out = False
    send("quit")
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    pv = [l for l in lines if re.search(r"\binfo\b.*\bpv\b", l)]
    depths = [int(m.group(1)) for l in pv for m in [re.search(r"depth (\d+)", l)] if m]
    nodes = [int(m.group(1)) for l in pv for m in [re.search(r"\bnodes (\d+)", l)] if m]
    score = None
    if pv:
        m = re.search(r"score (mate|cp) (-?\d+)", pv[-1])
        score = f"{m.group(1)} {m.group(2)}" if m else "?"
    return dict(go=go, n_info=len(pv), max_depth=max(depths) if depths else None,
                total_nodes=sum(nodes), last_nodes=nodes[-1] if nodes else None,
                score=score, best=best, wall=round(wall, 2), timed_out=timed_out)


print(f"exe: {EXE}")
print(f"fen: {FEN}")
print(f"{'go':18s} {'info lines':>10s} {'max depth':>9s} {'sum nodes':>12s} {'last nodes':>10s} "
      f"{'score':>9s} {'wall s':>7s} bestmove")
for go in GOS:
    r = run(go)
    print(f"{r['go']:18s} {r['n_info']:10d} {str(r['max_depth']):>9s} {r['total_nodes']:12d} "
          f"{str(r['last_nodes']):>10s} {str(r['score']):>9s} {r['wall']:7.2f} {r['best']}")
