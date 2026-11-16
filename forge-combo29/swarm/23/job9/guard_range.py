#!/usr/bin/env python3
"""guard_range.py : the guard's useful depth range, depths 12..16, ONE board, two settings.

Requested: "at which depths between 12 and 16 does the unguarded search still report a wrong mate distance on
that board, and does the guarded one stay correct throughout."

Board: seat 01's S-F49 board, used unchanged: `8/8/8/8/4k3/8/8/8 ...` NO — their board is
  `8/8/8/8/8/7P/8/6Q1` family; the exact board from their finding text is used verbatim below.
Two settings, both on the PC r15 build, Threads 1, Hash 16, S14 as the base regime:
  guard OFF  = S14
  guard ON   = S14 + `MateAlphaGuard true`
Every run is a FRESH PROCESS with `ucinewgame` before the search, and every command is drained to `bestmove`
(19-F12). For each (depth, setting) the printed PV is REPLAYED with python-chess to count its plies and to test
whether it really ends in checkmate, so "wrong mate distance" is a measurement, not a reading of the score.
"""
import re
import subprocess
import sys

import chess

EXE = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/pcbuild/forge"
S14FILE = sys.argv[2] if len(sys.argv) > 2 else "s14_opts.txt"
OUT = sys.argv[3] if len(sys.argv) > 3 else "guard_range.out"

# seat 01's S-F48/S-F49 board, exactly as published
FEN = "8/3K4/7P/8/8/7k/8/6Q1 w - - 100 1"
# the same board with the counter dropped to 0 (their method for reading the true distance)
FEN0 = "8/3K4/7P/8/8/7k/8/6Q1 w - - 0 1"
DEPTHS = [12, 13, 14, 15, 16]

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?(?: pv (.*))?$")


def replay(fen, pv):
    b = chess.Board(fen)
    n = 0
    for u in pv.split():
        try:
            m = chess.Move.from_uci(u)
        except ValueError:
            return n, False, "bad uci"
        if m not in b.legal_moves:
            return n, False, "illegal"
        b.push(m)
        n += 1
    return n, b.is_checkmate(), None


def run(fen, depth, guard):
    opts = [l.strip() for l in open(S14FILE) if l.strip() and not l.startswith("#")]
    if guard:
        opts = opts + ["setoption name MateAlphaGuard value true"]
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
            raise RuntimeError("STOP: option %r not in the engine's uci list" % nm)
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
            last = (int(m.group(1)), m.group(2), int(m.group(3)), m.group(4) or "", s)
        if s.startswith("bestmove"):
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    if last is None:
        return None
    d, kind, val, pv, raw = last
    nm = re.search(r"nodes (\d+)", raw)
    plies, mate, err = replay(fen, pv)
    return {"depth": d, "kind": kind, "score": val, "pv": pv, "pv_plies": plies,
            "pv_mate": mate, "err": err, "nodes": int(nm.group(1)) if nm else None}


def truth():
    """the true distance, from the counter-0 board at high depth with the guard on and off."""
    out = {}
    for guard in (False, True):
        r = run(FEN0, 20, guard)
        out[guard] = r
    return out


lines = []
lines.append("BOARD (seat 01's S-F48/S-F49 board, unchanged): %s" % FEN)
lines.append("counter-0 twin: %s" % FEN0)
lines.append("build: PC r15, Threads 1, Hash 16, S14 (+ MateAlphaGuard true for guard ON)")
lines.append("")
tr = truth()
for guard in (False, True):
    r = tr[guard]
    lines.append("truth probe, counter 0, depth 20, guard %s: %s %d, PV %d plies, ends in mate %s"
                 % ("ON" if guard else "OFF", r["kind"], r["score"], r["pv_plies"], r["pv_mate"]))
lines.append("")
lines.append("| depth | guard | score | mate distance promised (plies) | PV plies | PV ends in mate | nodes |")
lines.append("|---|---|---|---|---|---|---|")
rows = []
for d in DEPTHS:
    for guard in (False, True):
        r = run(FEN, d, guard)
        if r is None:
            lines.append("| %d | %s | NO INFO LINE | - | - | - | - |" % (d, "ON" if guard else "OFF"))
            continue
        if r["kind"] == "mate":
            need = 2 * r["score"] - 1 if r["score"] > 0 else 2 * abs(r["score"])
        else:
            need = None
        lines.append("| %d | %s | %s %d | %s | %d | %s | %s |" %
                     (d, "ON" if guard else "OFF", r["kind"], r["score"],
                      need if need else "-", r["pv_plies"], r["pv_mate"], r["nodes"]))
        rows.append((d, guard, r))

text = "\n".join(lines) + "\n"
open(OUT, "w").write(text)
print(text)

# the specific question, answered in one line
wrong_off = [d for d, g, r in rows if not g and r["kind"] == "mate" and not r["pv_mate"]]
wrong_on = [d for d, g, r in rows if g and r["kind"] == "mate" and not r["pv_mate"]]
print("UNGUARDED reports a mate distance its own PV does not deliver at depths: %s" % (wrong_off or "none"))
print("GUARDED  reports a mate distance its own PV does not deliver at depths: %s" % (wrong_on or "none"))
open(OUT, "a").write("\nUNGUARDED wrong at depths: %s\nGUARDED wrong at depths: %s\n"
                     % (wrong_off or "none", wrong_on or "none"))
