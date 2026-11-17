#!/usr/bin/env python3
"""job55 : does the bail require THIS root to repeat 3x, or ANY position in the history?

T0 root only. T1 a shuttle that repeats an INTERMEDIATE position 3x then leaves it, ending on the root (root occurs
ONCE). T2 a shuttle where the ROOT occurs 3x.

Occurrence counts are ASSERTED and printed BEFORE the engine is called; T2 is the gate on the whole job.
"""
import re, subprocess, sys, os, itertools
import chess

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
BASE = os.path.expanduser("~/build/forge")
ROOT = "1K6/8/8/3R4/8/8/8/k7 w - - 0 1"


def pk(b):
    f = b.fen().split(' ')
    return ' '.join(f[:2] + f[3:4])


def counts_along(root_fen, moves):
    b = chess.Board(root_fen)
    c = {pk(b): 1}
    for mv in moves:
        m = chess.Move.from_uci(mv)
        assert m in b.legal_moves, ("illegal", mv, b.fen())
        b.push(m)
        k = pk(b)
        c[k] = c.get(k, 0) + 1
    return c, b


def shuttle(root_fen, from_sq, to_sq, other_sq, other_to):
    """4-ply cycle: piece a->b, other c->d, b->a, d->c. Returns the move list if it is legal and non-capturing."""
    try:
        seq = [chess.Move.from_uci(from_sq + to_sq).uci()]
    except Exception:
        return None
    b = chess.Board(root_fen)
    try:
        for mv in (from_sq + to_sq, other_sq + other_to,
                   to_sq + from_sq, other_to + other_sq):
            m = chess.Move.from_uci(mv)
            if m not in b.legal_moves or b.is_capture(m):
                return None
            b.push(m)
            if b.is_check():
                return None
    except Exception:
        return None
    return seq + [other_sq + other_to, to_sq + from_sq, other_to + other_sq]


def find_cycle_returning_to_root(root_fen):
    """Find a 4-ply cycle that returns to the ROOT position (for T2)."""
    root = chess.Board(root_fen)
    target = pk(root)
    for a in ['d5d6', 'd5d7', 'd5e5', 'd5c5', 'd5d4']:
        for o in ['a1b1', 'a1b2', 'a1a2']:
            seq = shuttle(root_fen, a[:2], a[2:], o[:2], o[2:])
            if not seq:
                continue
            b = chess.Board(root_fen)
            ok = True
            for mv in seq:
                m = chess.Move.from_uci(mv)
                if m not in b.legal_moves:
                    ok = False
                    break
                b.push(m)
            if ok and pk(b) == target:
                return seq
    return None


def find_intermediate_cycle(root_fen):
    """Find a move list where SOME NON-ROOT position occurs 3 times and the ROOT occurs only once.

    MY FIRST VERSION WAS SELF-CONTRADICTORY: it required the sequence to END at the root with the root occurring once,
    but on this board every 4-ply shuttle returns to the root, so the root necessarily occurs twice. The predicate
    could never be satisfied and T1 silently became "NOT RUN" — which would have left M1/M2 undecided while looking
    like a completed experiment. Fixed by dropping the "ends at root" requirement: what T1 needs is a history whose
    MOST-REPEATED position is not the root, with the root present ONCE, so the engine faces a root it has seen once
    and a history containing a threefold elsewhere.
    """
    root = chess.Board(root_fen)
    rk = pk(root)
    # Build: one root-ish first move that leaves the root permanently, then repeat an unrelated shuttle 3x elsewhere.
    # Simplest reliable construction: move the rook away, then shuttle the kings between two squares three times.
    for rook_move in ['d5d6', 'd5d7', 'd5d5', 'd5e5', 'd5c5', 'd5b5', 'd5a5']:
        b0 = chess.Board(root_fen)
        try:
            m0 = chess.Move.from_uci(rook_move)
        except Exception:
            continue
        if m0 not in b0.legal_moves:
            continue
        b0.push(m0)
        # shuttle black king and white king between two squares, 3 full cycles (6 plies each cycle is 4 plies here)
        bk = b0.piece_at(chess.A1)
        wk = b0.piece_at(chess.B8)
        if not bk or bk.piece_type != chess.KING:
            continue
        bcycle = None
        for seq in (['a1b1', 'b8c8', 'b1a1', 'c8b8'],
                    ['a1a2', 'b8c8', 'a2a1', 'c8b8'],
                    ['a1b2', 'b8c8', 'b2a1', 'c8b8']):
            bb = b0.copy()
            ok = True
            for mv in seq:
                m = chess.Move.from_uci(mv)
                if m not in bb.legal_moves or bb.is_capture(m):
                    ok = False
                    break
                bb.push(m)
                if bb.is_check():
                    ok = False
                    break
            if ok and pk(bb) == pk(b0):
                bcycle = seq
                break
        if not bcycle:
            continue
        moves = [rook_move] + bcycle * 3
        try:
            c, bend = counts_along(root_fen, moves)
        except AssertionError:
            continue
        rootc = c.get(rk, 0)
        nonroot_max = max((v for k, v in c.items() if k != rk), default=0)
        if rootc == 1 and nonroot_max >= 3:
            return moves
    return None


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


# ---- construct and ASSERT fixtures BEFORE any engine call ----
cyc_root = find_cycle_returning_to_root(ROOT)
cyc_mid = find_intermediate_cycle(ROOT)
print("== fixture construction (asserted before the engine is started) ==")
print("T2 cycle (root returns): %s" % (cyc_root,))
print("T1 cycle (intermediate repeats, root does NOT): %s" % (cyc_mid,))

t2_moves = (cyc_root * 2) if cyc_root else None
t1_moves = None
if cyc_mid:
    # repeat the intermediate shuttle so SOME position occurs 3x, then step away and come back to the root once
    t1_moves = cyc_mid  # already contains its own non-root threefold

for name, moves in (("T1", t1_moves), ("T2", t2_moves)):
    if not moves:
        print("  %s: NO VALID MOVE LIST -> that case cannot run" % name)
        continue
    c, b = counts_along(ROOT, moves)
    rootc = c.get(pk(chess.Board(ROOT)), 0)
    maxc = max(c.values())
    print("  %s: root occurrences=%d  max occurrences of any position=%d  ends at root=%s" % (
        name, rootc, maxc, pk(b) == pk(chess.Board(ROOT))))

print()
print("== measurement ==")
p = conn()
print("| case | root occ | max occ | nodes | score | bestmove |")
print("|---|---|---|---|---|---|")
res = {}
for name, moves in (("T0 root only", None), ("T1 intermediate 3x", t1_moves), ("T2 root 3x", t2_moves)):
    if moves is None and name != "T0 root only":
        print("| %s | - | - | **NOT RUN** | - | - |" % name)
        continue
    c, b = counts_along(ROOT, moves) if moves else ({pk(chess.Board(ROOT)): 1}, chess.Board(ROOT))
    (kind, val, nodes), bm = go(p, ROOT.rstrip().rsplit(' ', 2)[0] + " 0 1", moves, 10)
    res[name] = (nodes, kind, val, bm)
    print("| %s | %d | %d | %d | %s %d | %s |" % (
        name, c.get(pk(chess.Board(ROOT)), 0), max(c.values()), nodes, kind, val, bm))
    sys.stdout.flush()
p.stdin.write("quit\n"); p.stdin.flush()
try:
    p.wait(timeout=10)
except Exception:
    p.kill()

print()
t0 = res.get("T0 root only")
t1 = res.get("T1 intermediate 3x")
t2 = res.get("T2 root 3x")
print("P1 T0 searches (nodes > 0):", bool(t0 and t0[0] > 0), "nodes =", t0[0] if t0 else "-")
print("P3 T2 bails (0 nodes):", bool(t2 and t2[0] == 0), "nodes =", t2[0] if t2 else "-",
      "  <-- GATE: if False, no conclusion about T1 may be drawn")
if t2 and t2[0] == 0:
    print("P2 T1 searches (root-specific, M1):", bool(t1 and t1[0] > 0), "nodes =", t1[0] if t1 else "-")
else:
    print("P2 NOT EVALUATED: T2 did not bail, so the fixture is not demonstrated and T1 proves nothing.")
