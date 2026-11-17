#!/usr/bin/env python3
"""Find the FEN the §1b/3aa matrix figures were measured on.

The seat reported `go depth 1` -> 41 nodes and `go depth 5` -> 896 nodes on a
"midgame" position with OwnBook false. Node counts are position-dependent, so a
cross-check of their table needs the same board. This scans a handful of
plausible boards (and a depth ladder for each) and prints the ones whose depth-1
line reads 41 nodes.
"""

from __future__ import annotations

import sys

from go_probe import run_cell

CANDIDATES = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 0 1",
    "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N1PN2/PPPP1PPP/R1BQ1RK1 b kq - 1 1",
    "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
    "rnbqkb1r/pp2pppp/2p2n2/3p4/2PP4/2N2N2/PP2PPPP/R1BQKB1R w KQkq - 0 5",
    "r4rk1/1pp1qppp/p1np1n2/4p1B1/2B1P1b1/2NP1N2/PPP1QPPP/R4RK1 w - - 0 10",
    "r1bqk2r/ppp2ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQK2R w KQkq - 0 6",
    "rnbq1rk1/ppp1ppbp/3p1np1/8/2PPP3/2N2N2/PP2BPPP/R1BQK2R w KQ - 0 6",
]


def main() -> int:
    exe = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/build/base/forge"
    for fen in CANDIDATES:
        one = run_cell(exe, "go depth 1", fen)
        five = run_cell(exe, "go depth 5", fen)
        flag = "  <== 41/896 MATCH" if (one.last_nodes == 41 and five.last_nodes == 896) else ""
        print(f"{one.last_nodes!s:>5} / {five.last_nodes!s:>5}   depth5 move {five.bestmove}   {fen}{flag}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
