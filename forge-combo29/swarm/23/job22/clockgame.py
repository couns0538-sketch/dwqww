#!/usr/bin/env python3
"""clockgame.py : drive a CLOCK self-play game with the PC build until a third occurrence is claimable, then replay
that exact game to both builds and compare their answer at the third occurrence."""
import re, subprocess
import chess
INFO=re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
PC="/home/ubuntu/pcbuild/forge"; BASE="/home/ubuntu/build/forge"
PC20=[l.strip() for l in open("../job7/pc20_opts.txt") if l.strip() and not l.startswith("#")]
OWB="setoption name OwnBook value false"

class Eng:
    def __init__(self, exe, opts):
        self.p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
        p=self.p
        p.stdin.write("uci\n");p.stdin.flush()
        names=set()
        while True:
            l=p.stdout.readline()
            if not l: raise RuntimeError("died")
            s=l.strip()
            if s.startswith("option name "): names.add(s.split("option name ")[1].split(" type ")[0])
            if s=="uciok": break
        for line in list(opts)+[OWB]:
            nm=line.split("name ")[1].split(" value ")[0]
            if nm not in names: raise RuntimeError("STOP option "+nm)
            p.stdin.write(line+"\n");p.stdin.flush()
            p.stdin.write("isready\n");p.stdin.flush()
            while p.stdout.readline().strip()!="readyok": pass
    def go(self, position_cmd, budget):
        p=self.p
        p.stdin.write("ucinewgame\n");p.stdin.flush()
        p.stdin.write(position_cmd+"\n");p.stdin.flush()
        p.stdin.write("isready\n");p.stdin.flush()
        while p.stdout.readline().strip()!="readyok": pass
        p.stdin.write(budget+"\n");p.stdin.flush()
        last=None; bm=None
        while True:
            l=p.stdout.readline()
            if not l: raise RuntimeError("died in search")
            s=l.strip()
            m=INFO.match(s)
            if m: last=(m.group(2),int(m.group(3)),int(m.group(4)))
            if s.startswith("bestmove"): bm=s.split()[1]; break
        return last,bm
    def close(self):
        self.p.stdin.write("quit\n");self.p.stdin.flush()
        try: self.p.wait(timeout=10)
        except: self.p.kill()

CLOCK="go wtime 6000 btime 6000 winc 60 binc 60"
# --- step 1: clock-driven self-play until a claimable third occurrence
e=Eng(PC,PC20)
b=chess.Board(); moves=[]
third=None
for ply in range(200):
    if b.can_claim_threefold_repetition():
        third=(ply, b.halfmove_clock, b.fen()); break
    cmd = "position startpos" if not moves else "position startpos moves "+" ".join(moves)
    last,bm = e.go(cmd, CLOCK)
    if bm in (None,"0000"): break
    mv=chess.Move.from_uci(bm)
    if mv not in b.legal_moves: break
    b.push(mv); moves.append(bm)
e.close()
print("self-play plies played:", len(moves))
print("third occurrence claimable:", third is not None)
if third:
    print("at ply %d, halfmove counter %d"%(third[0],third[1]))
    print("fen:",third[2])
print("game:", " ".join(moves))

if third:
    ply,hc,fen=third
    # --- step 2: replay that exact game to both builds and compare
    print()
    print("| build | answer at the third occurrence (same game) |")
    print("|---|---|")
    for name,exe,opts in (("base 6b98f217",BASE,[]),("PC r15 + PC20",PC,PC20)):
        ee=Eng(exe,opts)
        last,bm=ee.go("position startpos moves "+" ".join(moves), CLOCK)
        ee.close()
        if last is None:
            print("| %s | no info line, bestmove %s |"%(name,bm))
        else:
            print("| %s | %s %d, %d nodes, bestmove %s |"%(name,last[0],last[1],last[2],bm))
    print()
    print("halfmove counter at the third occurrence:",hc,"(< 100 means the repetition, not the fifty-move rule)")
