#!/usr/bin/env python3
"""Decisive sign check: in a LOST position, does the engine prefer the LONGER mate?

Build a position where White (to move, lost) can walk into mate in 1 or delay. Then ask the engine.
If it reports a NEGATIVE mate for White and prefers the longer one, the convention is:
  mate -N = White (side to move) gets mated in N; a SMALLER |N| is worse; -10 is BETTER than -8.
"""
import subprocess

FEN = "7k/8/8/8/8/8/6q1/7K w - - 0 1"

def run(exe, fen, depth, sm=None):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    def w(c): p.stdin.write(c+"\n"); p.stdin.flush()
    def r():
        l = p.stdout.readline()
        if l == "": raise RuntimeError("died")
        return l
    def rd():
        while True:
            if r().strip() == "readyok": return
    w("uci")
    while r().strip() != "uciok": pass
    for n,v in [("Threads","1"),("Hash","16"),("OwnBook","false")]:
        w("setoption name %s value %s" % (n,v)); w("isready"); rd()
    w("ucinewgame"); w("isready"); rd()
    w("position fen "+fen); w("isready"); rd()
    w(("go depth %d searchmoves %s" % (depth, sm)) if sm else ("go depth %d" % depth))
    last=None; bm=None
    while True:
        l=r().strip()
        if " pv " in l and l.startswith("info"): last=l.split()
        if l.startswith("bestmove"): bm=l.split()[1]; break
    p.kill()
    if last is None: return None, None, None, bm
    return last[last.index("score")+1], int(last[last.index("score")+2]), last[last.index("seldepth")+1], bm

exe="/home/ubuntu/bld/release/forge"
import chess
b=chess.Board(FEN)
print("FEN:", FEN)
print(b)
print("White to move, White has ONLY a king, Black has K+Q -> White is lost.")
print("legal white moves:", [m.uci() for m in b.legal_moves])
print()
print("| what | score | seldepth | move |")
print("|---|---|---|---|")
k,v,sd,bm = run(exe,FEN,14)
print("| free choice, depth 14 | %s %d | %s | %s |" % (k,v,sd,bm))
# Score each white move separately to see the ordering of mate distances
for mv in sorted(m.uci() for m in b.legal_moves):
    k,v,sd,bm2 = run(exe,FEN,14,mv)
    print("| searchmoves %s | %s %d | %s | %s |" % (mv,k,v,sd,bm2))
print()
print("Read: if the moves' scores are all 'mate -N' with N>=1, then White is being mated.")
print("Whichever move has the LARGEST |N| is the one that survives longest. The engine should pick it.")
