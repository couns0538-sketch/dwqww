#!/usr/bin/env python3
"""cold_depth1.py EXE OUT.txt : does cold-per-search (ucinewgame before every search) plus a full-window root
restore depth-1 node symmetry, and at what depth does it start to fail?

This follows seat 06's S-F19 (state is carried WITHIN a single search, not across searches) and my S-F8
(full-window root does not restore symmetry). It asks the narrow question the pair raised: at the SHALLOWEST
depth, with both the root alpha removed and the process reset each time, do the node counts match?
"""
import re
import subprocess
import sys
import time

import chess

EXE, OUT = sys.argv[1], sys.argv[2]
FEN = "R7/8/8/5p1p/5K1P/1kpr2n1/8/8 b - - 0 1"
MIR = chess.Board(FEN).mirror().fen()


class Missing(Exception):
    pass


def search(fen, depth, fw):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def to(tok, lim=120):
        out = []
        dl = time.monotonic() + lim
        while time.monotonic() < dl:
            l = p.stdout.readline()
            if not l:
                return out, False
            l = l.rstrip("\n")
            out.append(l)
            if l.strip().startswith(tok):
                return out, True
        return out, False

    # COLD: ucinewgame before the search, as seat 10's rule allows
    send("uci"); to("uciok", 15)
    send("isready"); to("readyok", 15)
    send("setoption name OwnBook value false")
    send("isready"); to("readyok", 15)
    if fw:
        send("setoption name FullWindowRoot value true")
        send("isready")
        got, ok = to("readyok", 15)
        if not ok or any("unknown option" in l.lower() for l in got):
            raise Missing("FullWindowRoot not accepted by this build")
    send("ucinewgame")
    send("isready"); to("readyok", 15)
    send("position fen " + fen)
    send("isready"); to("readyok", 15)
    send(f"go depth {depth}")
    lines, ok = to("bestmove", 300)
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    if not ok:
        raise Missing(f"no bestmove at depth {depth}")
    nodes = score = best = None
    for l in lines:
        if l.startswith("bestmove"):
            best = l.split()[1]
        m = re.search(rf"^info depth {depth} .*score (cp|mate) (-?\d+) nodes (\d+)", l)
        if m:
            score = f"{m.group(1)} {m.group(2)}"
            nodes = int(m.group(3))
    if nodes is None:
        raise Missing(f"no depth-{depth} info line with nodes")
    return best, score, nodes


out = [f"position  {FEN}", f"mirror    {MIR}", "every search: fresh process, ucinewgame before it", ""]
for depth in (1, 2, 3):
    for fw in (False, True):
        a = search(FEN, depth, fw)
        b = search(MIR, depth, fw)
        mv = chess.Move.from_uci(b[0]) if b[0] and b[0] != "0000" else None
        back = chess.Move(mv.from_square ^ 56, mv.to_square ^ 56, mv.promotion).uci() if mv else None
        line = (f"depth {depth} fullwindow={str(fw):5s} | A {a[0]} {a[1]} nodes {a[2]:6d} | "
                f"mirror {b[0]} {b[1]} nodes {b[2]:6d} | nodes equal {a[2] == b[2]} "
                f"score equal {a[1] == b[1]} bm equal {a[0] == back}")
        out.append(line)
        print(line)
text = "\n".join(out) + "\n"
with open(OUT, "w") as fh:
    fh.write(text)
