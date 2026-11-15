#!/usr/bin/env python3
"""Job 6 part A2: whole games, the cost of A1's errors in real play.

Controls: KQvK and KRvK (every won start must be won). Measures: KBNvK and KQvKR are
NOT available (no Syzygy, and I solved only KQvK/KRvK/KPvK), so this runs KQvK, KRvK
and KPvK and says so.

The engine plays the winning side with `go nodes N`, the game given as
`position fen <start> moves ...` and NO ucinewgame between moves (as in a game).
The defender plays a tablebase move that holds out longest: among the defender's moves
that keep the defender's WDL as good as possible, pick the one whose resulting position
is a WIN for the strong side with the largest distance-to-win available in my table is
not available (my table is WDL only), so "holds out longest" is approximated by picking
a random legal move among those that do not lose immediately. This is stated as a
limitation: with WDL-only tables I cannot choose the maximally stubborn defence.

Usage: a2_games.py <tables.json> <classes> <nodes> <out.json> <seed>
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
MAX_PLIES = 300


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

    def best(self, fen, moves, nodes, timeout=300):
        pos = f"position fen {fen}"
        if moves:
            pos += " moves " + " ".join(moves)
        self.send(pos)
        self.send(f"go nodes {nodes}")
        last = None
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                line = self.q.get(timeout=max(0.01, deadline - time.monotonic()))
            except queue.Empty:
                return None, last
            if line is None:
                return None, last
            if line.startswith("info") and " score " in line:
                last = line
            elif line.startswith("bestmove"):
                parts = line.split()
                return (parts[1] if len(parts) > 1 else None), last

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


def kind_of(board):
    men = [s for s in chess.SQUARES
           if board.piece_at(s) and board.piece_at(s).piece_type != chess.KING]
    if len(men) != 1:
        return None
    pt = board.piece_at(men[0]).piece_type
    return {chess.QUEEN: "KQvK", chess.ROOK: "KRvK", chess.PAWN: "KPvK"}.get(pt)


def strong_colour(board):
    for s in chess.SQUARES:
        piece = board.piece_at(s)
        if piece and piece.piece_type != chess.KING:
            return piece.color
    return None


def wdl(board, tables):
    kind = kind_of(board)
    if kind is None or kind not in tables:
        return None
    return tables[kind].get(class_key(board))


def won_starts(kind, count, rng, tables):
    """`count` distinct positions of the class that are WON for the side to move."""
    strong = {"KQvK": chess.QUEEN, "KRvK": chess.ROOK, "KPvK": chess.PAWN}[kind]
    out, seen = [], set()
    guard = 0
    while len(out) < count and guard < count * 3000:
        guard += 1
        wk, bk, s = rng.sample(range(64), 3)
        if chess.square_distance(wk, bk) < 2:
            continue
        if strong == chess.PAWN and chess.square_rank(s) in (0, 7):
            continue
        sw = rng.random() < 0.5
        b = chess.Board(None)
        b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        b.set_piece_at(s, chess.Piece(strong, chess.WHITE if sw else chess.BLACK))
        b.castling_rights = 0
        b.ep_square = None
        b.halfmove_clock = 0
        b.turn = chess.WHITE if sw else chess.BLACK       # strong side to move
        if not b.is_valid() or b.is_game_over():
            continue
        if wdl(b, tables) != "W":
            continue
        fen = b.fen()
        if fen in seen:
            continue
        seen.add(fen)
        out.append(fen)
    return out


def defender_move(board, tables, rng):
    """A move for the side to move that keeps its WDL as good as possible."""
    order = {"W": 3, "D": 2, "L": 1}
    options = []
    for move in board.legal_moves:
        board.push(move)
        if board.is_checkmate():
            board.pop()
            continue                      # never available to a defender that is lost
        if board.is_stalemate():
            board.pop()
            options.append((2, move))     # a draw is the best a defender can do
            continue
        child = wdl(board, tables)
        board.pop()
        if child is None:
            # The class changed (capture/promotion). Judge by material:
            if board.is_insufficient_material():
                options.append((2, move))
            else:
                options.append((1, move))
            continue
        options.append((order[child], move))
    if not options:
        return None
    best = max(v for v, _ in options)
    return rng.choice([m for v, m in options if v == best])


def play_game(eng, start_fen, tables, nodes, rng):
    board = chess.Board(start_fen)
    moves = []
    result = "unfinished"
    for _ in range(MAX_PLIES):
        if board.is_checkmate():
            result = "mate"
            break
        if board.is_stalemate():
            result = "stalemate"
            break
        if board.can_claim_fifty_moves() or board.halfmove_clock >= 100:
            result = "fifty"
            break
        if board.can_claim_threefold_repetition():
            result = "repetition"
            break
        if board.is_insufficient_material():
            result = "insufficient"
            break
        strong = strong_colour(board) if kind_of(board) else None
        if strong is None:
            result = "class-changed"
            break
        if board.turn == strong:
            move_text, _last = eng.best(start_fen, moves, nodes)
            if move_text is None:
                result = "no-bestmove"
                break
            try:
                move = chess.Move.from_uci(move_text)
            except ValueError:
                result = "illegal"
                break
            if move not in board.legal_moves:
                result = "illegal"
                break
        else:
            move = defender_move(board, tables, rng)
            if move is None:
                result = "defender-stuck"
                break
        board.push(move)
        moves.append(move.uci())
    return result, moves


def main():
    tables_path, classes, nodes, out_path, seed = sys.argv[1:6]
    nodes = int(nodes)
    rng = random.Random(int(seed))
    with open(tables_path) as f:
        tables = json.load(f)
    classes = [c for c in classes.split(",") if c in tables]
    eng = Engine()
    out = {"nodes": nodes, "seed": int(seed), "classes": {}}
    t0 = time.time()
    for kind in classes:
        starts = won_starts(kind, 200, rng, tables)
        tally = {}
        not_won = []
        for fen in starts:
            result, moves = play_game(eng, fen, tables, nodes, rng)
            tally[result] = tally.get(result, 0) + 1
            if result != "mate":
                not_won.append({"fen": fen, "result": result, "moves": moves})
        out["classes"][kind] = {"starts": len(starts), "tally": tally,
                                "not_won": not_won}
        print(json.dumps({"class": kind, "starts": len(starts), "tally": tally}), flush=True)
    eng.close()
    out["wall_s"] = round(time.time() - t0, 1)
    with open(out_path, "w") as f:
        json.dump(out, f)


if __name__ == "__main__":
    main()
