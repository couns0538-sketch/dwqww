#!/usr/bin/env python3
"""corpus_accept.py EXE BUILD — do all real G+O positions get accepted, and does perft 1 match
python-chess? PC20, Threads 1. Tests the FEN layer end-to-end on real data."""
import os,re,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
fens=[]
for p in ("positions/G_set_G.epd","positions/O_first200.fens"):
    with open(p) as f:
        for line in f:
            line=line.strip()
            if not line or line.startswith("#"): continue
            x=line.split(";")[0].strip().split(" ")[:6]
            if len(x)==6: fens.append(" ".join(x))
print(f"build {BUILD}\n{len(fens)} real positions, PC20, Threads 1, go perft 1\n")
acc=ref=mis=0; bad=[]
e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
try:
    for fen in fens:
        ans,r=e.position(fen=fen)
        if r: ref+=1; bad.append(("REFUSED",fen,r[0])); continue
        e.send("go perft 1"); lines=e.read_until("nodes ")
        n=None
        for l in lines:
            m=re.match(r"nodes (\d+)",l)
            if m: n=int(m.group(1))
        if n is None: bad.append(("MEASUREMENT FAILED",fen,"no nodes")); continue
        acc+=1
        py=chess.Board(fen).legal_moves.count()
        if n!=py: mis+=1; bad.append(("MISMATCH",fen,f"engine {n} py {py}"))
finally: e.quit()
print(f"  accepted {acc}, refused {ref}, perft-1 mismatches {mis}")
for t,f,d in bad[:10]: print(f"    {t}: {d}  {f[:60]}")
