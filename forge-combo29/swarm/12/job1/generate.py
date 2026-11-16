#!/usr/bin/env python3
"""generate.py SEED OUTDIR — write the UCI command sequences for area 2 job 1.

2,000 sequences of 5..30 lines from the grammar in the brief, each ending isready + quit.
Every sequence is written to OUTDIR/seq_<n>.txt (one line per UCI line) so the same
bytes can be replayed; the grammar decisions are printed to stdout for the record.
"""
import random
import sys
from pathlib import Path

OPTIONS = [
    ("Hash", "spin", 1, 2048), ("Threads", "spin", 1, 256), ("MultiPV", "spin", 1, 8),
    ("Move Overhead", "spin", 0, 1000), ("Ponder", "check", None, None),
    ("OwnBook", "check", None, None), ("Book File", "string", None, None),
    ("Book Depth", "spin", 0, 100), ("Book Variety", "spin", 0, 100),
    ("UseNNUE", "check", None, None), ("NnueFile", "string", None, None),
    ("ContHist4PlyRead", "check", None, None), ("NonPawnCorrection", "check", None, None),
    ("LmrDeeperShallower", "check", None, None), ("EvalRule50Damp", "check", None, None),
    ("ThreatHistory", "check", None, None), ("LmrSignedCorrection", "check", None, None),
    ("LmrLateParentRelief", "check", None, None), ("HindsightDepth", "check", None, None),
    ("NullThreatVerify", "check", None, None), ("NullSeeVeto", "check", None, None),
    ("AspCappedReopen", "check", None, None), ("AspArmLate", "check", None, None),
    ("EvasionOrdering", "check", None, None), ("DeadMaterial", "check", None, None),
    ("QuietExtinction", "check", None, None), ("DrawJitter", "spin", 0, 8),
    ("TmFinishIteration", "check", None, None), ("TmNodeShare", "check", None, None),
    ("SoundMatePruning", "check", None, None), ("LmrQuietBase", "spin", 0, 300),
    ("LmrQuietDivisor", "spin", 100, 500), ("LmrNoisyBase", "spin", 0, 300),
    ("LmrNoisyDivisor", "spin", 100, 800), ("NullMoveMinDepth", "spin", 1, 10),
    ("NullMoveBase", "spin", 1, 6), ("NullMoveDepthDivisor", "spin", 1, 10),
    ("NullMoveEvalDivisor", "spin", 50, 1000), ("RfpDepth", "spin", 0, 15),
    ("RfpMargin", "spin", 10, 300), ("RfpImproving", "spin", 0, 200),
    ("RazorDepth", "spin", 0, 6), ("RazorBase", "spin", 0, 1000),
    ("RazorMultiplier", "spin", 0, 1000), ("FutilityDepth", "spin", 0, 15),
    ("FutilityBase", "spin", 0, 500), ("FutilityMultiplier", "spin", 0, 500),
    ("LmpBase", "spin", 0, 20), ("HistoryPruneDepth", "spin", 0, 10),
    ("HistoryPruneMultiplier", "spin", 0, 20000), ("SeeQuietMultiplier", "spin", 0, 200),
    ("SeeNoisyMultiplier", "spin", 0, 1000), ("SingularDepth", "spin", 2, 20),
    ("SingularMargin", "spin", 0, 10), ("IirDepth", "spin", 1, 20),
    ("ProbcutDepth", "spin", 1, 20), ("ProbcutMargin", "spin", 0, 1000),
    ("QsFutilityMargin", "spin", 0, 1000), ("QsSeeMargin", "spin", 0, 500),
    ("AspirationDelta", "spin", 4, 200), ("HistoryBonusQuadratic", "spin", 0, 100),
    ("HistoryBonusLinear", "spin", 0, 500), ("HistoryBonusMax", "spin", 100, 10000),
    ("LmrHistoryDivisor", "spin", 1000, 30000), ("CheckExtensionDepth", "spin", 1, 30),
    ("LmrCutoffThreshold", "spin", 0, 20), ("MaterialCorrectionWeight", "spin", 0, 300),
    ("TmSoftDivisor", "spin", 5, 80), ("TmIncrementPercent", "spin", 0, 150),
    ("TmHardPercent", "spin", 10, 95), ("TmHardSoftMultiple", "spin", 1, 20),
    ("TmStableFactor", "spin", 20, 150), ("TmSemiStableFactor", "spin", 20, 150),
    ("TmUnstableFactor", "spin", 50, 300), ("TmEffortBase", "spin", 100, 250),
    ("TmFallingEvalPercent", "spin", 0, 400), ("TmMinFactorPercent", "spin", 10, 100),
    ("CaptureFutilityBase", "spin", 0, 1000), ("CaptureFutilityMultiplier", "spin", 0, 1000),
    ("CaptureFutilityDepth", "spin", 0, 15), ("FailLowContinuationBonus", "spin", 0, 300),
    ("Clear Hash", "button", None, None),
]

FENS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r2q1r1k/2p1bppp/p1np1n2/1p2P3/4P3/1NN1B3/PPP2PPP/R2Q1RK1 w - - 0 10",
    "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1",
    "8/8/8/8/8/k7/p7/K7 b - - 0 1",
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 99 200",
    "2r3k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1",
]
# a legal, legal-then-illegal, and a garbage move list
MOVES = [
    "e2e4 e7e5 g1f3 b8c6",
    "d2d4 d7d5 c2c4 e7e6 b1c3 g8f6",
    "e2e4 e7e5 e1e3",
    "a2a3 a7a6 h2h3 h7h6 g2g4 g7g5 d2d3 d7d6",
    "e2e5",
    "g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8",
]
GARBAGE = ["hello", "ucix", "isready now", "setoption", "go bananas", "position",
           "position fen", "position startpos moves", "stop now", "ponderhit extra",
           "setoption name", "setoption name NoSuchOption value 1", "go depth", "   ",
           "go depth 0", "register later", "debug on", "ucinewgame x"]


def choose_option(rng):
    name, kind, lo, hi = rng.choice(OPTIONS)
    if kind == "button":
        return f"setoption name {name}"
    if kind == "check":
        value = rng.choice(["true", "false", "true", "false", "maybe", "TRUE"])
    elif kind == "spin":
        if rng.random() < 0.12:
            value = rng.choice(["0", "1", "-1", "99999", "abc", "", "2049", "4294967296"])
        else:
            value = str(rng.randint(lo, hi))
    else:
        value = rng.choice(["", "<empty>", "/tmp/x.bin", "a b c", "12345"])
    if rng.random() < 0.07:
        return f"setoption name {name}"           # value left out on purpose
    return f"setoption name {name} value {value}".rstrip()


def choose_position(rng):
    kind = rng.random()
    if kind < 0.5:
        line = "position startpos"
    else:
        fen = rng.choice(FENS)
        if rng.random() < 0.1:                    # deliberately broken FEN
            fen = fen.replace(" w ", " w KQ ", 1) if rng.random() < 0.3 else fen + " x9"
        line = f"position fen {fen}"
    if rng.random() < 0.65:
        line += " moves " + rng.choice(MOVES)
    return line


def choose_go(rng):
    kind = rng.random()
    if kind < 0.25:
        return f"go depth {rng.randint(1, 6)}"
    if kind < 0.42:
        return f"go nodes {rng.randint(1, 50000)}"
    if kind < 0.62:
        return f"go movetime {rng.randint(1, 50)}"
    if kind < 0.72:
        return "go infinite"
    if kind < 0.80:
        return "go ponder depth " + str(rng.randint(1, 5))
    if kind < 0.88:
        return rng.choice(["go wtime 1000 btime 1000", "go wtime 50 btime 50 winc 0 binc 0",
                           "go wtime 100 btime 100 winc 1 binc 1", "go movestogo 3 wtime 200 btime 200"])
    return rng.choice(["go", "go depth 1 searchmoves e2e4", "go perft 1"])


def one_sequence(rng):
    lines = ["uci"]
    body = rng.randint(3, 26)
    pending_go = False
    for _ in range(body):
        r = rng.random()
        if pending_go and r < 0.45:
            lines.append(rng.choice(["stop", "stop", "ponderhit"]))
            pending_go = False
        elif r < 0.10:
            lines.append("isready")
        elif r < 0.20:
            lines.append("ucinewgame")
        elif r < 0.42:
            lines.append(choose_option(rng))
        elif r < 0.62:
            lines.append(choose_position(rng))
        elif r < 0.82:
            lines.append(choose_go(rng))
            pending_go = True
        elif r < 0.92:
            lines.append(rng.choice(["stop", "ponderhit"]))
        else:
            lines.append(rng.choice(GARBAGE))
    lines += ["isready", "quit"]
    return lines


def main():
    seed = int(sys.argv[1])
    outdir = Path(sys.argv[2])
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 2000
    outdir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    total = 0
    for n in range(count):
        seq = one_sequence(rng)
        (outdir / f"seq_{n:04d}.txt").write_text("\n".join(seq) + "\n")
        total += len(seq)
    print(f"seed {seed}: wrote {count} sequences, {total} UCI lines, into {outdir}")


if __name__ == "__main__":
    main()
