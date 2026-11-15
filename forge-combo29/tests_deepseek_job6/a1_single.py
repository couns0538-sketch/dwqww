#!/usr/bin/env python3
"""Job 6 part A1: single-move half points thrown away, judged by my retrograde tables.

For each class: 2,000 random legal positions (no castling, no en passant, halfmove 0,
not checkmate or stalemate, either side to move, each position once). The engine gets
`ucinewgame`, `position fen`, `go nodes N`; the class before the move is compared with
the class after it.

Classes are limited to the three I could solve locally (KQvK, KRvK, KPvK): the Syzygy
mirror is unreachable, which the job's fallback covers.

Usage: a1_single.py <tables.json> <classes> <nodes> <out.json> <seed>
"""
import json
import queue
import random
import re
import subprocess
import sys
import threading
import time

import chess

ENGINE = "/tmp/ds/build-release/forge"
CP_RE = re.compile(r"\bscore (cp|mate) (-?\d+)\b")


class Engine:
    def __init__(self):
        self.proc = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True, bufsize=1)
        self.q = queue.Queue()
        self.err = []
        threading.Thread(target=self._read, daemon=True).start()
        threading.Thread(target=lambda: [self.err.append(l.rstrip()) for l in self.proc.stderr],
                         daemon=True).start()
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

    def play(self, fen, nodes, timeout=300):
        self.send("ucinewgame")
        self.send(f"position fen {fen}")
        self.send(f"go nodes {nodes}")
        last = None
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            remaining = deadline - time.monotonic()
            try:
                line = self.q.get(timeout=max(0.01, remaining))
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
    """The table's key: board_fen + side to move, with the strong piece's colour kept."""
    return board.board_fen() + (" w" if board.turn else " b")


def wdl(board, tables, kind):
    """W/D/L for the side to move, from my table. None if the position is not in it."""
    return tables[kind].get(class_key(board))


def kind_of(board):
    """Which class a board is, by its material (kings + one man)."""
    men = [s for s in chess.SQUARES if board.piece_at(s) and board.piece_at(s).piece_type != chess.KING]
    if len(men) != 1:
        return None
    pt = board.piece_at(men[0]).piece_type
    return {chess.QUEEN: "KQvK", chess.ROOK: "KRvK", chess.PAWN: "KPvK"}.get(pt)


def random_positions(kind, count, rng):
    """Random legal positions of the class, no castling/en passant, halfmove 0."""
    out = []
    seen = set()
    strong = {"KQvK": chess.QUEEN, "KRvK": chess.ROOK, "KPvK": chess.PAWN}[kind]
    guard = 0
    while len(out) < count and guard < count * 400:
        guard += 1
        wk, bk, s = rng.sample(range(64), 3)
        if chess.square_distance(wk, bk) < 2:
            continue
        if strong == chess.PAWN and chess.square_rank(s) in (0, 7):
            continue
        strong_white = rng.random() < 0.5
        b = chess.Board(None)
        b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        b.set_piece_at(s, chess.Piece(strong, chess.WHITE if strong_white else chess.BLACK))
        b.castling_rights = 0
        b.ep_square = None
        b.halfmove_clock = 0
        b.turn = chess.WHITE if rng.random() < 0.5 else chess.BLACK
        if not b.is_valid():
            continue
        # The side not to move must not be in check.
        b.turn = not b.turn
        bad = b.is_check()
        b.turn = not b.turn
        if bad:
            continue
        if b.is_checkmate() or b.is_stalemate() or b.is_game_over():
            continue
        fen = b.fen()
        if fen in seen:
            continue
        seen.add(fen)
        out.append(fen)
    return out


def main():
    tables_path, classes, nodes, out_path, seed = sys.argv[1:6]
    nodes = int(nodes)
    rng = random.Random(int(seed))
    with open(tables_path) as f:
        tables = json.load(f)
    classes = [c for c in classes.split(",") if c in tables]
    eng = Engine()
    result = {"nodes": nodes, "seed": int(seed), "classes": {}}
    t0 = time.time()
    for kind in classes:
        positions = random_positions(kind, 2000, rng)
        stats = {"positions": len(positions), "wins": 0, "win_to_draw": 0,
                 "win_to_loss": 0, "draws": 0, "draw_to_loss": 0,
                 "losses": 0, "not_in_table": 0, "no_bestmove": 0, "illegal": 0}
        failures = []
        for fen in positions:
            b = chess.Board(fen)
            before = wdl(b, tables, kind)
            if before is None:
                stats["not_in_table"] += 1
                continue
            move_text, last = eng.play(fen, nodes)
            if move_text is None:
                stats["no_bestmove"] += 1
                continue
            try:
                move = chess.Move.from_uci(move_text)
            except ValueError:
                stats["illegal"] += 1
                continue
            if move not in b.legal_moves:
                stats["illegal"] += 1
                continue
            b.push(move)
            after_board = b
            # The move is judged by the resulting position, from the OPPONENT's view,
            # then negated to the mover's view. Two cases:
            if after_board.is_checkmate():
                after_mover = "W"          # we just mated
            elif after_board.is_stalemate() or after_board.is_insufficient_material():
                after_mover = "D"
            else:
                kind_after = kind_of(after_board)
                after = wdl(after_board, tables, kind_after) if kind_after else None
                if after is None:
                    stats["not_in_table"] += 1
                    continue
                after_mover = {"W": "L", "L": "W", "D": "D"}[after]
            if before == "W":
                stats["wins"] += 1
                if after_mover == "D":
                    stats["win_to_draw"] += 1
                    failures.append({"fen": fen, "move": move_text, "score": last,
                                     "before": before, "after": after_mover})
                elif after_mover == "L":
                    stats["win_to_loss"] += 1
                    failures.append({"fen": fen, "move": move_text, "score": last,
                                     "before": before, "after": after_mover})
            elif before == "D":
                stats["draws"] += 1
                if after_mover == "L":
                    stats["draw_to_loss"] += 1
                    failures.append({"fen": fen, "move": move_text, "score": last,
                                     "before": before, "after": after_mover})
            else:
                stats["losses"] += 1
        stats["failures"] = failures
        result["classes"][kind] = stats
        print(json.dumps({"class": kind, **{k: v for k, v in stats.items() if k != "failures"}}),
              flush=True)
    eng.close()
    result["wall_s"] = round(time.time() - t0, 1)
    with open(out_path, "w") as f:
        json.dump(result, f)


if __name__ == "__main__":
    main()
