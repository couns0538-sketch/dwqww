"""Positions for the hash-gap grid.

Two sets, because they answer different questions.

SET_24 is the shape the earlier report used: 24 cells, i.e. 24 (position, budget)
pairs. The earlier seat did not record which positions, so this is NOT a
reproduction of their 178 cells; it is an independent set of the same shape and
size. Any count here is a count on this set.

SET_PRACTICAL is ordinary middlegame positions at depths a game actually reaches,
for the "is Hash 16 unsafe in play" question.

Every FEN was checked by the engine itself: a refused FEN raises, and a search
that emits no `info depth` line raises, so a mistyped position cannot enter a
result row silently.
"""

# Openings and early middlegames: the region a real game spends most of its time.
PRACTICAL = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
    "rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2",
    "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
    "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 6 5",
    "r1bq1rk1/pppp1ppp/2n2n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 0 8",
    "r1bq1rk1/ppp2ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 0 7",
    "r2q1rk1/ppp1ppbp/2np1np1/8/2PPP3/2N2N2/PP2BPPP/R1BQ1RK1 b - - 0 9",
    "r1bq1rk1/pp2ppbp/2np1np1/2p5/2P1P3/2NP1NP1/PP3PBP/R1BQ1RK1 b - - 0 10",
    "r2q1rk1/1pp2ppp/p1npbn2/8/2BPP3/2N2N2/PP3PPP/R2Q1RK1 w - - 0 11",
    "2rq1rk1/pp1bppbp/2np1np1/8/3NP3/1BN1BP2/PPPQ2PP/2KR3R b - - 5 12",
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "r1b2rk1/pp2qppp/2n2n2/2pp4/8/2NP1NP1/PP2PPBP/R1BQ1RK1 w - - 0 10",
    "3rr1k1/pp3ppp/2n1bn2/2qp4/8/1PN1PN2/PB1PBPPP/R2Q1RK1 w - - 0 13",
    "r1bq1r1k/pp2nppp/2n1p3/2ppP3/3P4/2PB1N2/PP3PPP/RNBQ1RK1 w - - 0 12",
]

# Tactical and endgame positions, where a wrong move is visible immediately.
SHARP = [
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
    "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    "8/8/8/8/8/6k1/6p1/6K1 w - - 0 1",
    "8/8/4k3/8/8/4K3/4P3/8 w - - 0 1",
    "8/k7/3p4/p2P1p2/P2P1P2/8/8/K7 w - - 0 1",
]

PRACTICAL_BUDGETS = [50000, 200000, 500000, 1000000, 2000000]
