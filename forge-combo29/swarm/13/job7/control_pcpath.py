#!/usr/bin/env python3
"""Rule-1 control for pcpath.py: a zero needs a planted one.

The zeros I report are "0 non-deterministic runs" and "0 illegal bestmoves" out of 48. Both count
only if the same comparison functions catch a planted one.
"""
import chess

def ident(a,b):
    return (a["depth"],a["nodes"],a["cp"],a["mate"],a["bestmove"])==(b["depth"],b["nodes"],b["cp"],b["mate"],b["bestmove"])

def legal(bestmove, fen):
    parts=bestmove.split()
    mv=parts[1] if len(parts)>1 else None
    if mv in (None,"(none)","0000"): return True
    return mv in {m.uci() for m in chess.Board(fen).legal_moves}

ok=True
rows=[]
a={"depth":10,"nodes":17947,"cp":-256,"mate":None,"bestmove":"bestmove g5h5"}
rows.append(("P0 identity","identical runs",not ident(a,dict(a)),False))
b=dict(a); b["nodes"]=17948
rows.append(("A nodes +1","one node differs",not ident(a,b),True))
c=dict(a); c["depth"]=9
rows.append(("B depth differs","one depth",not ident(a,c),True))
d=dict(a); d["cp"]=-257
rows.append(("C score differs","one centipawn",not ident(a,d),True))
e=dict(a); e["bestmove"]="bestmove e5e4"
rows.append(("D bestmove differs","other move",not ident(a,e),True))
f=dict(a); f["mate"]=3
rows.append(("E mate vs cp","mate 3 instead of cp",not ident(a,f),True))

fen="8/5p2/8/pp1pkpKp/7P/2P3P1/1P6/8 w - - 0 1"
rows.append(("F legal move","g5h5 in this position",not legal("bestmove g5h5",fen),False))
rows.append(("G ILLEGAL move planted","a1a8 is not legal here",not legal("bestmove a1a8",fen),True))

print("| plant | what it is | flagged? | should be | result |")
print("|---|---|---|---|---|")
for name,desc,flag,want in rows:
    good = flag==want
    ok &= good
    print("| %s | %s | %s | %s | %s |"%(name,desc,flag,want,"correct" if good else "WRONG"))
print()
print("Rule 1 verdict:", "every plant caught, identities not flagged - the zeros are measurements" if ok else "FAILED")
raise SystemExit(0 if ok else 1)
