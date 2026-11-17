#!/usr/bin/env python3
"""driver_test.py : does the recommended protocol actually prevent the three hazards?

Two drivers, same code except the `info string` check:
  COMPLIANT: ucinewgame once before any position; prefer move list; count info-string lines after every position and
             REBUILD if any appeared; send both clocks; read to bestmove.
  NAIVE:     same, minus the info-string check.
Each plays the moves of a game against python-chess, then is given a hazard input, then asked for a move. A move is
WRONG if it is not legal on the board the driver believes it is on.
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
    def set_position(self, cmd):
        p=self.p
        if self.compliant:
            p.stdin.write("ucinewgame\n");p.stdin.flush()
        p.stdin.write(cmd+"\n");p.stdin.flush()
        p.stdin.write("isready\n");p.stdin.flush()
        diags=0
        while True:
            l=p.stdout.readline()
            if not l: break
            s=l.strip()
            if s.startswith("info string"): diags+=1
            if s=="readyok": break
        return diags
    def go(self):
        p=self.p
        p.stdin.write("go wtime 6000 btime 6000 winc 60 binc 60\n");p.stdin.flush()
        bm=None
        while True:
            l=p.stdout.readline()
            if not l: break
            s=l.strip()
            if s.startswith("bestmove"): bm=s.split()[1]; break
        return bm
    def close(self):
        self.p.stdin.write("quit\n");self.p.stdin.flush()
        try: self.p.wait(timeout=5)
        except: self.p.kill()

STALE_MOVES="d2d4 g7g6 b1c3 d7d5 e2e4 d5e4 c3e4 f8g7"
STALE=chess.Board()
for m in STALE_MOVES.split(): STALE.push(chess.Move.from_uci(m))
SSET=set(m.uci() for m in STALE.legal_moves)
# INTENDED boards chosen so their legal sets are DISJOINT from STALE's: a move then reveals WHICH board was searched
INT1=chess.Board("7k/5Q2/6K1/8/8/8/8/8 w - - 0 1")          # for H1 (FEN route)
I1SET=set(m.uci() for m in INT1.legal_moves)
INT2=chess.Board("7k/8/6K1/8/8/8/8/7Q w - - 0 1")            # for H2 (move-list route)
I2SET=set(m.uci() for m in INT2.legal_moves)

def verdict(bm, intended_set):
    if bm in (None,"0000"): return "NO BESTMOVE","-","-","-"
    on_i = bm in intended_set
    on_s = bm in SSET
    searched = "INTENDED" if (on_i and not on_s) else ("STALE" if (on_s and not on_i) else "ambiguous")
    return bm, ("yes" if on_i else "no"), ("yes" if on_s else "no"), searched

print("STALE board (engine holds this after game 1):", STALE.fen(), "| legal", len(SSET))
print("INT1:", INT1.fen(), "| legal", len(I1SET), "| disjoint from STALE:", SSET.isdisjoint(I1SET))
print("INT2:", INT2.fen(), "| legal", len(I2SET), "| disjoint from STALE:", SSET.isdisjoint(I2SET))
print()
print("| driver | scenario | bestmove | legal on INTENDED? | legal on STALE? | which board was searched |")
print("|---|---|---|---|---|---|")
for compliant,label in ((False,"NAIVE"),(True,"COMPLIANT")):
    # H1: the driver means to start INT1 but sends it with an impossible castling right
    d=Driver(compliant)
    d.set_position("position startpos moves "+STALE_MOVES); d.go()
    diags=d.set_position("position fen 7k/5Q2/6K1/8/8/8/8/8 w K - 0 1")
    if compliant and diags>0:
        d.set_position("position fen "+INT1.fen())
    bm=d.go(); d.close()
    print("| %s | H1 refused FEN for the new game | %s | %s | %s | **%s** |"%((label,)+verdict(bm,I1SET)))
    # H2: the driver sends a move list with an illegal token; intended is INT2 reached by a legal prefix
    d=Driver(compliant)
    d.set_position("position startpos moves "+STALE_MOVES); d.go()
    # a legal prefix that reaches INT2 does not exist from startpos, so use: prefix + illegal token
    good="e2e4 e7e5"
    diags=d.set_position("position startpos moves "+good+" e2e4")
    if compliant and diags>0:
        d.set_position("position startpos moves "+good)
    bm=d.go(); d.close()
    b2=chess.Board()
    for m in good.split(): b2.push(chess.Move.from_uci(m))
    B2SET=set(m.uci() for m in b2.legal_moves)
    bm_,oi,os_,searched = verdict(bm,B2SET)
    print("| %s | H2 illegal token (intended = after %s) | %s | %s | %s | **%s** |"%(label,good,bm_,oi,os_,searched))
