#!/usr/bin/env python3
"""short_sleep_test.py EXE : does `quit` DURING a still-running search fabricate a bestmove?

This is the case that matters for my bash probes: they sleep a fixed time and then quit. If a search
runs longer than the sleep, quit lands mid-search. Two cases:
  S1 quit at 0.5 s while a depth-30 search is still running  -> is the bestmove fabricated?
  S2 quit after bestmove already arrived                      -> safe by construction
For each: info lines received BEFORE the quit, the bestmove, and the nodes on the last info line.
"""
import subprocess
import sys
import time

EXE = sys.argv[1]


def run(tag, quit_after):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    p.stdin.write("uci\nisready\nucinewgame\nisready\n")
    p.stdin.flush()
    p.stdin.write("position startpos\ngo depth 30\n")
    p.stdin.flush()
    start = time.monotonic()
    infos = []
    best = None
    quit_sent = False
    while time.monotonic() - start < 60:
        if not quit_sent and time.monotonic() - start >= quit_after:
            p.stdin.write("quit\n")
            p.stdin.flush()
            quit_sent = True
        line = p.stdout.readline()
        if not line:
            break
        line = line.rstrip("\n")
        if line.startswith("info depth"):
            infos.append(line)
        if line.startswith("bestmove"):
            best = line
            break
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        p.kill()
    nodes = None
    if infos:
        parts = infos[-1].split()
        if "nodes" in parts:
            nodes = parts[parts.index("nodes") + 1]
    print(f"{tag}: quit_after={quit_after}s info_lines={len(infos)} last_nodes={nodes} bestmove={best}")
    if infos:
        print(f"    last info before quit: {infos[-1][:110]}")


run("S1 quit at 0.5 s, search still running", 0.5)
run("S2 quit at 3 s", 3.0)
