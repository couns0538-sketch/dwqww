#!/usr/bin/env python3
"""Job 7 part A1: the ladder. Won KQvK/KRvK starts against a weak and the best defender.

For each (class, defender, limit) cell: 200 won starts, the engine on the strong side
with `go <limit>`, `ucinewgame` before every game and none inside a game.

Counting, two kinds of repetition as Fable asked:
  * "third occurrence reached": the final position is `is_repetition(3)` - a match
    program ends the game there;
  * "only claimable": `can_claim_threefold_repetition()` is true but `is_repetition(3)`
    is not - the defender could claim but the position has not occurred three times.

The best defender picks a move with the LARGEST distance to mate from the DTM table.

Usage: j7a1.py <dtm.json> <class> <defender: weak|best> <limit> <out.json> <seed>
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
MAX_PLIES = 400


class Engine:
    def __init__(self, setopts=()):
        self.proc = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True, bufsize=1)
        self.q = queue.Queue()
        threading.Thread(target=self._read, daemon=True).start()
        self.send("setoption name Threads value 1")
        self.send("setoption name Hash value 16")
        self.send("setoption name NNUEArch value false")
        for name, value in setopts:
            self.send(f"setoption name {name} value {value}")
        self.send("isready")
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

    def best(self, pos, limit, timeout=300):
        self.send(pos)
        self.send(f"go {limit}")
        last = None
        depth = None
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                line = self.q.get(timeout=max(0.01, deadline - time.monotonic()))
            except queue.Empty:
                return None, last, depth
            if line is None:
                return None, last, depth
            if line.startswith("info") and " score " in line:
                last = line
                if " depth " in line:
                    try:
                        depth = int(line.split(" depth ")[1].split()[0])
                    except (IndexError, ValueError):
                        pass
            elif line.startswith("bestmove"):
                parts = line.split()
                return (parts[1] if len(parts) > 1 else None), last, depth

    def close(self):
        try:
            self.send("quit")
        except (BrokenPipeError, ValueError):
            pass
        try:
            self.proc.wait(timeout=60)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()


def class_key(board):
    return board.board_fen() + (" w" if board.turn else " b")


def dtm_of(board, dtm):
    kind = None
    men = [s for s in chess.SQUARES
           if board.piece_at(s) and board.piece_at(s).piece_type != chess.KING]
    if len(men) == 1:
        pt = board.piece_at(men[0]).piece_type
        kind = {chess.QUEEN: "KQvK", chess.ROOK: "KRvK"}.get(pt)
    if kind is None:
        return None
    return dtm[kind].get(class_key(board))


def strong_colour(board):
    for s in chess.SQUARES:
        piece = board.piece_at(s)
        if piece and piece.piece_type != chess.KING:
            return piece.color
    return None


def won_starts(kind, dtm, count, rng):
    strong = chess.QUEEN if kind == "KQvK" else chess.ROOK
    out, seen = [], set()
    guard = 0
    while len(out) < count and guard < count * 5000:
        guard += 1
        wk, bk, s = rng.sample(range(64), 3)
        if chess.square_distance(wk, bk) < 2:
            continue
        b = chess.Board(None)
        b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        b.set_piece_at(s, chess.Piece(strong, chess.WHITE))
        b.castling_rights = 0
        b.turn = chess.WHITE
        if not b.is_valid() or b.is_game_over():
            continue
        v = dtm[kind].get(class_key(b))
        if not v or v[0] != "W":
            continue
        fen = b.fen()
        if fen in seen:
            continue
        seen.add(fen)
        out.append(fen)
    return out


def defender_move(board, dtm, style, rng):
    """weak: random among moves that keep the defender's WDL best.
       best: a move with the largest resulting distance for the winner."""
    options = []
    for m in board.legal_moves:
        board.push(m)
        if board.is_checkmate():
            board.pop()
            continue
        if board.is_stalemate() or board.is_insufficient_material():
            board.pop()
            options.append((2, 0, m))
            continue
        v = dtm_of(board, dtm)
        board.pop()
        if v is None:
            options.append((1, 0, m))
            continue
        wdl, d = v
        rank = {"L": 3, "D": 2, "W": 1}[wdl]
        # The child is from the OPPONENT's view; a child "L" is best for us.
        options.append((rank, abs(d) if d else 0, m))
    if not options:
        return None
    best_rank = max(o[0] for o in options)
    pool = [o for o in options if o[0] == best_rank]
    if style == "best":
        max_d = max(o[1] for o in pool)
        pool = [o for o in pool if o[1] == max_d]
    return rng.choice(pool)[2]


def main():
    dtm_path, kind, style, limit, out_path, seed = sys.argv[1:7]
    rng = random.Random(int(seed))
    with open(dtm_path) as f:
        dtm = json.load(f)
    starts = won_starts(kind, dtm, 200, rng)
    eng = Engine()
    t0 = time.time()
    tally = {"starts": len(starts), "mated": 0, "third_occurrence": 0,
             "claimable_only": 0, "fifty": 0, "stalemate": 0, "other": 0,
             "no_bestmove": 0}
    mate_lengths = []
    games = []
    for fen in starts:
        board = chess.Board(fen)
        moves = []
        result = "other"
        for ply in range(MAX_PLIES):
            if board.is_checkmate():
                result = "mated"
                break
            if board.is_stalemate():
                result = "stalemate"
                break
            if board.halfmove_clock >= 100:
                result = "fifty"
                break
            if board.is_repetition(3):
                result = "third_occurrence"
                break
            if board.can_claim_threefold_repetition():
                result = "claimable_only"
                break
            if dtm_of(board, dtm) is None:
                result = "other"
                break
            strong = strong_colour(board)
            if board.turn == strong:
                pos = f"position fen {fen} moves " + " ".join(moves) if moves else f"position fen {fen}"
                mv, last, depth = eng.best(pos, limit)
                if mv is None:
                    result = "no_bestmove"
                    break
                try:
                    move = chess.Move.from_uci(mv)
                except ValueError:
                    result = "no_bestmove"
                    break
                if move not in board.legal_moves:
                    result = "no_bestmove"
                    break
            else:
                move = defender_move(board, dtm, style, rng)
                if move is None:
                    result = "other"
                    break
            board.push(move)
            moves.append(move.uci())
        tally[result] = tally.get(result, 0) + 1
        if result == "mated":
            mate_lengths.append(len(moves))
        elif len(games) < 20:
            games.append({"fen": fen, "result": result, "moves": moves})
    eng.close()
    out = {"class": kind, "defender": style, "limit": limit, "seed": int(seed),
           "tally": tally, "wall_s": round(time.time() - t0, 1),
           "mate_length_mean": (sum(mate_lengths) / len(mate_lengths)) if mate_lengths else None,
           "mate_length_max": max(mate_lengths) if mate_lengths else None,
           "example_games": games}
    with open(out_path, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "example_games"}))


if __name__ == "__main__":
    main()
