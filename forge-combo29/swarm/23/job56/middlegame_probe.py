#!/usr/bin/env python3
"""job56c : extend the castling contrast to a MIDDLEGAME board with pieces.

Take a real sampled position (castling rights present), find a repetition cycle, and send it:
  X1 as-is (rights present)   -> predict SEARCHES
  X2 identical but castling field set to '-'  -> predict BAILS
Everything else identical including the cycle. If X2 bails while X1 searches, the castling result is not an artefact of
the sparse endgame that produced it.
"""
import re, subprocess, os, sys
import chess

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
BASE = os.path.expanduser("~/build/forge")


def pk(b):
    f = b.fen().split(' ')
    return ' '.join(f[:2] + f[3:4])


def find_cycle(fen, maxlen=4):
    root = chess.Board(fen)
    target = pk(root)
    found = []

    def dfs(b, path):
        if found:
            return
        if len(path) == maxlen:
            if pk(b) == target:
                found.append(list(path))
            return
        for m in b.legal_moves:
            if b.is_capture(m):
                continue
            b.push(m)
            if not b.is_check():
                dfs(b, path + [m.uci()])
            b.pop()
            if found:
                return

    dfs(root, [])
    return found[0] if found else None


def conn():
    p = subprocess.Popen([BASE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    p.stdin.write("uci\n"); p.stdin.flush()
    o = set()
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died")
        s = l.strip()
        if s.startswith("option name "):
            o.add(s.split("option name ")[1].split(" type ")[0])
        if s == "uciok":
            break
    if "OwnBook" in o:
        p.stdin.write("setoption name OwnBook value false\n"); p.stdin.flush()
    p.stdin.write("setoption name Threads value 1\nsetoption name Hash value 16\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    return p


def go(p, fen, moves, depth=10):
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen %s%s\n" % (fen, (" moves " + " ".join(moves)) if moves else "")); p.stdin.flush()
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


fens = [l.strip() for l in open('../job1/R_2301.fens') if l.strip()]
sample = [fens[i] for i in range(0, 400 * 12, 400)][:12]
p = conn()
print("| pos | castling | cycle | root occ | nodes | score | verdict |")
print("|---|---|---|---|---|---|---|")
done = 0
for i, fen0 in enumerate(sample, 1):
    b0 = chess.Board(fen0)
    if not b0.fen().split(' ')[2] or b0.fen().split(' ')[2] == '-':
        continue
    cyc = find_cycle(fen0)
    if not cyc:
        continue
    for label, fen in (("rights", fen0), ("stripped", ' '.join(b0.fen().split(' ')[:2] + ['-'] + b0.fen().split(' ')[3:]))):
        bb = chess.Board(fen)
        c = {pk(bb): 1}
        okc = True
        for mv in cyc * 2:
            m = chess.Move.from_uci(mv)
            if m not in bb.legal_moves:
                okc = False
                break
            bb.push(m)
            k = pk(bb)
            c[k] = c.get(k, 0) + 1
        if not okc:
            print("| %d | %s | **cycle illegal after stripping** | - | - | - | EXCLUDED |" % (i, label))
            continue
        rootc = c.get(pk(chess.Board(fen)), 0)
        (kind, val, nodes), bm = go(p, fen, cyc * 2, 10)
        print("| %d | %s | %s | %d | %d | %s %d | %s |" % (
            i, label, " ".join(cyc), rootc, nodes, kind, val, "**BAIL**" if nodes == 0 else "searched"))
        sys.stdout.flush()
    done += 1
    if done >= 3:
        break
p.stdin.write("quit\n"); p.stdin.flush()
print()
print("positions tested: %d (each with rights present and stripped, same cycle)" % done)
