#!/usr/bin/env python3
"""guard_range2.py : the guard on/off depth comparison on the CORRECT board.

Board mismatch that caused the earlier confusion, recorded here so it cannot repeat:
  S-F49's DEPTH TABLE board  = 8/8/1p6/8/p3p3/8/2Kpk3/8 w   (pawn-and-piece endgame; -27 pawns plausible)
  S-F48's counter-reset board = 8/3K4/7P/8/8/7k/8/6Q1 w - - 100 1   (Q vs bare king)
My previous job9 measured ONLY the S-F48 board, so its flat table says nothing about S-F49's depth table.
Every row below states its board.

Settings: PC r15 build, Threads 1, Hash 16, S14; guard ON = S14 + `setoption name MateAlphaGuard true`.
Fresh process per run, ucinewgame before each search, drained to bestmove (19-F12), PV replayed by python-chess.
"""
import re
import subprocess
import sys

import chess

EXE = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/pcbuild/forge"
S14FILE = sys.argv[2] if len(sys.argv) > 2 else "s14_opts.txt"
OUT = sys.argv[3] if len(sys.argv) > 3 else "guard_range2.out"

BOARD_SF49 = "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"
DEPTHS = [8, 10, 12, 14, 16]

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?(?: pv (.*))?$")


def replay(fen, pv):
    b = chess.Board(fen)
    n = 0
    for u in pv.split():
        try:
            m = chess.Move.from_uci(u)
        except ValueError:
            return n, False
        if m not in b.legal_moves:
            return n, False
        b.push(m)
        n += 1
    return n, b.is_checkmate()


def run(fen, depth, guard):
    chess.Board(fen)  # validity guard: a bad FEN must never be scored
    if not chess.Board(fen).is_valid():
        raise RuntimeError("REFUSING invalid FEN %r" % fen)
    opts = [l.strip() for l in open(S14FILE) if l.strip() and not l.startswith("#")]
    if guard:
        opts.append("setoption name MateAlphaGuard value true")
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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
            raise RuntimeError("STOP: option %r not in uci list" % nm)
        p.stdin.write(line + "\n"); p.stdin.flush()
        p.stdin.write("isready\n"); p.stdin.flush()
        while True:
            l2 = p.stdout.readline()
            if not l2:
                raise RuntimeError("died on option")
            if "unknown option" in l2 or "invalid value" in l2 or "ERROR" in l2:
                raise RuntimeError("STOP on %r" % l2.strip())
            if l2.strip() == "readyok":
                break
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
            last = (m.group(2), int(m.group(3)), m.group(4) or "", s)
        if s.startswith("bestmove"):
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    if last is None:
        return None
    kind, val, pv, raw = last
    nm = re.search(r"nodes (\d+)", raw)
    plies, mate = replay(fen, pv)
    return {"kind": kind, "score": val, "pv": pv, "pv_plies": plies, "pv_mate": mate,
            "nodes": int(nm.group(1)) if nm else None}


lines = ["|| board | depth | guard | score | mate distance promised (plies) | PV plies | PV ends in mate | nodes |",
         "|---|---|---|---|---|---|---|---|---|"]
rows = []
for d in DEPTHS:
    off = run(BOARD_SF49, d, False)
    on = run(BOARD_SF49, d, True)
    for guard, r in ((False, off), (True, on)):
        if r is None:
            lines.append("| %s | %d | %s | NO INFO LINE | - | - | - | - |"
                         % ("S-F49 endgame", d, "ON" if guard else "OFF"))
            continue
        need = None
        if r["kind"] == "mate":
            need = 2 * r["score"] - 1 if r["score"] > 0 else 2 * abs(r["score"])
        lines.append("| S-F49 endgame | %d | %s | %s %d | %s | %d | %s | %s |" %
                     (d, "ON" if guard else "OFF", r["kind"], r["score"],
                      need if need else "-", r["pv_plies"], r["pv_mate"], r["nodes"]))
        rows.append((d, guard, r))

text = "BOARD (S-F49's depth-table board): %s\n" % BOARD_SF49
text += "build: PC r15, Threads 1, Hash 16, S14 (+ MateAlphaGuard for guard ON)\n\n"
text += "\n".join(lines) + "\n"
open(OUT, "w").write(text)
print(text)

print("per-depth comparison (the pattern the coordinator asked about):")
for d in DEPTHS:
    off = next(r for dd, g, r in rows if dd == d and not g)
    on = next(r for dd, g, r in rows if dd == d and g)
    same = (off["kind"], off["score"], off["nodes"]) == (on["kind"], on["score"], on["nodes"])
    print("  depth %2d: OFF %s %d nodes %s | ON %s %d nodes %s -> %s"
          % (d, off["kind"], off["score"], off["nodes"], on["kind"], on["score"], on["nodes"],
             "IDENTICAL" if same else "DIFFERENT"))
