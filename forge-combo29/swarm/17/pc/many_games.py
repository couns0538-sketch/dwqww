#!/usr/bin/env python3
"""seat 17: 30 match-clock games at 6 s + 0.06 — is a forfeit possible at all?

Reuses the validated driver from matchclock.py (read to bestmove, no pipelined quit).
Each game starts from a different real middlegame and plays up to 60 plies; the clock is debited by the
WALL time of each move and credited the increment. A move whose wall time exceeds that side's remaining
clock is a forfeit.

Writes one JSON per game as it finishes (so a cut-off loses at most one game) plus a running summary.

usage: many_games.py <exe> <outdir> <games> [plies]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matchclock as M

# 30 real middlegames taken from set G (the same file the rest of my work uses).
FENS = [
    "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1",
    "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1",
    "6k1/p4r1p/1p2Q3/2p5/2P1N3/1P3P2/PK6/6q1 b - - 0 1",
    "2r4r/pp4k1/3q2p1/3ppn2/1P4QP/P2P1N2/R4P2/4RK2 b - - 0 1",
    "8/6k1/3p4/3P2PP/4KP2/4N3/8/8 w - - 0 1",
    "8/5p2/8/pp1pkpKp/7P/2P3P1/1P6/8 w - - 0 1",
    "r1bqkb1r/pppp1ppp/2n2n2/5N2/3P4/2PB4/PP3PPP/RNBQ1RK1 b kq - 0 1",
    "R7/8/8/5p1p/5K1P/1kpr2n1/8/8 b - - 0 1",
    "r1bq1rk1/pp2ppbp/2np1np1/8/2BNP3/2N1BP2/PPPQ2PP/R3K2R w KQ - 0 1",
    "2rq1rk1/pp1bbppp/2n1pn2/3p4/3P1B2/2NB1N2/PP3PPP/R2Q1RK1 w - - 0 1",
    "r4rk1/1pp2ppp/p1nb4/3q4/3P4/2NB1N2/PP3PPP/R2Q1RK1 w - - 0 1",
    "3rr1k1/pp3ppp/2n1b3/2pq4/8/2NBBN2/PP3PPP/R2Q1RK1 w - - 0 1",
    "1k1r3r/ppp2ppp/8/8/3b4/8/PPP2PPP/1K1R3R w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/1q4K1 b - - 0 1",
    "3q1rk1/5ppp/8/8/8/8/5PPP/1R3RK1 w - - 0 1",
    "2kr3r/ppp2ppp/2n5/8/8/2N5/PPP2PPP/2KR3R w - - 0 1",
    "r2q1rk1/pp1n1ppp/2pb4/8/2BP4/2N2N2/PP3PPP/R2Q1RK1 w - - 0 1",
    "8/8/4k3/8/8/4K3/4P3/8 w - - 0 1",
    "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1",
    "8/2k5/8/8/3P4/8/2K5/8 w - - 0 1",
    "r1b1k2r/pppp1ppp/2n2q2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQ1RK1 w kq - 0 1",
    "r2qk2r/ppp2ppp/2np1n2/2b1p1B1/2B1P3/2NP1N2/PPP2PPP/R2Q1RK1 w kq - 0 1",
    "2r2rk1/1bqnbppp/p2ppn2/1p6/3NPP2/1BN1B3/PPPQ2PP/2RR2K1 w - - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
    "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
    "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10",
    "8/5k2/8/8/8/8/2K5/8 w - - 0 1",
    "7k/8/8/8/8/8/8/K6R w - - 0 1",
]


def main():
    exe, outdir, games = sys.argv[1], sys.argv[2], int(sys.argv[3])
    plies = int(sys.argv[4]) if len(sys.argv) > 4 else 60
    os.makedirs(outdir, exist_ok=True)
    done = 0
    agg = {"games": 0, "plies": 0, "forfeits": 0, "illegal": 0, "min_clock_ms": None,
           "max_wall_ms": 0, "per_game": []}
    for gi in range(min(games, len(FENS))):
        M.START_FEN = FENS[gi]
        rows, w, b = M.play(exe, plies, outdir)
        os.replace(os.path.join(outdir, "game.log"), os.path.join(outdir, "game_%02d.log" % gi))
        walls = [r["wall_ms"] for r in rows if "wall_ms" in r and not r.get("forfeit")]
        forfeits = [r for r in rows if r.get("forfeit")]
        illegal = [r for r in rows if "illegal" in r.get("note", "")]
        clocks = [r["clock_before_ms"] for r in rows if "clock_before_ms" in r]
        entry = {"game": gi, "start": FENS[gi], "plies": len(rows),
                 "forfeits": len(forfeits), "illegal": len(illegal),
                 "min_clock_ms": min(clocks) if clocks else None,
                 "median_wall_ms": sorted(walls)[len(walls) // 2] if walls else None,
                 "max_wall_ms": max(walls) if walls else None,
                 "white_left": w, "black_left": b,
                 "forfeit_rows": forfeits, "illegal_rows": illegal}
        agg["per_game"].append(entry)
        agg["games"] += 1
        agg["plies"] += len(rows)
        agg["forfeits"] += len(forfeits)
        agg["illegal"] += len(illegal)
        if clocks:
            agg["min_clock_ms"] = min(clocks) if agg["min_clock_ms"] is None else min(agg["min_clock_ms"], min(clocks))
        if walls:
            agg["max_wall_ms"] = max(agg["max_wall_ms"], max(walls))
        json.dump(agg, open(os.path.join(outdir, "many_games.json"), "w"), indent=1)
        print(json.dumps(entry), flush=True)
        done += 1
    print("SUMMARY", json.dumps({k: v for k, v in agg.items() if k != "per_game"}), flush=True)


if __name__ == "__main__":
    main()
