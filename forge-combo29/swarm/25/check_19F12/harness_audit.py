#!/usr/bin/env python3
"""harness_audit.py EXE : proves whether MY harness pattern is safe, with hard timeouts.

Three patterns, each bounded so a hang is reported rather than waited on:
  P1 pipelined `go` then `quit` on one write, stdin closed  -> 19-F12's failure mode
  P2 stdin held open, read until `bestmove`, then quit       -> my run_pv.py
  P3 stdin held open, quit after a fixed sleep               -> my bash probe scripts
For each: count of info lines, last depth/nodes, and the bestmove.
"""
import subprocess
import sys
import time

EXE = sys.argv[1]


def read_until(p, pred, deadline):
    lines = []
    while time.monotonic() < deadline:
        line = p.stdout.readline()
        if not line:
            return lines, False
        line = line.rstrip("\n")
        lines.append(line)
        if pred(line):
            return lines, True
    return lines, False


def report(tag, infos, best, timed_out):
    nodes = None
    last = infos[-1] if infos else "(none)"
    if infos:
        for tok in infos[-1].split():
            pass
        parts = infos[-1].split()
        if "nodes" in parts:
            nodes = parts[parts.index("nodes") + 1]
    print(f"{tag}: info_lines={len(infos)} nodes={nodes} bestmove={best} timeout={timed_out}")
    print(f"    last info: {last[:110]}")


def p1():
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    for c in ["uci", "isready", "ucinewgame", "isready"]:
        p.stdin.write(c + "\n")
        p.stdin.flush()
    p.stdin.write("position startpos\ngo depth 12\nquit\n")
    p.stdin.flush()
    p.stdin.close()
    infos, best = [], None
    deadline = time.monotonic() + 20
    lines, _ = read_until(p, lambda l: l.startswith("bestmove"), deadline)
    for l in lines:
        if l.startswith("info depth"):
            infos.append(l)
        elif l.startswith("bestmove"):
            best = l
    timed_out = best is None
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        p.kill()
    report("P1 pipelined go+quit, stdin closed", infos, best, timed_out)


def p2():
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    for c in ["uci", "isready", "ucinewgame", "isready"]:
        p.stdin.write(c + "\n")
        p.stdin.flush()
    p.stdin.write("position startpos\ngo depth 12\n")
    p.stdin.flush()
    infos, best = [], None
    deadline = time.monotonic() + 60
    lines, _ = read_until(p, lambda l: l.startswith("bestmove"), deadline)
    for l in lines:
        if l.startswith("info depth"):
            infos.append(l)
        elif l.startswith("bestmove"):
            best = l
    timed_out = best is None
    p.stdin.write("quit\n")
    p.stdin.flush()
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        p.kill()
    report("P2 read-until-bestmove, stdin open  (MY HARNESS)", infos, best, timed_out)


def p3():
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    for c in ["uci", "isready", "ucinewgame", "isready"]:
        p.stdin.write(c + "\n")
        p.stdin.flush()
    p.stdin.write("position startpos\ngo depth 12\n")
    p.stdin.flush()
    time.sleep(2)
    p.stdin.write("quit\n")
    p.stdin.flush()
    infos, best = [], None
    deadline = time.monotonic() + 20
    lines, _ = read_until(p, lambda l: l.startswith("bestmove"), deadline)
    for l in lines:
        if l.startswith("info depth"):
            infos.append(l)
        elif l.startswith("bestmove"):
            best = l
    timed_out = best is None
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        p.kill()
    report("P3 sleep-then-quit, stdin open  (my bash probes)", infos, best, timed_out)


p1()
p2()
p3()
