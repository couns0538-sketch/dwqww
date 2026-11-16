#!/usr/bin/env python3
"""S02 AREA 2 job 1 — 2,000 random UCI command sequences against the engine.

Reads nothing from disk except an FEN list; writes the sequences to seqs.jsonl and the verdicts
to results.jsonl. Every sequence is reproduced by feeding its lines (seqs.jsonl) to the exe on stdin.

Grammar (fixed by the brief): uci, isready, ucinewgame, setoption with a real option name and a random
value or none, position startpos/fen with random legal or illegal moves, go depth 1..6 / nodes /
movetime 1..50 / infinite / ponder, stop, ponderhit, quit, garbage lines. Every sequence ends with
isready + quit.
"""
import json
import random
import sys

SEED = 201
SEQS = 2000

# The engine's real options, taken from its own `uci` answer (forge-combo29/swarm/02/job1/uci_answer.txt).
SPIN = [("Hash", 1, 2048), ("Threads", 1, 256), ("MultiPV", 1, 8), ("Move Overhead", 0, 1000),
        ("Book Depth", 0, 100), ("Book Variety", 0, 100), ("DrawJitter", 0, 60)]
CHECK = ["Ponder", "OwnBook", "UseNNUE", "NNUEArch", "ContHist4PlyRead", "NonPawnCorrection",
         "LmrDeeperShallower", "EvalRule50Damp", "ThreatHistory", "LmrSignedCorrection",
         "LmrLateParentRelief", "HindsightDepth", "NullThreatVerify", "NullSeeVeto",
         "AspCappedReopen", "AspArmLate", "EvasionOrdering", "DeadMaterial", "QuietExtinction",
         "TmFinishIteration", "TmNodeShare", "SoundMatePruning"]
STRING = ["Book File", "NnueFile", "NNUEArchFile"]
BUTTON = ["Clear Hash"]

GARBAGE = ["", "hello world", "go", "go depth", "go depth banana", "position", "position fen",
           "position startpos moves", "setoption name", "setoption value 3", "isread", "uciok",
           "bestmove e2e4", "debug on", "register later", "  ", "UCI", "IsReady",
           "setoption name Hash", "position fen 8/8/8/8/8/8/8/8 w - - 0 1",
           "go movetime", "go nodes", "go mate 2", "go infinite ponder",
           "\x00\x01\x02", "stop stop stop", "ponderhit", "board", "eval now",
           "uci uci", "isready isready", "setoption", "position startpos moves e2e4 e2e4"]

START_FENS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    "4k3/8/8/8/8/8/8/4K3 w - - 0 1",
    "8/8/8/8/8/8/8/8 w - - 0 1",
    "not a fen at all",
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 99",
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR x Qkq - 0 1",
]
ILLEGAL_MOVES = ["e2e5", "e2e4e4", "e1e1", "a1a8", "0000", "e7e5", "Ke2", "zzzz", "e2", "e2e4q",
                 "h7h8n", "a7a6a6"]


def legal_moves_of(fen):
    try:
        import chess
        b = chess.Board(fen)
        if not b.is_valid():
            return []
        return [m.uci() for m in b.legal_moves]
    except Exception:
        return []


def rand_setoption(rng):
    kind = rng.random()
    if kind < 0.45:
        name, lo, hi = rng.choice(SPIN)
        v = rng.choice([rng.randint(lo, hi), lo, hi, lo - 1, hi + 1, 0, -5, 10 ** 9])
        return f"setoption name {name} value {v}"
    if kind < 0.75:
        name = rng.choice(CHECK)
        return f"setoption name {name} value {rng.choice(['true', 'false', 'true', 'TRUE', 'on', 'off', '1', '0'])}"
    if kind < 0.87:
        name = rng.choice(STRING)
        return f"setoption name {name} value {rng.choice(['', 'x', '/tmp/nonexistent.nnue', 'a b c'])}"
    if kind < 0.93:
        return f"setoption name {rng.choice(BUTTON)}"
    name, lo, hi = rng.choice(SPIN)
    return f"setoption name {name}"  # no value at all


def rand_position(rng):
    fen = rng.choice(START_FENS)
    legal = legal_moves_of(fen)
    n = rng.choice([0, 1, 2, 3, 5, 8, 13])
    moves = []
    for _ in range(n):
        r = rng.random()
        if legal and r < 0.6:
            moves.append(rng.choice(legal))
        elif r < 0.85:
            moves.append(rng.choice(ILLEGAL_MOVES))
        elif r < 0.95:
            moves.append(rng.choice(legal) if legal else rng.choice(ILLEGAL_MOVES))
        else:
            moves.append("")
    if rng.random() < 0.5:
        head = "position startpos"
        if rng.random() < 0.15:
            head = "position startpos moves"
    else:
        head = f"position fen {fen}"
    body = " ".join(m for m in moves if m)
    return (head + " moves " + body).strip() if body else head


def rand_go(rng):
    r = rng.random()
    if r < 0.40:
        return f"go depth {rng.randint(1, 6)}"
    if r < 0.60:
        return f"go nodes {rng.choice([1, 10, 100, 500, 1000, 5000, 20000])}"
    if r < 0.78:
        return f"go movetime {rng.randint(1, 50)}"
    if r < 0.86:
        return "go infinite"
    if r < 0.92:
        return "go ponder depth 3"
    return rng.choice(["go", "go depth 0", "go depth -1", "go wtime 100", "go mate 1",
                       "go infinite ponder", "go searchmoves e2e4 depth 3", "go searchmoves depth 2"])


def make_sequence(rng):
    n = rng.randint(5, 30)
    lines = []
    for _ in range(n - 2):  # the last two are always isready + quit
        r = rng.random()
        if r < 0.12:
            lines.append("uci")
        elif r < 0.26:
            lines.append("isready")
        elif r < 0.34:
            lines.append("ucinewgame")
        elif r < 0.52:
            lines.append(rand_setoption(rng))
        elif r < 0.72:
            lines.append(rand_position(rng))
        elif r < 0.90:
            lines.append(rand_go(rng))
        elif r < 0.94:
            lines.append("stop")
        elif r < 0.97:
            lines.append("ponderhit")
        else:
            lines.append(rng.choice(GARBAGE))
    lines.append("isready")
    lines.append("quit")
    return lines


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "seqs.jsonl"
    rng = random.Random(SEED)
    with open(out, "w") as fh:
        for i in range(SEQS):
            fh.write(json.dumps({"id": i, "lines": make_sequence(rng)}) + "\n")
    print(f"wrote {SEQS} sequences to {out}")


if __name__ == "__main__":
    main()
