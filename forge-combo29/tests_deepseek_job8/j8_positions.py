#!/usr/bin/env python3
"""Job 8 step 1: 200 mate-in-one positions, filtered so a blind first move is visibly wrong.

Positions: random legal positions of 6 to 20 men, seed 20261115, each with at least one
legal move that mates. For each the engine's FIRST generated legal move is recorded (via
`go perft 1`, which lists the moves in generation order); positions whose first move
mates are dropped, so a player that answers with the first legal move scores 0 of 200.

Usage: j8_positions.py <out.json> <seed> [count]
"""
import json
import queue
import random
import subprocess
import sys
import threading
import time

import chess

ENGINE = "/tmp/ds/build-release/forge"


class Engine:
    def __init__(self):
        self.proc = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.q = queue.Queue()
        threading.Thread(target=self._read, daemon=True).start()
        for c in ("setoption name Threads value 1", "setoption name Hash value 16",
                  "setoption name NNUEArch value false", "isready"):
            self.send(c)
        self.until("readyok", 120)

    def _read(self):
        for line in self.proc.stdout:
            self.q.put(line.rstrip("\n"))
        self.q.put(None)

    def send(self, c):
        self.proc.stdin.write(c + "\n")
        self.proc.stdin.flush()

    def until(self, needle, timeout):
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            try:
                line = self.q.get(timeout=remaining)
            except queue.Empty:
                return None
            if line is None:
                return None
            if line.startswith(needle):
                return line

    def first_generated_move(self, fen):
        """`go perft 1` prints one line per legal move, in generation order."""
        self.send(f"position fen {fen}")
        self.send("go perft 1")
        first = None
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            try:
                line = self.q.get(timeout=max(0.01, deadline - time.monotonic()))
            except queue.Empty:
                break
            if line is None:
                break
            if line.startswith("nodes "):
                break
            if first is None and ":" in line:
                first = line.split(":")[0].strip()
        return first

    def close(self):
        try:
            self.send("quit")
        except (BrokenPipeError, ValueError):
            pass
        try:
            self.proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()


def random_position(rng, min_men=6, max_men=20):
    for _ in range(20000):
        target = rng.randint(min_men, max_men)
        board = chess.Board(None)
        squares = rng.sample(range(64), target)
        wk, bk = squares[0], squares[1]
        if chess.square_distance(wk, bk) < 2:
            continue
        board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        pool = ([chess.Piece(t, chess.WHITE) for t in
                 [chess.PAWN] * 8 + [chess.KNIGHT] * 2 + [chess.BISHOP] * 2 + [chess.ROOK] * 2 + [chess.QUEEN]]
                + [chess.Piece(t, chess.BLACK) for t in
                   [chess.PAWN] * 8 + [chess.KNIGHT] * 2 + [chess.BISHOP] * 2 + [chess.ROOK] * 2 + [chess.QUEEN]])
        rng.shuffle(pool)
        ok = True
        for sq, piece in zip(squares[2:], pool):
            if piece.piece_type == chess.PAWN and chess.square_rank(sq) in (0, 7):
                ok = False
                break
            board.set_piece_at(sq, piece)
        if not ok:
            continue
        board.turn = rng.choice([chess.WHITE, chess.BLACK])
        board.castling_rights = 0
        board.ep_square = None
        board.halfmove_clock = 0
        board.turn = not board.turn
        if board.is_check():
            continue
        board.turn = not board.turn
        if not board.is_valid() or board.is_game_over():
            continue
        return board
    return None


def mating_moves(board):
    out = []
    for m in board.legal_moves:
        board.push(m)
        if board.is_checkmate():
            out.append(m.uci())
        board.pop()
    return out


def main():
    out_path, seed = sys.argv[1], int(sys.argv[2])
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 200
    rng = random.Random(seed)
    eng = Engine()
    kept = []
    dropped_first_mates = 0
    attempts = 0
    while len(kept) < count and attempts < 400000:
        attempts += 1
        board = random_position(rng)
        if board is None:
            continue
        mm = mating_moves(board)
        if not mm:
            continue
        fen = board.fen()
        first = eng.first_generated_move(fen)
        if first is None:
            continue
        if first in mm:
            dropped_first_mates += 1
            continue
        kept.append({"fen": fen, "mating_moves": mm, "first_generated": first,
                     "men": len(board.piece_map())})
        if len(kept) % 25 == 0:
            print(f"  {len(kept)}/{count}", flush=True)
    eng.close()
    with open(out_path, "w") as f:
        json.dump(kept, f, indent=1)
    print(json.dumps({"positions": len(kept), "attempts": attempts,
                      "dropped_because_first_move_mates": dropped_first_mates}))


if __name__ == "__main__":
    main()
