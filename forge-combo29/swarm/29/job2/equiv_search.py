#!/usr/bin/env python3
"""Equivalence on SEARCH OUTPUT, base vs patched.

For each FEN: uci, Hash 16, Threads 1, isready, position fen, go depth 10, then wait for `bestmove`
(no early `quit`: the UCI loop is asynchronous, so a piped `quit` cancels the search before it prints).
Collects every `info depth` line and the bestmove, and the node count of the last info line.
Prints one line per position and a summary that is pasted into the report.
"""
import subprocess, sys

TIME_FIELDS = {"nps", "time"}


def strip_volatile(line):
    """Drop the wall-clock fields (nps, time) that differ run to run; keep depth/score/nodes/hashfull/pv."""
    if not line:
        return line
    out, toks, skip = [], line.split(), False
    for t in toks:
        if skip:
            skip = False
            continue
        if t in TIME_FIELDS:
            skip = True
            continue
        out.append(t)
    return " ".join(out)

POS = "searchpos.txt"
DEPTH = 10


def run(exe, fen):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    cmds = ["uci", "setoption name Hash value 16", "setoption name Threads value 1", "isready",
            f"position fen {fen}", f"go depth {DEPTH}"]
    for c in cmds:
        p.stdin.write(c + "\n")
    p.stdin.flush()
    infos, best = [], None
    for line in p.stdout:
        line = line.rstrip("\n")
        if line.startswith("info depth"):
            infos.append(line)
        elif line.startswith("bestmove"):
            best = line
            break
    p.stdin.write("quit\n")
    p.stdin.flush()
    p.wait(timeout=60)
    return infos, best


fens = [l.strip() for l in open(POS) if l.strip()]
same = diff = 0
total_nodes = 0
for i, fen in enumerate(fens, 1):
    ai, ab = run(sys.argv[1], fen)
    bi, bb = run(sys.argv[2], fen)
    # compare the last info line (deepest) plus the bestmove; the whole block is compared too
    ok = ([strip_volatile(x) for x in ai] == [strip_volatile(x) for x in bi]) and (ab == bb)
    nodes = 0
    if ab:
        for tok, nxt in zip(ai[-1].split(), ai[-1].split()[1:] if ai else []):
            pass
    if ai:
        parts = ai[-1].split()
        if "nodes" in parts:
            nodes = int(parts[parts.index("nodes") + 1])
        total_nodes += nodes
    if ok:
        same += 1
    else:
        diff += 1
        print(f"DIFF {fen}")
        print(f"  base   : {ai[-1] if ai else '(none)'} | {ab}")
        print(f"  patched: {bi[-1] if bi else '(none)'} | {bb}")
    print(f"{i:3d} {'SAME' if ok else 'DIFF'} nodes={nodes:>9} {fen[:50]}")
print(f"\nsearch agreements: {same}   differences: {diff}   total nodes compared: {total_nodes}")
print(f"depth compared: {DEPTH}, all info lines compared verbatim (pv included)")
