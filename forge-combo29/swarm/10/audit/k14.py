#!/usr/bin/env python3
"""k14.py -- K14: does a searchmoves-restricted root search a different, smaller tree, and is no
root hash entry stored? Measured with the EOF-safe driver at depth 12.

Design: same position (startpos) and depth; A unrestricted, B restricted to all 20 legal moves.
Then each repeated ONCE MORE in the SAME process to see whether a stored root entry shrinks the repeat.
"""
import json, os, sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from drv import Drv
EXE=os.environ.get("FORGE_EXE","/home/ubuntu/builds/release/forge")
OUT=os.path.abspath(sys.argv[1]); os.makedirs(OUT,exist_ok=True)
ALL=" ".join(m.uci() for m in __import__("chess").Board().legal_moves)
def seq(restrict, times):
    d=Drv(EXE); d.uci(); d.isready(); d.opt("OwnBook","false"); d.isready()
    d.write("ucinewgame"); d.isready(); d.pos("position startpos")
    res=[]
    for k in range(times):
        cmd="go depth 12" + ((" searchmoves "+ALL) if restrict else "")
        n,b,l=d.go(cmd)
        res.append({"nodes":n,"bestmove":b})
    d.quit(); return res
A=seq(False,1); B=seq(True,1); C=seq(False,2); Dd=seq(True,2)
s={"ALL_moves_listed":len(ALL.split()),"A_unrestricted":A,"B_restricted_all":B,
   "C_unrestricted_twice":C,"D_restricted_twice":Dd,
   "B_smaller":(B[0]["nodes"] is not None and A[0]["nodes"] is not None and B[0]["nodes"]<A[0]["nodes"]),
   "B_differs":B[0]["nodes"]!=A[0]["nodes"],
   "unrestricted_repeat_shrinks":C[1]["nodes"]<C[0]["nodes"],
   "restricted_repeat_shrinks":Dd[1]["nodes"]<Dd[0]["nodes"],
   "bestmove_same":A[0]["bestmove"]==B[0]["bestmove"]}
s["verdict"]=("PASS" if s["B_smaller"] and s["unrestricted_repeat_shrinks"] and not s["restricted_repeat_shrinks"]
              else "PARTLY/REFUTED")
json.dump(s,open(os.path.join(OUT,"K14","summary.json") if os.path.isdir(os.path.join(OUT,"K14")) else os.path.join(OUT,"K14_summary.json"),"w"),indent=2)
print(json.dumps(s,indent=2))
