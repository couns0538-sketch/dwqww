#!/usr/bin/env python3
"""job47 : build a VALIDATED threefold shuffle for each root, then run the breadth test.

The shuffle is derived per root by search: enumerate short move sequences that return the SAME position (same piece
placement, same side to move, same castling/ep rights) with no captures and no pawn moves, repeat the cycle until the
root has occurred three times. Nothing is hand-typed — that is what cost me a retracted finding in job 44.

Prints the validated cycle for each root, then the measurement.
"""
import re, subprocess, sys, os, itertools
import chess

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
BASE = os.path.expanduser("~/build/forge")
PC = os.path.expanduser("~/pcbuild/forge")

ROOTS = [
    ("R1  rook d5, kings b8/a1", "1K6/8/8/3R4/8/8/8/k7 w - - 0 1"),
    ("R2  rook a1, kings b3/h1", "8/8/8/8/8/1K6/8/R6k w - - 0 1"),
    ("R3  rook c1, kings a1/h8", "7k/8/8/8/8/8/8/K1R5 w - - 0 1"),
]


def poskey(b):
    f = b.fen().split(' ')
    return ' '.join(f[:2] + f[3:4])   # placement + side + castling (ep ignored: none here)


def find_cycle(root_fen, max_plies=6):
    """Find a short sequence returning to the ROOT position, no captures, no pawns, non-checking."""
    root = chess.Board(root_fen)
    rk = poskey(root)
    for n in range(2, max_plies + 1, 2):
        for seq in itertools.product(range(1), repeat=0):
            pass
        # depth-limited DFS over legal moves
        found = []

        def dfs(b, path):
            if found:
                return
            if len(path) == n:
                if poskey(b) == rk:
                    found.append(list(path))
                return
            for m in b.legal_moves:
                if b.is_capture(m):
                    continue
                b.push(m)
                if not b.is_check() and poskey(b) != rk or len(path) + 1 == n:
                    dfs(b, path + [m.uci()])
                b.pop()

        dfs(root, [])
        if found:
            return found[0]
    return None


print("== fixture construction: a validated cycle per root, no hand-typed moves ==")
cycles = {}
for label, fen in ROOTS:
    cyc = find_cycle(fen)
    if cyc is None:
        print("%-30s NO CYCLE FOUND within 6 plies -> root EXCLUDED" % label)
        continue
    b = chess.Board(fen)
    for mv in cyc:
        m = chess.Move.from_uci(mv)
        assert m in b.legal_moves, ("cycle illegal", mv)
        b.push(m)
    if poskey(b) != poskey(chess.Board(fen)):
        print("%-30s cycle does not return to root -> EXCLUDED" % label)
        continue
    seq = cyc * 2
    b = chess.Board(fen)
    occ = {poskey(b): 1}
    for i, mv in enumerate(seq, 1):
        m = chess.Move.from_uci(mv)
        assert m in b.legal_moves, ("illegal at ply %d: %s" % (i, mv))
        b.push(m)
        k = poskey(b)
        occ[k] = occ.get(k, 0) + 1
    n = occ[poskey(chess.Board(fen))]
    ok = n == 3
    print("%-30s cycle %-22s plies=%d | root occurrences=%d %s" % (
        label, " ".join(cyc), len(seq), n, "OK" if ok else "WRONG COUNT -> EXCLUDED"))
    if ok:
        cycles[label] = (fen, " ".join(seq))
print()


def proc(exe):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    opts = set()
    p.stdin.write("uci\n"); p.stdin.flush()
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died")
        s = l.strip()
        if s.startswith("option name "):
            opts.add(s.split("option name ")[1].split(" type ")[0])
        if s == "uciok":
            break
    if "OwnBook" in opts:
        p.stdin.write("setoption name OwnBook value false\n"); p.stdin.flush()
    p.stdin.write("setoption name Threads value 1\nsetoption name Hash value 16\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    return p


def go(p, fen, moves, depth):
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen %s%s\n" % (fen, (" moves " + moves) if moves else "")); p.stdin.flush()
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
            last = (m.group(2), int(m.group(3)), int(m.group(4)))
        if s.startswith("bestmove"):
            return last, s.split()[1]


print("== measurement ==")
print("| root | build/step | score | nodes | move |")
print("|---|---|---|---|---|")
p = proc(BASE)
picks = {}
for label, (fen, seq) in cycles.items():
    (kind, val, nodes), bm = go(p, fen, seq, 12)
    picks[label] = bm
    print("| %s | base on root | %s %d | %d | %s |" % (label, kind, val, nodes, bm))
p.stdin.write("quit\n"); p.stdin.flush()

p = proc(PC)
for label, (fen, seq) in cycles.items():
    (kind, val, nodes), bm = go(p, fen, seq, 16)
    print("| %s | PC on ROOT (control) | %s %d | %d | %s |" % (label, kind, val, nodes, bm))
    b = chess.Board(fen)
    for mv in seq.split():
        b.push(chess.Move.from_uci(mv))
    pm = picks[label]
    assert chess.Move.from_uci(pm) in b.legal_moves, ("base move illegal", pm)
    b.push(chess.Move.from_uci(pm))
    (kind2, val2, nodes2), bm2 = go(p, b.fen(), None, 16)
    print("| %s | PC AFTER base's %s | %s %d | %d | %s |" % (label, pm, kind2, val2, nodes2, bm2))
p.stdin.write("quit\n"); p.stdin.flush()
try:
    p.wait(timeout=10)
except Exception:
    p.kill()
