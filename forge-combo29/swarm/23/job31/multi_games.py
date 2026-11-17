#!/usr/bin/env python3
"""clockgame2.py : play the clock game UNTIL THE POSITION HAS ACTUALLY OCCURRED THREE TIMES.

My first version stopped when python-chess's can_claim_threefold_repetition() turned True — but that function also
returns True when a third occurrence COULD BE REACHED BY A MOVE, so it fired at only two actual occurrences and the
engine (which needs three) searched normally. This version counts ACTUAL occurrences and keeps playing until the
current position has occurred three times.
"""
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

def key(b):
    return b.board_fen()+"|"+(("w") if b.turn else "b")+"|"+str(b.castling_rights)+"|"+str(b.ep_square)


import chess, sys
CLOCK="go wtime 6000 btime 6000 winc 60 binc 60"
def key(b): return b.board_fen()+"|"+("w" if b.turn else "b")+"|"+str(b.castling_rights)+"|"+str(b.ep_square)
OPENINGS=[[],["e2e4"],["d2d4"],["c2c4"],["g1f3"],["b1c3"],
          ["e2e4","e7e5"],["d2d4","d7d5"],["e2e4","c7c5"],["d2d4","g8f6","c2c4"]]
results=[]
for seed in OPENINGS:
    e=Eng(PC,PC20)
    b=chess.Board(); moves=list(seed)
    for m in moves: b.push(chess.Move.from_uci(m))
    counts={key(b):1}; hit=None
    for ply in range(250):
        if counts.get(key(b),0)>=3: hit=(len(moves),b.halfmove_clock,b.fen()); break
        cmd="position startpos" if not moves else "position startpos moves "+" ".join(moves)
        last,bm=e.go(cmd,CLOCK)
        if bm in (None,"0000"): break
        mv=chess.Move.from_uci(bm)
        if mv not in b.legal_moves: break
        b.push(mv); moves.append(bm); counts[key(b)]=counts.get(key(b),0)+1
    e.close()
    results.append((seed,moves,hit))
    import chess as _c
    ok = hit is not None
    if ok:
        bb=_c.Board(hit[2])
        ok = (not bb.is_insufficient_material()) and hit[1] < 100
        print("opening %-16s plies %3d | occurrence at ply %s halfmove %s pieces %2d | GENUINE: %s"%(
            str(seed),len(moves),hit[0],hit[1],len(bb.piece_map()),ok))
    else:
        print("opening %-16s plies %3d | NO occurrence within 250 plies"%(str(seed),len(moves)))
import json
json.dump([(s,m,h) for s,m,h in results], open("games.json","w"))
