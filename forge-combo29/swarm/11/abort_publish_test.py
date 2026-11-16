#!/usr/bin/env python3
"""abort_publish_test.py — ABORT_PUBLISH is shipped OFF; the source comment claims it is NOT a repair
(43 wins / 30 losses, avg 14 cp LOWER on the finished move). Test that claim independently: does the
move chosen under an exact-node stop differ between ships-OFF (/tmp/pcbuild) and switch-ON (/tmp/pconbuild)?"""
import sys,re
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
from ucio import Engine
from pc20 import PC20_LINES
SHIP="/tmp/pcbuild/forge"      # ABORT_PUBLISH 0
ON="/tmp/pconbuild/forge"      # ABORT_PUBLISH 1, everything else same
fens=[]
with open("positions/O_first200.fens") as f:
    for line in f:
        line=line.strip()
        if line: fens.append(line)
fens=fens[:40]
def run(exe,fen,N):
    e=Engine(exe,options=PC20_LINES,timeout=120); e.start()
    try:
        _,r=e.position(fen=fen)
        if r: return None
        infos,bm,_=e.go(f"go nodes {N}",timeout=30)
        return bm
    finally: e.quit()
print("ABORT_PUBLISH: shipped-OFF vs switch-ON, exact-node stops on 40 O positions\n")
for N in (50000,250000):
    diff=0; tot=0
    for fen in fens:
        a=run(SHIP,fen,N); b=run(ON,fen,N)
        if a is None or b is None: continue
        tot+=1
        if a!=b: diff+=1
    print(f"  go nodes {N:6}: move differs on {diff} of {tot} positions")
