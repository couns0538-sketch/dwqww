#!/usr/bin/env python3
"""SYNTHETIC UCI engine for the S42 tests: score = deterministic hash of (placement, side to move) mapped to
[-250, 250] cp (White POV converted to side-to-move POV), bestmove = first legal move in UCI order. Not an engine."""
import hashlib
import sys

import chess


def score_white(board):
    h = int.from_bytes(hashlib.sha256((board.board_fen() + (" w" if board.turn else " b")).encode()).digest()[:4], "little")
    return (h % 501) - 250


def main():
    board = chess.Board()
    out = sys.stdout
    for raw in sys.stdin:
        line = raw.strip()
        if line == "uci":
            out.write("id name FakeForge S42\nid author test\noption name Threads type spin default 1 min 1 max 8\n"
                      "option name Hash type spin default 16 min 1 max 1024\nuciok\n")
        elif line == "isready":
            out.write("readyok\n")
        elif line.startswith("position"):
            parts = line.split()
            if parts[1] == "startpos":
                board = chess.Board(); rest = parts[2:]
            else:
                i = parts.index("moves") if "moves" in parts else len(parts)
                board = chess.Board(" ".join(parts[2:i])); rest = parts[i:]
            if rest and rest[0] == "moves":
                for u in rest[1:]:
                    board.push_uci(u)
        elif line.startswith("go"):
            parts = line.split(); depth = int(parts[parts.index("depth") + 1]) if "depth" in parts else 1
            w = score_white(board); stm = w if board.turn else -w
            moves = sorted(m.uci() for m in board.legal_moves)
            out.write(f"info depth {depth} score cp {stm} nodes {1000 + depth} pv {moves[0] if moves else '0000'}\n")
            out.write(f"bestmove {moves[0] if moves else '0000'}\n")
        elif line == "quit":
            break
        out.flush()


if __name__ == "__main__":
    main()
