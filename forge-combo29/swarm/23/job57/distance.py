#!/usr/bin/env python3
"""job57 : does the ROOT'S DISTANCE in the history decide the bail?

On M1 (bails at 0/4/8) and M7 (searches at 0/4/8), build move lists where the root occurs exactly 3 times at three
DIFFERENT spacings, using a distinct filler shuttle that never returns to the root. Every list validated (root count
== 3, ends at root) BEFORE the engine is asked.

Patterns: A = 0/4/8 (the standard), B = 0/8/16, C = 0/4/12.
Control: the same filler WITHOUT the final return (engine asked about a once-occurring filler position) must search.
"""
import re, subprocess, os, sys, itertools
import chess

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
BASE = os.path.expanduser("~/build/forge")

BOARDS = {
    "M1": ("rnbqkbnr/pppp3p/6p1/4pp2/7P/1P1BP3/P1PP1PP1/RNBQK1NR b KQkq - 0 4",
           "g8e7 d3a6 e7g8 a6d3"),
    "M7": ("rn1qkb1r/p2p1p2/1p2p3/2pP2pp/Q1N3P1/P1P1BP2/1P2P1K1/R4BNR w kq - 1 15",
           "c4e5 h8g8 e5c4 g8h8"),
}


def pk(b):
    f = b.fen().split(' ')
    return ' '.join(f[:2] + f[3:4])


def apply(fen, moves):
    b = chess.Board(fen)
    for mv in moves:
        m = chess.Move.from_uci(mv)
        if m not in b.legal_moves:
            return None
        b.push(m)
    return b


def find_filler(fen, cycle, avoid_root=True):
    """A 4-ply shuttle that returns to a NON-root position (so it repeats without touching the root)."""
    root = chess.Board(fen)
    rk = pk(root)
    start = apply(fen, cycle)
    if start is None:
        return None
    sk = pk(start)
    found = []

    def dfs(b, path):
        if found:
            return
        if len(path) == 4:
            if pk(b) == sk and sk != (rk if avoid_root else None):
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

    dfs(start, [])
    return found[0] if found else None


def build(fen, cycle, filler, pattern):
    """Return a move list in which the root occurs exactly 3x with the requested spacing, ending at the root."""
    cyc = cycle.split()
    fil = filler
    if pattern == "A":
        seq = cyc * 2
    elif pattern == "B":
        seq = cyc + fil + fil + cyc
    elif pattern == "C":
        seq = cyc + fil + cyc
    else:
        raise ValueError(pattern)
    b = apply(fen, seq)
    if b is None:
        return None, None
    c = {}
    bb = chess.Board(fen)
    c[pk(bb)] = 1
    for mv in seq:
        bb.push(chess.Move.from_uci(mv))
        c[pk(bb)] = c.get(pk(bb), 0) + 1
    rootcount = c.get(pk(chess.Board(fen)), 0)
    ends_at_root = pk(bb) == pk(chess.Board(fen))
    return seq, (rootcount, ends_at_root)


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


p = conn()
print("| board | pattern | list length | root count | ends at root | nodes | verdict |")
print("|---|---|---|---|---|---|---|")
results = {}
for name, (fen, cycstr) in BOARDS.items():
    cyc = cycstr.split()
    fil = find_filler(fen, cyc)
    if not fil:
        print("| %s | - | - | - | - | - | **NO FILLER FOUND** |" % name)
        continue
    for pattern in ("A", "B", "C"):
        seq, chk = build(fen, cycstr, fil, pattern)
        if seq is None or chk is None:
            print("| %s | %s | - | - | - | - | **NOT CONSTRUCTIBLE** |" % (name, pattern))
            continue
        rc, ends = chk
        if rc != 3 or not ends:
            print("| %s | %s | %d | %d | %s | - | EXCLUDED (assert failed) |" % (name, pattern, len(seq), rc, ends))
            continue
        (k, v, n), bm = go(p, fen, seq, 10)
        results[(name, pattern)] = n
        print("| %s | %s | %d | %d | %s | %d | %s |" % (name, pattern, len(seq), rc, ends, n,
                                                        "**BAIL**" if n == 0 else "searched"))
        sys.stdout.flush()
    # control: filler only, ending on a filler position (root occurs once)
    if fil:
        seq2 = cyc + fil
        b2 = apply(fen, seq2)
        if b2 is not None:
            c2 = {}
            bb = chess.Board(fen); c2[pk(bb)] = 1
            for mv in seq2:
                bb.push(chess.Move.from_uci(mv)); c2[pk(bb)] = c2.get(pk(bb), 0) + 1
            rc2 = c2.get(pk(chess.Board(fen)), 0)
            (k, v, n), bm = go(p, fen, seq2, 10)
            print("| %s | CONTROL filler | %d | %d | no | %d | %s |" % (name, len(seq2), rc2, n,
                                                                        "**BAIL (confound!)**" if n == 0 else "searched"))
p.stdin.write("quit\n"); p.stdin.flush()
try:
    p.wait(timeout=10)
except Exception:
    p.kill()

print()
for name in BOARDS:
    got = [results.get((name, p)) for p in ("A", "B", "C")]
    print("%s: A=%s B=%s C=%s" % (name, got[0], got[1], got[2]))
