#!/usr/bin/env python3
"""job68d : does the PC decline to claim because of POLICY, or because it finds a MATE?

F131 said the PC consistently does not claim a repetition draw (0 of 2 claimable roots). F168 showed it finds mate 8 at a
real clock on one of those roots. Those two are confounded: "found a mate" and "chose not to claim" produce the same
observation. The discriminating test is a drawn root with NO forced win available — if the PC still declines to report
cp 0 there, it is policy; if it reports the draw, the earlier result was just the mate.
"""
import re, subprocess, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job59"))
from validate import check_fixture
import chess

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
BASE = os.path.expanduser("~/build/forge")
PC = os.path.expanduser("~/pcbuild/forge")


def conn(exe):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    p.stdin.write("uci\n"); p.stdin.flush()
    while True:
        l = p.stdout.readline()
        if l.strip() == "uciok":
            break
    p.stdin.write("setoption name OwnBook value false\n"); p.stdin.flush()
    p.stdin.write("setoption name Threads value 1\nsetoption name Hash value 16\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    return p


def go(p, fen, moves, cmd):
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen %s%s\n" % (fen, (" moves " + " ".join(moves)) if moves else "")); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write(cmd + "\n"); p.stdin.flush()
    last = None; pvlen = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died")
        s = l.strip()
        m = INFO.match(s)
        if m:
            last = (m.group(2), int(m.group(3)), int(m.group(4)))
            tail = s[s.find(" pv ") + 4:] if " pv " in s else ""
            pvlen = len(tail.split())
        if s.startswith("bestmove"):
            return last, pvlen, s.split()[1]


# A drawn-by-repetition root with NO forced win for either side: two kings and two knights in a locked shuffle.
# K+N v K+N is a draw; a repetition cycle exists; nobody has a mate.
DEAD = "8/8/4k3/8/8/4K3/4N3/4n3 w - - 0 1"
CYC = None
def find_cycle(fen):
    b = chess.Board(fen); target = (b.board_fen(), b.turn, b.castling_xfen()); cf = b.castling_xfen() or '-'
    found = []
    def dfs(bb, path):
        if found: return
        if len(path) == 4:
            if (bb.board_fen(), bb.turn, bb.castling_xfen()) == target: found.append(list(path))
            return
        for m in bb.legal_moves:
            if bb.is_capture(m): continue
            bb.push(m)
            if (bb.castling_xfen() or '-') != cf or bb.is_check():
                bb.pop(); continue
            bb.pop(); bb.push(m)
            dfs(bb, path + [m.uci()])
            bb.pop()
    dfs(b, []); return found[0] if found else None

b = chess.Board(DEAD)
print("candidate board:", DEAD, "| valid:", b.is_valid(), "| legal:", len(list(b.legal_moves)))
cyc = find_cycle(DEAD)
print("cycle:", cyc)
if not cyc:
    print("no cycle -> cannot build the test here")
    sys.exit(0)
moves = cyc * 2
ok, msg = check_fixture(DEAD, moves, expect=3)
print("fixture:", "PASS" if ok else "REJECTED", "|", msg)
print()
print("| build | budget | score | pv plies | bestmove | reported the DRAW? |")
print("|---|---|---|---|---|---|")
for name, exe in (("base", BASE), ("PC", PC)):
    p = conn(exe)
    for cmd in ("go depth 12", "go movetime 1000"):
        last, pvlen, bm = go(p, DEAD, moves, cmd)
        drew = (last[0] == "cp" and last[1] == 0)
        print("| %s | `%s` | %s %d | %s | %s | %s |" % (name, cmd, last[0], last[1], pvlen, bm,
                                                       "**yes**" if drew else "no"))
    p.stdin.write("quit\n"); p.stdin.flush()
