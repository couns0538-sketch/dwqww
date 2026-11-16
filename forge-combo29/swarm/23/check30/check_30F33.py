#!/usr/bin/env python3
"""check_30F33.py : independent check of the deep lone-king mate failures (seat 30's 30-F33/F34/F38).

Claim: on six lone-king boards where a mate in 5 plies exists, the BASE tree at `go depth 24` does NOT report a
mate (it gives a cp score instead), while the PC r15 build does.

My own harness: fresh process per line, `ucinewgame` + `isready` before each search, Threads 1, Hash 16, stdout
drained to bestmove (19-F12), and the engine's own `mate` line read only from a real info line. I also PROVE the
mate distance independently with python-chess rather than trusting the claim's "mate_plies 5".

Settings: defaults (no setoption) and S14, because 30-F38 says the failure is settings-independent.
"""
import re
import subprocess
import sys

import chess

BASE = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/build/forge"
PC = sys.argv[2] if len(sys.argv) > 2 else "/home/ubuntu/pcbuild/forge"
DEPTH = int(sys.argv[3]) if len(sys.argv) > 3 else 24

FENS = [
    "6k1/8/7R/2K5/8/8/8/8 w - - 0 1",
    "7K/5k2/8/4R3/8/8/8/8 w - - 0 1",
    "8/3K4/8/8/8/7k/3R4/8 w - - 0 1",
    "4k2K/8/8/1R6/8/8/8/8 w - - 0 1",
    "8/8/8/8/8/R7/7K/3k4 w - - 0 1",
    "8/8/8/6k1/8/8/5K2/1Q6 w - - 0 1",
]

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+)")


def search(exe, fen, depth, opts):
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
    p.stdin.write("position fen %s\n" % fen); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write("go depth %d\n" % depth); p.stdin.flush()
    last = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died in search")
        s = l.strip()
        m = INFO.match(s)
        if m:
            last = (int(m.group(1)), m.group(2), int(m.group(3)))
        if s.startswith("bestmove"):
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    return last


def mate_in_plies(fen, max_plies=7):
    """exhaustive: is there a forced mate for the side to move in <= max_plies, and what is the shortest?"""
    def mate_for(board, plies):
        if plies <= 0:
            return False
        for mv in board.legal_moves:
            board.push(mv)
            if board.is_checkmate():
                board.pop()
                return True
            if plies >= 3:
                # opponent must have no move that avoids mate
                all_lose = True
                for om in list(board.legal_moves):
                    board.push(om)
                    ok = mate_for(board, plies - 2)
                    board.pop()
                    if not ok:
                        all_lose = False
                        break
                board.pop()
                if all_lose:
                    return True
                continue
            board.pop()
        return False

    b = chess.Board(fen)
    for plies in range(1, max_plies + 1, 2):
        if mate_for(b, plies):
            return plies
    return None


S14 = [l.strip() for l in open("/agent/repos/dwqww/forge-combo29/swarm/23/check05/s14_opts.txt")
       if l.strip() and not l.startswith("#")]

print("deep lone-king mate check — fresh process per line, Threads 1, Hash 16, depth %d" % DEPTH)
print("base %s" % BASE)
print("pc   %s" % PC)
print()
print("| # | fen | python-chess mate in | base defaults | base S14 | PC defaults | PC S14 |")
print("|---|---|---|---|---|---|---|")
rows = []
for i, fen in enumerate(FENS, 1):
    plies = mate_in_plies(fen)
    bt = search(BASE, fen, DEPTH, [])
    bs = search(BASE, fen, DEPTH, S14)
    pt = search(PC, fen, DEPTH, [])
    ps = search(PC, fen, DEPTH, S14)

    def fmt(r):
        return "no info" if r is None else "%s %d" % (r[1], r[2])

    print("| %d | %s | %s | %s | %s | %s | %s |"
          % (i, fen, plies, fmt(bt), fmt(bs), fmt(pt), fmt(ps)))
    rows.append({"fen": fen, "plies": plies, "base_defaults": bt, "base_s14": bs,
                 "pc_defaults": pt, "pc_s14": ps})

def reports_mate(r):
    return r is not None and r[1] == "mate"

base_fail = sum(1 for r in rows if r["plies"] and not reports_mate(r["base_defaults"]))
base_fail_s14 = sum(1 for r in rows if r["plies"] and not reports_mate(r["base_s14"]))
pc_ok = sum(1 for r in rows if r["plies"] and reports_mate(r["pc_defaults"]))
pc_ok_s14 = sum(1 for r in rows if r["plies"] and reports_mate(r["pc_s14"]))
print()
print("boards where a mate exists (by my own python-chess search): %d of %d"
      % (sum(1 for r in rows if r["plies"]), len(rows)))
print("base FAILS to report mate (defaults): %d of %d" % (base_fail, len(rows)))
print("base FAILS to report mate (S14):      %d of %d" % (base_fail_s14, len(rows)))
print("PC reports mate (defaults):           %d of %d" % (pc_ok, len(rows)))
print("PC reports mate (S14):                %d of %d" % (pc_ok_s14, len(rows)))
