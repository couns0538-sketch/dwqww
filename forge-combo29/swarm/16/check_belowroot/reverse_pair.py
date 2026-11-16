#!/usr/bin/env python3
"""reverse_pair.py EXE OUT.txt : the four searches behind S-F12, as a committed script.

Runs the probe position and its colour mirror under two builds (pass each as EXE with a label):
  depth 2 with the full-window root, and depth 1 with the base root,
every search in a fresh process after `ucinewgame`, OwnBook false.
A build without the FullWindowRoot option is reported as such rather than silently treated as ON.
"""
import re
import subprocess
import sys
import time

import chess

FEN = "R7/8/8/5p1p/5K1P/1kpr2n1/8/8 b - - 0 1"
MIR = chess.Board(FEN).mirror().fen()


class Missing(Exception):
    pass


def search(exe, fen, depth, fullwindow):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def to(tok, lim=180):
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

    send("uci"); to("uciok", 15)
    send("isready"); to("readyok", 15)
    send("setoption name Threads value 1")  # swarm rule: scores are Threads 1
    send("isready"); to("readyok", 15)
    send("setoption name OwnBook value false")
    send("isready"); to("readyok", 15)
    if fullwindow:
        send("setoption name FullWindowRoot value true")
        send("isready")
        got, ok = to("readyok", 15)
        if not ok or any("unknown option" in l.lower() or "invalid value" in l.lower() for l in got):
            raise Missing("this build has no FullWindowRoot option")
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
    nodes = score = None
    for l in lines:
        m = re.search(rf"^info depth {depth} .*score (cp|mate) (-?\d+) nodes (\d+)", l)
        if m:
            score = f"{m.group(1)} {m.group(2)}"
            nodes = int(m.group(3))
    if nodes is None:
        raise Missing(f"no depth-{depth} info line with nodes")
    return nodes, score


def main(builds):
    out = [f"position {FEN}", f"mirror   {MIR}",
           "cold discipline: fresh process, ucinewgame before every search, OwnBook false", ""]
    for label, exe in builds:
        for depth, fw in ((2, True), (1, False)):
            tag = f"{label:10s} depth {depth} fullwindow={str(fw):5s}"
            try:
                na, sa = search(exe, FEN, depth, fw)
                nb, sb = search(exe, MIR, depth, fw)
                line = (f"{tag} | A {na:5d} nodes {sa:10s} | mirror {nb:5d} nodes {sb:10s} | "
                        f"equal {na == nb}")
            except Missing as exc:
                line = f"{tag} | NOT MEASURED: {exc}"
            out.append(line)
            print(line)
    text = "\n".join(out) + "\n"
    with open(sys.argv[2], "w") as fh:
        fh.write(text) if False else None
    return text


if __name__ == "__main__":
    builds = [(f"build{i}", e) for i, e in enumerate(sys.argv[3:], 1)]
    text = main(builds)
    with open(sys.argv[2], "w") as fh:
        fh.write(text + "\n")
