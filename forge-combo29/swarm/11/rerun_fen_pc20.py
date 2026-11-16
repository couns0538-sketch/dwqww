#!/usr/bin/env python3
"""rerun_fen_pc20.py EXE BUILD — re-run seat 11's FEN-validation finds on a build under PC20.
Every value asserted; a missing node count aborts with no verdict."""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucio import Engine
from pc20 import PC20_LINES, describe

EXE = sys.argv[1]; BUILD = sys.argv[2] if len(sys.argv) > 2 else "?"
class ME(Exception): pass

def perft1(fen):
    e = Engine(EXE, options=PC20_LINES, timeout=180); e.start()
    try:
        ans, refused = e.position(fen=fen)
        if refused: return ("REFUSED", refused[0] if refused else "?")
        e.send("go perft 1"); lines = e.read_until("nodes ")
        for l in lines:
            m = re.match(r"nodes (\d+)", l)
            if m: return ("ACCEPTED", int(m.group(1)))
        raise ME(f"no nodes for {fen}")
    finally: e.quit()

print(f"build: {BUILD}\nsettings: {describe()}\n" + "="*90)

print("\n[S-F2] adjacent digits in a rank (5K11 vs canonical 5K2)")
for label, fen in (("5K11", "4k3/8/8/8/8/8/5K11/8 w - - 0 1"),
                   ("5K2 (canonical)", "4k3/8/8/8/8/8/5K2/8 w - - 0 1")):
    try: r = perft1(fen)
    except ME as exc: print(f"  {label:16} MEASUREMENT FAILED {exc}"); continue
    print(f"  {label:16} -> {r}")

print("\n[S-F13] en-passant field: only the legal ep square should be accepted")
BASE = "rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq {ep} 0 3"
for ep in ("d6", "e6", "e4", "d3", "a1", "h8"):
    try: r = perft1(BASE.format(ep=ep))
    except ME as exc: print(f"  ep={ep:3} MEASUREMENT FAILED {exc}"); continue
    print(f"  ep={ep:3} -> {r}")

print("\n[S-F14] castling rights: Q with no a1 rook must be refused")
for label, fen in (("all rights legal", "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"),
                   ("Q but no a1 rook", "r3k2r/8/8/8/8/8/8/4K2R w Q - 0 1"),
                   ("K with h1 rook (legal)", "r3k2r/8/8/8/8/8/8/4K2R w K - 0 1")):
    try: r = perft1(fen)
    except ME as exc: print(f"  {label:24} MEASUREMENT FAILED {exc}"); continue
    print(f"  {label:24} -> {r}")

print("\n[S-F16] piece inventory boundaries")
for label, fen in (("8P+3R (infeasible)", "4k3/8/8/8/8/8/PPPPPPPP/2RRK3 w - - 0 1"),
                   ("7P+2Q (feasible)",   "4k3/8/8/8/8/P7/PPPPPPP1/2QQK3 w - - 0 1"),
                   ("9 pawns (infeasible)","4k3/8/8/8/8/PPPPPPPPP/8/4K3 w - - 0 1")):
    try: r = perft1(fen)
    except ME as exc: print(f"  {label:24} MEASUREMENT FAILED {exc}"); continue
    print(f"  {label:24} -> {r}")

print("\n[S-F15] counter independence: halfmove 0 vs 100 must not change perft 1")
for hm in (0, 100):
    try: r = perft1(f"r3k2r/8/8/8/8/8/8/R3K2R w KQkq - {hm} 1")
    except ME as exc: print(f"  halfmove {hm} MEASUREMENT FAILED {exc}"); continue
    print(f"  halfmove {hm:3} -> {r}")
