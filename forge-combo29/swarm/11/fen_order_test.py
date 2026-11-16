#!/usr/bin/env python3
"""fen_order_test.py EXE BUILD — FEN castling-field ORDER and duplicate handling, PC20, Threads 1.
FEN is a six-field string; the castling field is a SET in practice, but the spec shows KQkq order.
Test whether non-canonical order is accepted and whether it changes the board."""
import os,re,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
BASE="r3k2r/8/8/8/8/8/8/R3K2R w {c} - 0 1"
CASES=["KQkq","kqKQ","QKqk","qkQK","KQ","QK","kq","qk","Kq","qK","KQk","kKQ","KQkqK"]
def perft1(fen):
    e=Engine(EXE,options=PC20_LINES,timeout=120); e.start()
    try:
        _,r=e.position(fen=fen)
        if r: return ("REFUSED", r[0] if r else "?")
        e.send("go perft 1"); lines=e.read_until("nodes ")
        for l in lines:
            m=re.match(r"nodes (\d+)",l)
            if m: return ("OK", int(m.group(1)))
        return ("MEASUREMENT FAILED no nodes", None)
    finally: e.quit()
print(f"build {BUILD}  board {BASE.format(c='<c>')}")
print(f"{'castling field':16} {'result':10} value")
groups={}
for c in CASES:
    st,v = perft1(BASE.format(c=c))
    print(f"{repr(c):16} {st:10} {v}")
    if st=="OK": groups.setdefault(v,[]).append(c)
print("\n=== reading ===")
for v,cs in groups.items():
    print(f"  perft 1 = {v} for {cs}")
print("  -> two orders of the SAME rights set giving different counts would be a defect;")
print("     orders that group together show the field is treated as a set.")
