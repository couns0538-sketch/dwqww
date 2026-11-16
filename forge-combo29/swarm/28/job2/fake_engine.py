#!/usr/bin/env python3
"""fake_engine.py MODE — a deliberately broken UCI engine, used to prove a harness can see faults.

Opus's Rule 1 (FABLE_TO_swarm_2): "'0 illegal moves / 0 sanitizer lines / 0 hangs / 0 differences'
counts only when the SAME harness, unchanged, counted one planted case: a fake engine that answers
`bestmove a1a8` to every `go`, a fake engine that never answers `readyok`..."

Modes:
  illegal   — answers `bestmove a1a8` to every `go` (illegal in almost every position)
  overrun   — answers a legal-looking move but SLEEPS well past the clock (a time loss)
  noanswer  — never prints bestmove (a hang)
  noready   — never prints readyok

Everything else is a normal UCI engine: uci/uciok, isready/readyok, setoption accepted silently,
ucinewgame, position, quit.
"""
import sys
import time

import chess

MODE = sys.argv[1] if len(sys.argv) > 1 else "illegal"
BOARD = None


def first_legal():
    if BOARD is None:
        return "e2e4"
    try:
        moves = list(BOARD.legal_moves)
    except Exception:
        return "e2e4"
    return moves[0].uci() if moves else "0000"


def out(s):
    sys.stdout.write(s + "\n")
    sys.stdout.flush()


for raw in sys.stdin:
    line = raw.strip()
    if line == "uci":
        out("id name Fake Engine (" + MODE + ")")
        out("id author seat 28 control")
        out("option name Move Overhead type spin default 10 min 0 max 1000")
        out("uciok")
    elif line == "isready":
        if MODE != "noready":
            out("readyok")
    elif line.startswith("setoption"):
        pass
    elif line == "ucinewgame":
        BOARD = None
    elif line.startswith("position"):
        parts = line.split()
        try:
            if "fen" in parts:
                i = parts.index("fen")
                fen = " ".join(parts[i + 1:i + 7])
                BOARD = chess.Board(fen)
            elif "startpos" in parts:
                BOARD = chess.Board()
            if "moves" in parts:
                for uci in parts[parts.index("moves") + 1:]:
                    BOARD.push(chess.Move.from_uci(uci))
        except Exception:
            pass
    elif line.startswith("go"):
        parts = line.split()
        if MODE == "overrun":
            # A 100 ms clock, and we take 300 ms: a real time loss a GUI would flag.
            time.sleep(0.3)
            out("info depth 1 score cp 0 nodes 20 time 300 pv " + first_legal())
            out("bestmove " + first_legal())
        elif MODE == "illegal":
            out("info depth 1 score cp 0 nodes 20 time 1 pv a1a8")
            out("bestmove a1a8")
        elif MODE == "noanswer":
            pass
        else:
            out("info depth 1 score cp 0 nodes 20 time 1 pv " + first_legal())
            out("bestmove " + first_legal())
    elif line == "quit":
        break
