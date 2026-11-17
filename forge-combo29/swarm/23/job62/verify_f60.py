#!/usr/bin/env python3
"""job62 : re-verify 23-F60's "the unsearched move hangs a piece" under the corrected validator.

The material check is the load-bearing part: "hangs a piece" is a MATERIAL claim and is settled by counting material,
not by a search score.
"""
import re, subprocess, os, sys
sys.path.insert(0, '../job59')
import chess
from validate import check_fixture, count_occurrences

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
BASE = os.path.expanduser("~/build/forge")
PC = os.path.expanduser("~/pcbuild/forge")
FEN = "rn3rk1/pp2bpp1/1q2pnbp/3p4/N2P1B1P/4P1N1/PP1Q1PP1/2R1KB1R b K - 11 16"
VAL = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}


def material(b):
    """(white_total, black_total) in pawns."""
    w = sum(VAL[p.piece_type] for p in b.piece_map().values() if p.color == chess.WHITE)
    k = sum(VAL[p.piece_type] for p in b.piece_map().values() if p.color == chess.BLACK)
    return w, k


def conn(exe):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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


def go(p, fen, moves, depth=12):
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


# find a castling-neutral cycle from F60's FEN: shuttling a knight/bishop (not a king or rook) between two squares
def find_cycle(fen):
    root = chess.Board(fen)
    rk = (root.board_fen(), root.turn, root.castling_xfen())
    found = []

    def idn(b):
        return (b.board_fen(), b.turn, b.castling_xfen())

    def dfs(b, path):
        if found:
            return
        if len(path) == 4:
            if idn(b) == rk:
                found.append(list(path))
            return
        for m in b.legal_moves:
            if b.is_capture(m):
                continue
            pc = b.piece_at(m.from_square)
            if pc.piece_type in (chess.KING, chess.ROOK, chess.PAWN):
                continue
            b.push(m)
            if not b.is_check():
                dfs(b, path + [m.uci()])
            b.pop()
            if found:
                return

    dfs(root, [])
    return found[0] if found else None


print("== fixture ==")
cyc = find_cycle(FEN)
print("F60 FEN:", FEN)
print("castling-neutral cycle found:", cyc)
if not cyc:
    print("NO CASTLING-NEUTRAL CYCLE FOUND on this board -> P1 KILLED, cannot rebuild F60's root this way")
    sys.exit(2)
moves = cyc * 2
ok, msg = check_fixture(FEN, moves, expect=3)
print("validator:", "PASS" if ok else "**REJECTED**", "|", msg)
if not ok:
    sys.exit(3)

print()
print("== base's move on the validated root ==")
p = conn(BASE)
(k, v, nodes), bm_base = go(p, FEN, moves, 10)
p.stdin.write("quit\n"); p.stdin.flush()
print("  base: %s %d | nodes %d | move %s" % (k, v, nodes, bm_base))

print()
print("== PC's move and both consequences at depth 16 ==")
q = conn(PC)
(k2, v2, n2), bm_pc = go(q, FEN, moves, 16)
print("  PC  : %s %d | nodes %d | move %s" % (k2, v2, n2, bm_pc))

root = chess.Board(FEN)
for mv in moves:
    root.push(chess.Move.from_uci(mv))
rw, rb = material(root)
print()
print("  material BEFORE either move: white %d, black %d (diff %+d for white)" % (rw, rb, rw - rb))

rows = []
for name, mv in (("base's", bm_base), ("PC's", bm_pc)):
    b = root.copy()
    m = chess.Move.from_uci(mv)
    legal = m in b.legal_moves
    captured = b.piece_at(m.to_square) if legal else None
    capv = VAL.get(captured.piece_type, 0) if captured else 0
    b.push(m)
    aw, ab = material(b)
    # how much material can the OPPONENT win immediately? count free captures available to white
    best_gain = 0
    for om in b.legal_moves:
        if b.is_capture(om):
            victim = b.piece_at(om.to_square)
            gain = VAL.get(victim.piece_type, 0) if victim else 0
            # is the capturing square defended by black?
            bb = b.copy()
            bb.push(om)
            recaptured = any(bb.is_capture(r) and bb.piece_at(r.to_square) and
                             bb.piece_at(r.to_square).piece_type == victim.piece_type for r in bb.legal_moves)
            net = gain - (VAL.get(victim.piece_type, 0) if recaptured else 0)
            best_gain = max(best_gain, gain if not recaptured else 0)
    (kk, vv, nn), _ = go(conn(PC), root.fen(), moves + [mv], 16)
    rows.append((name, mv, legal, capv, aw - ab, best_gain, kk, vv, nn))
    print()
    print("  %s %s: legal %s | captured on arrival %s | material after: white %d black %d (diff %+d) |"
          " best FREE capture available to white next = %d pawns" % (
              name, mv, legal, captured.symbol() if captured else 'none', aw, ab, aw - ab, best_gain))
    print("      PC depth 16 on the position after it: %s %d (%d nodes)" % (kk, vv, nn))
q.stdin.write("quit\n"); q.stdin.flush()

print()
print("P3 MATERIAL CHECK: does the base's move lose material relative to the PC's?")
b0 = next(r for r in rows if r[0] == "base's")
p0 = next(r for r in rows if r[0] == "PC's")
print("  free-capture available to white after base's move:", b0[5], "pawns")
print("  free-capture available to white after PC's move  :", p0[5], "pawns")
print("  => base's move HANGS material:", b0[5] > p0[5])
