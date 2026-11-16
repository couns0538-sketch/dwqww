#!/usr/bin/env python3
"""make_stress_sessions.py - UCI sessions that exercise the code paths read in job 1 while a
search is running: Threads 2/4, MultiPV 2/3, the unlisted tuning options, and stop/ucinewgame
issued from stdin while `go infinite` runs (the UCI loop's stop_search path).

Sessions end with quit. The engine reads stdin on its main thread while the search runs on the
worker thread, so the interleaving is the engine's own, not the driver's.
"""
import argparse
import os
import random
import sys

OPTS_TRUE = ["ContHist4PlyRead", "NonPawnCorrection", "LmrDeeperShallower", "EvalRule50Damp",
             "ThreatHistory", "LmrSignedCorrection", "LmrLateParentRelief", "HindsightDepth",
             "NullThreatVerify", "NullSeeVeto", "AspCappedReopen", "AspArmLate", "EvasionOrdering",
             "DeadMaterial", "QuietExtinction", "TmFinishIteration", "TmNodeShare", "SoundMatePruning"]
SPINS = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
         ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
         ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
         ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2)]
FENS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "4k3/8/8/8/8/8/8/4K3 w - - 0 1",
    "2K2r2/4P3/8/8/8/8/8/3k4 w - - 0 1",
    "4k3/8/8/8/8/8/8/4K2R w - - 100 60",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--seed", type=int, default=2701)
    ap.add_argument("--sessions", type=int, default=40)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    os.makedirs(args.outdir, exist_ok=True)

    for s in range(args.sessions):
        lines = ["uci", "isready",
                 "setoption name Hash value %d" % rng.choice([1, 16, 64]),
                 "setoption name Threads value %d" % rng.choice([1, 2, 4]),
                 "setoption name MultiPV value %d" % rng.choice([1, 2, 3])]
        # S14 plus a few option flips, always through setoption + isready
        for name, val in SPINS:
            lines += ["setoption name %s value %d" % (name, val)]
        for name in rng.sample(OPTS_TRUE, 4):
            lines += ["setoption name %s value true" % name]
        lines += ["isready", "ucinewgame", "isready"]
        for _ in range(rng.randint(2, 5)):
            fen = rng.choice(FENS)
            lines.append("position fen " + fen)
            lines.append("isready")
            kind = rng.choice(["depth", "nodes", "movetime", "infinite_then_stop", "clock"])
            if kind == "depth":
                lines.append("go depth %d" % rng.randint(1, 9))
            elif kind == "nodes":
                lines.append("go nodes %d" % rng.choice([0, 1, 26, 500, 5000]))
            elif kind == "movetime":
                lines.append("go movetime %d" % rng.randint(1, 60))
            elif kind == "clock":
                lines.append("go wtime %d btime %d winc 10 binc 10" % (rng.randint(50, 3000),
                                                                      rng.randint(50, 3000)))
            else:
                lines.append("go infinite")
                lines.append("stop")
            lines.append("isready")
        # a search interrupted by ucinewgame, then a normal one
        lines += ["position startpos", "isready", "go infinite", "ucinewgame", "isready",
                  "position startpos", "isready", "go depth 6", "isready", "quit"]
        with open(os.path.join(args.outdir, "stress_%03d.uci" % s), "w") as f:
            f.write("\n".join(lines) + "\n")
    print("wrote %d stress sessions to %s" % (args.sessions, args.outdir))


if __name__ == "__main__":
    sys.exit(main())
