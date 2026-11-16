#!/usr/bin/env python3
"""guard_clock_loop.py EXE — the guard's SECOND rule under repetition: does bestmove() keep refusing
one-sided clocks after many calls, and do clock searches through the guard stay stable?
S-F99 tested repeated FEN faults; this tests repeated CLOCK use, which is what a match actually does."""
import sys, time
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from uci_guard import UciGuard
from pc20 import PC20_LINES
EXE=sys.argv[1]; GAMES=int(sys.argv[2]) if len(sys.argv)>2 else 20
g=UciGuard(EXE, options=PC20_LINES).start()
FEN="rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
refusals=0; ok=0; illegal=0; walls=[]
try:
    for n in range(1,GAMES+1):
        g.set_position(fen=FEN)
        # every 4th call: try a one-sided clock, which MUST be refused
        if n % 4 == 0:
            try:
                g.bestmove(wtime=6000)
                print(f"  call {n}: UNEXPECTED — one-sided clock accepted")
            except ValueError:
                refusals+=1
            continue
        t0=time.monotonic()
        mv=g.bestmove(wtime=6000, btime=6000, winc=60, binc=60)
        walls.append((time.monotonic()-t0)*1000)
        if mv and mv!="0000":
            if chess.Move.from_uci(mv) in chess.Board(FEN).legal_moves: ok+=1
            else: illegal+=1
finally:
    g.stop()
print(f"\n  calls {GAMES}: clock searches ok {ok}, one-sided refused {refusals} (expected {GAMES//4}), illegal {illegal}")
if walls:
    print(f"  wall ms: min {min(walls):.0f} median {sorted(walls)[len(walls)//2]:.0f} max {max(walls):.0f}")
print(f"  both rules held under repetition: {illegal==0 and refusals==GAMES//4}")
