#!/usr/bin/env python3
"""fen_truncation.py EXE BUILD — every way a FEN can be short or long, on PC20, Threads 1.
For each: is it refused, and does the engine keep the PREVIOUS board (perft-1 tells us which)?"""
import os,re,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
OLD="r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"          # 26 moves
OLD_CNT=chess.Board(OLD).legal_moves.count()
CASES=[
 ("full 6 fields",            "4k3/8/8/8/8/8/8/4K3 w - - 0 1", "accepted"),
 ("5 fields (no fullmove)",   "4k3/8/8/8/8/8/8/4K3 w - - 0",   "refused"),
 ("4 fields",                 "4k3/8/8/8/8/8/8/4K3 w - -",     "refused"),
 ("3 fields",                 "4k3/8/8/8/8/8/8/4K3 w -",       "refused"),
 ("1 field",                  "4k3/8/8/8/8/8/8/4K3",           "refused"),
 ("empty after fen",          "",                              "refused?"),
 ("7 fields",                 "4k3/8/8/8/8/8/8/4K3 w - - 0 1 x","reported?"),
]
def probe(target):
    e=Engine(EXE,options=PC20_LINES,timeout=120); e.start()
    try:
        _,r0=e.position(fen=OLD)
        if r0: raise SystemExit("OLD refused")
        e.send(("position fen "+target) if target else "position fen")
        e.send("isready"); sync=e.read_until("readyok")
        refusal=[l for l in sync if "invalid" in l or "illegal" in l]
        e.send("go perft 1"); lines=e.read_until("nodes ")
        n=None
        for l in lines:
            m=re.match(r"nodes (\d+)",l)
            if m: n=int(m.group(1))
        return refusal, n
    finally: e.quit()
print(f"build {BUILD}\nprevious board {OLD} has {OLD_CNT} legal moves\n")
print(f"{'case':26} {'refused?':9} {'perft1':>7}  board_kept")
for label,target,expect in CASES:
    ref,n=probe(target)
    kept = "PREVIOUS (stale)" if n==OLD_CNT else ("new board" if n is not None else "?")
    print(f"{label:26} {str(bool(ref)):9} {str(n):>7}  {kept}")
    if ref: print(f"    line: {ref[0]}")
