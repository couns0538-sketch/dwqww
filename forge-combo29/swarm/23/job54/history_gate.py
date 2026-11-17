#!/usr/bin/env python3
"""job54 : is the HISTORY GATE general? S1 bare FEN / S2 cycle x2 (threefold) / S3 cycle x1 (two occurrences).

CRITICAL CONTROL: every FEN is rewritten with halfmove 0 so the FIFTY-MOVE rule cannot confound the repetition test —
23-F93 already showed the counter triggers the same bail, so leaving a high counter in would make every S2 result
uninformative.

Each cycle is FOUND by search (non-capturing, non-checking, returns to the same position) and validated, never typed.
"""
import re, subprocess, sys, os
import chess

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
MOVELINE = re.compile(r"^([a-h][1-8][a-h][1-8][qrbn]?): (\d+)$")
BASE = os.path.expanduser("~/build/forge")

POSITIONS = [
    ("A F109 natural root", "1k6/3q1p1p/rp5p/4P3/pQ3P2/7P/3R2PK/8 b"),
    ("B F45 endgame", "1K6/8/8/3R4/8/8/8/k7 w"),
    ("C job52 P1", "6k1/5ppp/8/8/8/8/5PPP/R5K1 w"),
    ("D job52 P4", "7k/8/8/8/8/8/6PP/7K b"),
]


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


def klass(b, m):
    pc = b.piece_at(m.from_square)
    if pc.piece_type == chess.PAWN:
        if b.is_capture(m):
            return 2
        if abs(m.to_square - m.from_square) == 16:
            return 1
        return 0
    return {chess.KNIGHT: 3, chess.BISHOP: 4, chess.ROOK: 5, chess.QUEEN: 6, chess.KING: 7}[pc.piece_type]


def predict(fen):
    b = chess.Board(fen)
    classes = {}
    for m in b.legal_moves:
        classes.setdefault(klass(b, m), []).append(m)
    if not classes:
        return None
    first = min(classes)
    return min(classes[first], key=lambda m: (m.from_square, m.to_square)).uci()


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


def zero_counter(fen):
    # Shorthand FENs (< 6 fields) have no halfmove field at all — my first version indexed [4] and crashed on them.
    # Build the full FEN via python-chess, then force the counter to 0 so the fifty-move rule cannot confound the
    # repetition test (23-F93 showed the counter triggers the same bail).
    b = chess.Board(fen)
    f = b.fen().split(' ')
    f[4] = '0'
    return ' '.join(f)


print("| pos | cycle | S1 bare nodes | S2 x2 nodes | S3 x1 nodes | S2 score | S2 move | predicted | S2=pred? |")
print("|---|---|---|---|---|---|---|---|---|")
p = conn()
results = []
for label, fen0 in POSITIONS:
    fen = zero_counter(fen0)
    cyc = find_cycle(fen)
    if cyc is None:
        print("| %s | **NO CYCLE FOUND** | - | - | - | - | - | - | - |" % label)
        continue
    s1 = go(p, fen, None, 10)
    s2 = go(p, fen, " ".join(cyc * 2), 10)
    s3 = go(p, fen, " ".join(cyc), 10)
    pred = predict(fen)
    results.append((label, cyc, s1, s2, s3, pred))
    print("| %s | %s | %d | %d | %d | %s %d | %s | %s | %s |" % (
        label, " ".join(cyc), s1[0][2], s2[0][2], s3[0][2], s2[0][0], s2[0][1], s2[1], pred,
        "yes" if s2[1] == pred else "**no**"))
    sys.stdout.flush()
p.stdin.write("quit\n"); p.stdin.flush()
try:
    p.wait(timeout=10)
except Exception:
    p.kill()

print()
if results:
    n2 = sum(1 for r in results if r[3][0][2] == 0)
    n13 = sum(1 for r in results if r[2][0][2] > 1000 and r[4][0][2] > 1000)
    npx = sum(1 for r in results if r[3][1] == r[5])
    print("positions with a cycle: %d" % len(results))
    print("P1 S2 gave 0 nodes on: %d of %d" % (n2, len(results)))
    print("P2 S1 AND S3 both searched (>1000 nodes) on: %d of %d" % (n13, len(results)))
    print("P4 S2 move == predicted index 0 on: %d of %d" % (npx, len(results)))
    a = next((r for r in results if r[0].startswith("A")), None)
    if a:
        print("P3 known answer on A: S1 nodes %d (expect >1000), S2 nodes %d (expect 0) -> %s" % (
            a[2][0][2], a[3][0][2], "HOLDS" if (a[2][0][2] > 1000 and a[3][0][2] == 0) else "**DOES NOT HOLD**"))
