#!/usr/bin/env python3
"""driver_test2.py : discriminating version. The INTENDED board and the STALE board must not share the answer.

Design: after the first game the engine holds board S (a stale board). The driver then means to start board T. If T
is refused/truncated and the driver does not notice, it searches S. So the test asks: is the returned move legal on T
but NOT on S (or vice versa)? Only then does the answer reveal which board was actually searched.
I search both boards directly to find a position pair where the legal-move SETS differ, and report the move's
membership in each.
"""
import re, subprocess, chess
INFO=re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+)")
PC="/home/ubuntu/pcbuild/forge"
OPTS=[l.strip() for l in open("../job7/pc20_opts.txt") if l.strip() and not l.startswith("#")]+["setoption name OwnBook value false"]

class Driver:
    def __init__(self, compliant):
        self.compliant=compliant
        p=subprocess.Popen([PC],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
        self.p=p
        p.stdin.write("uci\n");p.stdin.flush()
        names=set()
        while True:
            l=p.stdout.readline()
            if not l: raise RuntimeError("died")
            s=l.strip()
            if s.startswith("option name "): names.add(s.split("option name ")[1].split(" type ")[0])
            if s=="uciok": break
        for line in OPTS:
            nm=line.split("name ")[1].split(" value ")[0]
            if nm in names:
                p.stdin.write(line+"\n");p.stdin.flush()
                p.stdin.write("isready\n");p.stdin.flush()
                while p.stdout.readline().strip()!="readyok": pass
    def pos(self,cmd):
        p=self.p
        if self.compliant: p.stdin.write("ucinewgame\n");p.stdin.flush()
        p.stdin.write(cmd+"\n");p.stdin.flush()
        p.stdin.write("isready\n");p.stdin.flush()
        d=0
        while True:
            l=p.stdout.readline()
            if not l: break
            s=l.strip()
            if s.startswith("info string"): d+=1
            if s=="readyok": break
        return d
    def go(self):
        p=self.p
        p.stdin.write("go wtime 6000 btime 6000 winc 60 binc 60\n");p.stdin.flush()
        while True:
            l=p.stdout.readline()
            if not l: return None
            s=l.strip()
            if s.startswith("bestmove"): return s.split()[1]
    def close(self):
        self.p.stdin.write("quit\n");self.p.stdin.flush()
        try: self.p.wait(timeout=5)
        except: self.p.kill()

STALE_MOVES="d2d4 g7g6 b1c3 d7d5 e2e4 d5e4 c3e4 f8g7"
STALE=chess.Board()
for m in STALE_MOVES.split(): STALE.push(chess.Move.from_uci(m))
# INTENDED: a position whose legal set differs sharply from STALE's - KQ vs K, mate in 1
INTENDED=chess.Board("7k/5Q2/6K1/8/8/8/8/8 w - - 0 1")
INTENDED_MOVES=[]  # sent as a FEN game start
print("STALE board    :", STALE.fen())
print("STALE legal    :", STALE.legal_moves.count(), "moves")
print("INTENDED board :", INTENDED.fen(), "| legal", INTENDED.legal_moves.count())
print("legal sets disjoint?", set(m.uci() for m in STALE.legal_moves).isdisjoint(set(m.uci() for m in INTENDED.legal_moves)))
print()
print("| driver | scenario (refuse the INTENDED fen) | bestmove | legal on INTENDED? | legal on STALE? | searched board |")
print("|---|---|---|---|---|---|")
for compliant,label in ((False,"NAIVE"),(True,"COMPLIANT")):
    d=Driver(compliant)
    d.pos("position startpos moves "+STALE_MOVES); d.go()      # engine now holds STALE
    # the driver MEANS to start INTENDED but sends an impossible-castling variant of it
    bad="7k/5Q2/6K1/8/8/8/8/8 w K - 0 1"
    diags=d.pos("position fen "+bad)
    if compliant and diags>0:
        d.pos("position fen "+INTENDED.fen())                  # rebuild with a well-formed FEN
    bm=d.go(); d.close()
    mv=chess.Move.from_uci(bm) if bm and bm!="0000" else None
    on_int = mv in INTENDED.legal_moves if mv else False
    on_st  = mv in STALE.legal_moves if mv else False
    searched = "INTENDED" if on_int and not on_st else ("STALE" if on_st and not on_int else "ambiguous")
    print("| %s | refused FEN for the new game | %s | %s | %s | **%s** |"%(label,bm,
        "yes" if on_int else "no","yes" if on_st else "no",searched))
