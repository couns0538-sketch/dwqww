#!/usr/bin/env python3
"""check_11SF1.py : independent check of seat 11's S-F1.

Claim: `position fen` reads only six tokens and the following loop silently discards any extra token, so a
malformed FEN with junk after the sixth field is ACCEPTED rather than refused.

Method: for each FEN, send a KNOWN position first (startpos, perft 1 = 20), then the test FEN, then `go perft 1`.
  - if the test FEN is REFUSED, the engine answers an `invalid FEN` line and keeps startpos -> perft 1 = 20.
  - if it is ACCEPTED, the board is the test board -> perft 1 is that board's own count.
A junk-suffixed FEN must be distinguishable from its clean twin: if both give the same non-20 count, the junk was
ignored and the position accepted (the claim); if the junk one is refused, the claim is wrong.

CONTROL: the same harness must show a REFUSAL working, which the known "too many squares" FEN provides.
"""
import re
import subprocess
import sys

EXE = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/build/forge"
OPTFILE = sys.argv[2] if len(sys.argv) > 2 else ""
FENS = [
    ("clean startpos-like", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    ("junk word after 6th", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 HELLO"),
    ("junk number after 6th", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 99"),
    ("junk gibberish", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 @@@ $$$"),
    ("junk on a mid-game FEN", "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3 JUNK"),
    ("mid-game clean twin", "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"),
    ("CONTROL too many squares", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNRQQ w KQkq - 0 1"),
]


def probe(exe, fen, opts):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    p.stdin.write("uci\n"); p.stdin.flush()
    names = set()
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died in uci")
        s = l.strip()
        if s.startswith("option name "):
            names.add(s.split("option name ")[1].split(" type ")[0])
        if s == "uciok":
            break
    for line in opts:
        nm = line.split("name ")[1].split(" value ")[0]
        if nm not in names:
            raise RuntimeError("STOP: %r not in uci list" % nm)
        p.stdin.write(line + "\n"); p.stdin.flush()
        p.stdin.write("isready\n"); p.stdin.flush()
        while p.stdout.readline().strip() != "readyok":
            pass
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position startpos\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write("position fen %s\n" % fen); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    bad = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died")
        s = l.strip()
        if "invalid FEN" in s:
            bad = s
        if s == "readyok":
            break
    p.stdin.write("go perft 1\n"); p.stdin.flush()
    nodes = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died in perft")
        s = l.strip()
        if s.startswith("nodes "):
            nodes = int(s.split()[1])
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    return bad, nodes


opts = []
if OPTFILE:
    opts = [x.strip() for x in open(OPTFILE) if x.strip() and not x.startswith("#")]

print("`position fen` with junk after the sixth field — base build, Threads 1, Hash 16")
print("startpos alone answers perft 1 = 20, so 20 means REFUSED and startpos kept")
print()
print("| case | invalid-FEN line? | perft 1 | reading |")
print("|---|---|---|---|")
for label, fen in FENS:
    bad, nodes = probe(EXE, fen, opts)
    if bad:
        reading = "REFUSED — startpos kept" if nodes == 20 else "REFUSED but board differs (?)"
    else:
        reading = "**ACCEPTED** (junk ignored)" if nodes == 20 else "accepted"
    print("| %s | %s | %s | %s |" % (label, "yes: " + bad if bad else "no", nodes, reading))
