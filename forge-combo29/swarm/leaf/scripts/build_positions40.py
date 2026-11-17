"""40 ordinary positions: the 8 bench FENs + 32 from real opening lines, all at
ordinary clocks (0-8). Printed one per line with a stable index."""
BENCH = [
 "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
 "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
 "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
 "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
 "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
 "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
 "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
 "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
]
LINES = [
 "e2e4 e7e5","e2e4 c7c5","d2d4 d7d5","d2d4 g8f6","c2c4 e7e5","g1f3 d7d5",
 "e2e4 e7e6","e2e4 c7c6","d2d4 g7g6","c2c4 c7c5","e2e4 d7d5","d2d4 e7e6",
 "g1f3 g8f6","c2c4 g8f6","e2e4 g8f6","d2d4 d7d6","e2e4 e7e5 g1f3","d2d4 d7d5 c2c4",
 "e2e4 c7c5 g1f3","d2d4 g8f6 c2c4","e2e4 e7e5 g1f3 b8c6","d2d4 d7d5 c2c4 e7e6",
 "c2c4 e7e5 b1c3","e2e4 c7c6 d2d4","d2d4 g7g6 c2c4","g1f3 d7d5 g2g3","e2e4 e7e6 d2d4",
 "e2e4 c7c5 b1c3","d2d4 g8f6 g1f3","c2c4 c7c5 g1f3","e2e4 d7d5 e4d5","d2d4 e7e6 e2e4",
 "e2e4 e7e5 f2f4","d2d4 f7f5",
]
import chess, json
out=[]
for f in BENCH: out.append({"kind":"bench","posline":f"position fen {f}"})
for mv in LINES:
    out.append({"kind":"line","posline":f"position startpos moves {mv}"})
out = out[:40]
assert len(out)==40, len(out)
json.dump(out, open("positions40.json","w"), indent=1)
for i,o in enumerate(out): print(i, o["posline"][:88])
