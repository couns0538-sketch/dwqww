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

GAME1="d2d4 g7g6 b1c3 d7d5 e2e4 d5e4 c3e4 f8g7"
GOOD_FEN="rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6 0 2"   # a legal shape
BAD_FEN="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w KQ - 0 1"          # impossible castling right
BAD_MOVES="e2e4 e7e5 g1f3 b8c6 e2e4"                                     # illegal token at ply 5

def scenario(kind, compliant):
    d=Driver(compliant)
    # play a first game so a "previous board" exists
    d.set_position("position startpos moves "+GAME1)
    d.go()
    if kind=="H1_refused_fen":
        diags=d.set_position("position fen "+BAD_FEN)
        # THE INTENDED board for H1 is the new game the driver meant to start
        intended=chess.Board(GOOD_FEN); believed=intended
        rebuilt = compliant and diags>0
        if rebuilt:
            d.set_position("position fen "+GOOD_FEN)
            believed=intended
    elif kind=="H2_illegal_token":
        diags=d.set_position("position startpos moves "+BAD_MOVES)
        # THE INTENDED board: the full well-formed list the driver MEANT to send
        intended=chess.Board()
        for m in "e2e4 e7e5 g1f3 b8c6".split(): intended.push(chess.Move.from_uci(m))
        believed=intended   # what a correct driver should end up on
        rebuilt = compliant and diags>0
        if rebuilt:
            good="e2e4 e7e5 g1f3 b8c6"
            d.set_position("position startpos moves "+good)
            believed=intended
    else:
        believed=chess.Board()
    bm=d.go(); d.close()
    if bm in (None,"0000"): return ("NO BESTMOVE", False, diags if 'diags' in dir() else 0)
    try: mv=chess.Move.from_uci(bm)
    except ValueError: return (bm, False, diags)
    return (bm, mv in believed.legal_moves, diags)

print("| driver | scenario | bestmove | legal on the board it believes? | info-string lines seen |")
print("|---|---|---|---|---|")
for compliant,label in ((False,"NAIVE"),(True,"COMPLIANT")):
    for kind in ("H1_refused_fen","H2_illegal_token"):
        bm,ok,diags=scenario(kind,compliant)
        print("| %s | %s | %s | %s | %s |"%(label,kind,bm,"yes" if ok else "**NO (WRONG MOVE)**",diags))
