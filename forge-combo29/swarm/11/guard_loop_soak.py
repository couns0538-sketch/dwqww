#!/usr/bin/env python3
"""guard_loop_soak.py EXE — the realistic shape: ONE guard, many games, faults injected periodically.
My earlier guard tests were single scenarios. A training run is a loop. Does recovery COMPOSE —
i.e. after 20 recoveries is the guard still correct, still fast, still leak-free?"""
import sys, time, random
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from uci_guard import UciGuard, PositionRejected
from pc20 import PC20_LINES
EXE=sys.argv[1]
GAMES=int(sys.argv[2]) if len(sys.argv)>2 else 40
rng=random.Random(1101)
BAD_FENS=["4k3/8/8/8/8/8/8/4K3 w - -",          # truncated
          "4k3/8/8/8/8/8/8/3KK3 w - - 0 1",      # two kings
          "8/8/8/8/8/8/8/8 w - - 0 1"]           # empty
g=UciGuard(EXE, options=PC20_LINES).start()
played=0; rejected=0; illegal=0; worst=0.0
t_all=time.monotonic()
try:
    for n in range(1,GAMES+1):
        # every 5th game is a FAULT game: a bad FEN instead of a real one
        fault = (n % 5 == 0)
        b=chess.Board()
        if fault:
            bad=rng.choice(BAD_FENS)
            try:
                g.set_position(fen=bad)
                print(f"  game {n}: UNEXPECTED — bad FEN accepted: {bad[:30]}")
            except PositionRejected:
                rejected+=1
            continue          # skip this game, as the documented protocol says
        # a real short game
        for _ in range(rng.randrange(3,12)):
            lm=list(b.legal_moves)
            if not lm or b.is_game_over(claim_draw=False): break
            b.push(rng.choice(lm))
        t0=time.monotonic()
        g.set_position(fen=None, startpos_moves=[m.uci() for m in b.move_stack])
        mv=g.bestmove(depth=8)
        worst=max(worst, time.monotonic()-t0)
        if mv and mv!="0000":
            if chess.Move.from_uci(mv) not in b.legal_moves: illegal+=1
            else: played+=1
finally:
    g.stop()
print(f"\n  games attempted {GAMES}, real positions played {played}, rejected (faults) {rejected}, illegal {illegal}")
print(f"  slowest search+recovery {worst*1000:.0f} ms, wall {time.monotonic()-t_all:.1f}s")
print(f"  recoveries composed correctly: {rejected == GAMES//5} (expected {GAMES//5})")
