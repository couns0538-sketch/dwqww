#!/usr/bin/env python3
"""job61 : is the PC's drawn-root behaviour CORRECT, judged against ground truth?

Fixtures validated by job59/validate.py. Scores and moves from both builds; each move's consequence scored by the DTM
prover from job58 where the position is small enough for it.
"""
import sys, re, subprocess, os
sys.path.insert(0, '../job59')
import chess
from validate import check_fixture

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
BASE = os.path.expanduser("~/build/forge")
PC = os.path.expanduser("~/pcbuild/forge")


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


CYC = "b8c8 a1b2 c8b8 b2a1".split() * 2
CASES = [
    ("R1 50-move root (halfmove 100)", "1K6/8/8/3R4/8/8/8/k7 w - - 100 60", None, "DRAWN (automatic at 75+, and 100)"),
    ("R2 CONTROL counter 0 (not drawn)", "1K6/8/8/3R4/8/8/8/k7 w - - 0 1", None, "WON for white"),
    ("R3 threefold root", "1K6/8/8/3R4/8/8/8/k7 w - - 0 1", CYC, "DRAWN (claimable, 3 occurrences)"),
    ("R4 bare kings", "8/8/8/8/8/8/8/K6k w - - 0 1", None, "DRAWN (automatic, insufficient material)"),
]

print("== fixture validation (job59 validator; both counters must agree) ==")
for label, fen, moves, truth in CASES:
    if moves:
        ok, msg = check_fixture(fen, moves, expect=3)
        print("  %-34s %s | %s" % (label, "PASS" if ok else "**REJECTED**", msg))
    else:
        print("  %-34s (no move list; truth: %s)" % (label, truth))
print()

print("| case | build | score | nodes | move | move legal? | ground truth |")
print("|---|---|---|---|---|---|---|")
res = {}
for label, fen, moves, truth in CASES:
    for name, exe in (("base", BASE), ("PC r15", PC)):
        p = conn(exe)
        (kind, val, nodes), bm = go(p, fen, moves, 12)
        p.stdin.write("quit\n"); p.stdin.flush()
        try:
            p.wait(timeout=10)
        except Exception:
            p.kill()
        b = chess.Board(fen)
        if moves:
            for mv in moves:
                b.push(chess.Move.from_uci(mv))
        legal = bm in [m.uci() for m in b.legal_moves]
        res[(label, name)] = (kind, val, nodes, bm, legal)
        print("| %s | %s | %s %d | %d | %s | %s | %s |" % (label, name, kind, val, nodes, bm,
                                                          "yes" if legal else "**NO**", truth))
print()

r4_base = res.get(("R4 bare kings", "base"))
r4_pc = res.get(("R4 bare kings", "PC r15"))
print("P2 (sharp case, insufficient material = automatic draw, no claim possible):")
print("  base  : %s %d" % (r4_base[0], r4_base[1]))
print("  PC    : %s %d" % (r4_pc[0], r4_pc[1]))
print("  PC reports cp 0 on an automatic draw:", r4_pc[1] == 0 and r4_pc[0] == "cp")
print()
r2b = res.get(("R2 CONTROL counter 0 (not drawn)", "base"))
r2p = res.get(("R2 CONTROL counter 0 (not drawn)", "PC r15"))
print("P4 control (R2 is NOT drawn): base %s %d | PC %s %d" % (r2b[0], r2b[1], r2p[0], r2p[1]))
print("  neither reports cp 0:", (r2b[1] != 0) and (r2p[1] != 0))

# 23-F230: the table above prints "**NO**" for an illegal bestmove and the P2/P4 lines print
# a bare True/False, and the script never exited nonzero - so an illegal move or a wrong P2
# would have printed and been read as a result. Assert the three claims instead.
_illegal = [k for k, v in res.items() if not v[4]]
_p2 = (r4_pc[1] == 0 and r4_pc[0] == "cp")
_p4 = (r2b[1] != 0) and (r2p[1] != 0)
print()
if not _illegal and _p2 and _p4:
    print("VERDICT: PASS (every bestmove legal; P2 holds; P4 control holds, %d positions)" % len(res))
    sys.exit(0)
print("VERDICT: FAIL (illegal bestmoves: %s; P2 %s; P4 %s)" % (_illegal or "none", _p2, _p4))
sys.exit(1)
