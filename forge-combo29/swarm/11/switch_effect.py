#!/usr/bin/env python3
"""switch_effect.py EXE — do the four PC20 SEARCH switches actually change the search?
Each switch is turned on ALONE against S14-only, at Threads 1, depth 10, on 40 G positions.
Reports: how many positions change bestmove, and how many change nodes. A switch that changes
NOTHING anywhere is either dead code or a no-op at this depth — worth knowing."""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chess
from ucio import Engine

EXE = sys.argv[1]
G = "positions/G_set_G.epd"
S14 = ["LmrQuietBase 93","LmrQuietDivisor 205","LmrNoisyBase 13","LmrNoisyDivisor 333",
       "LmrHistoryDivisor 5643","NullMoveBase 5","LmpBase 8","HistoryPruneMultiplier 2220",
       "HistoryBonusQuadratic 24","HistoryBonusLinear 54","HistoryBonusMax 2212",
       "SingularDepth 6","IirDepth 2","NonPawnCorrection true"]
BASE = S14 + ["Threads 1","Hash 16","OwnBook false"]
VARIANTS = [
    ("CuckooRep",   BASE + ["CuckooRep true"]),
    ("HistRework2", BASE + ["HistRework 2"]),
    ("TtPruneV2",   BASE + ["TtPruneV2 true"]),
    ("CorrHistV2",  BASE + ["CorrHistV2 true"]),
]

def opts(o):
    out=[]
    for x in o:
        n,_,v = x.partition(" ")
        out.append(f"setoption name {n} value {v}")
    return out

def search(fen, options, depth=10):
    e = Engine(EXE, options=opts(options), timeout=300); e.start()
    try:
        _,r = e.position(fen=fen)
        if r: return None
        infos,bm,_ = e.go(f"go depth {depth}")
        nodes=None
        for l in infos:
            m=re.search(r"nodes (\d+)",l)
            if m: nodes=int(m.group(1))
        return (bm,nodes)
    finally: e.quit()

fens=[]
with open(G) as f:
    for line in f:
        line=line.strip()
        if not line or line.startswith("#"): continue
        f=line.split(";")[0].strip().split(" ")[:6]
        if len(f)==6: fens.append(" ".join(f))
        if len(fens)>=40: break

print(f"exe {EXE}\nS14 baseline vs S14+ONE switch, depth 10, Threads 1, {len(fens)} G positions")
print("(a position counts as CHANGED if bestmove or nodes differ)\n")
baseline={}
for i,fen in enumerate(fens):
    baseline[i]=search(fen,BASE)
print(f"{'switch':13} {'move changed':>13} {'nodes changed':>14} {'both same':>10}")
for name,opt in VARIANTS:
    mc=nc=same=0
    for i,fen in enumerate(fens):
        r=search(fen,opt)
        b=baseline[i]
        if b is None or r is None: continue
        if r[0]!=b[0]: mc+=1
        if r[1]!=b[1]: nc+=1
        if r==b: same+=1
    print(f"{name:13} {mc:>13} {nc:>14} {same:>10}")
