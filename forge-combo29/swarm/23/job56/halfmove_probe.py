#!/usr/bin/env python3
"""job56d : vary ONLY the halfmove field on the three middlegame boards (M1, M4, M7).

M7 originally carried halfmove 1 while M1/M4 carried 0, so the clock was a candidate confound. This holds board and
cycle fixed and sweeps the field.
"""
import re, subprocess, os, chess
INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
BASE = os.path.expanduser("~/build/forge")
CYCLES = {1: 'g8e7 d3a6 e7g8 a6d3', 4: 'a7c7 g8h6 c7a7 h6g8', 7: 'c4e5 h8g8 e5c4 g8h8'}


def pk(x):
    f = x.fen().split(' ')
    return ' '.join(f[:2] + f[3:4])


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


def go(p, fen, moves, d=10):
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen %s%s\n" % (fen, (" moves " + " ".join(moves)) if moves else "")); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write("go depth %d\n" % d); p.stdin.flush()
    last = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died")
        s = l.strip()
        m = INFO.match(s)
        if m:
            last = (m.group(2), int(m.group(3)), int(m.group(4)))
        if s.startswith("bestmove"):
            return last, s.split()[1]


fens = [l.strip() for l in open('../job1/R_2301.fens') if l.strip()]
sample = [fens[i] for i in range(0, 400 * 12, 400)][:12]
p = conn()
print("HYPOTHESIS: pos 7 carried halfmove 1 while 1 and 4 carried 0. Vary ONLY the halfmove field.")
print()
print("| pos | halfmove | root occ | nodes | verdict | bestmove |")
print("|---|---|---|---|---|---|")
for i in (1, 4, 7):
    parts = chess.Board(sample[i - 1]).fen().split(' ')
    for hm in (0, 1, 2):
        f = ' '.join(parts[:4] + [str(hm), parts[5]])
        bb = chess.Board(f)
        c = {pk(bb): 1}
        ok = True
        for mv in CYCLES[i].split() * 2:
            m = chess.Move.from_uci(mv)
            if m not in bb.legal_moves:
                ok = False
                break
            bb.push(m)
            c[pk(bb)] = c.get(pk(bb), 0) + 1
        if not ok:
            print("| %d | %d | **cycle illegal** | - | - | - |" % (i, hm))
            continue
        (k, v, n), bm = go(p, f, CYCLES[i].split() * 2, 10)
        print("| %d | %d | %d | %d | %s | %s |" % (i, hm, c.get(pk(chess.Board(f)), 0), n,
                                                   "**BAIL**" if n == 0 else "searched", bm))
p.stdin.write("quit\n"); p.stdin.flush()
