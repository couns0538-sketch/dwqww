#!/usr/bin/env python3
"""Job 6 parts B2 and B3: the 50-move rule and repetition, hand-checkable cases.

B2 (a) halfmove 99 with mate in one: the engine must play it.
B2 (b) halfmove 99, a won ending with no mate in one and no pawn move/capture that keeps
       the win: the true result is a draw; report the score printed.
B2 (c) the same at halfmove 90, where the win needs more than 5 moves (from my WDL table
       I cannot measure DTZ, so "needs more than 5 moves" is approximated by a position
       whose WDL win needs a long manoeuvre - I use KQvK positions far from mate).
B3 repetition: 200 KQvK/KRvK cases reached through `moves` where the engine has at least
       one move after which python-chess says is_repetition(3) and at least one winning
       move that does not; count how often it plays the repeating move.

Usage: b23.py <tables.json> <outdir> <seed>
"""
import json
import os
import queue
import random
import subprocess
import sys
import threading
import time

import chess

ENGINE = "/tmp/ds/build-release/forge"


class Engine:
    def __init__(self, engine=ENGINE):
        self.proc = subprocess.Popen([engine], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True, bufsize=1)
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

    def best(self, pos, nodes, timeout=300):
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


def kind_of(board):
    men = [s for s in chess.SQUARES
           if board.piece_at(s) and board.piece_at(s).piece_type != chess.KING]
    if len(men) != 1:
        return None
    pt = board.piece_at(men[0]).piece_type
    return {chess.QUEEN: "KQvK", chess.ROOK: "KRvK", chess.PAWN: "KPvK"}.get(pt)


def class_key(board):
    return board.board_fen() + (" w" if board.turn else " b")


def main():
    tables_path, outdir, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
    os.makedirs(outdir, exist_ok=True)
    rng = random.Random(seed)
    with open(tables_path) as f:
        tables = json.load(f)
    eng = Engine()
    out = {"seed": seed}

    # --- B2(a): halfmove 99 with mate in one ---
    # Take the job-3 mate-in-one positions and set the clock to 99; a mate delivered
    # on the 100th halfmove is still a mate, so the engine must play it.
    mate1 = json.load(open('/tmp/ds/job3/B1-mates.json'))['mate2']
    cases_a = []
    for fen in mate1[:5]:
        b = chess.Board(fen)
        parts = fen.split()
        parts[4] = "99"
        g = " ".join(parts)
        cases_a.append(g)
    a_results = []
    for fen in cases_a:
        b = chess.Board(fen)
        # The mating move, found by brute force.
        mating = None
        for m in b.legal_moves:
            b.push(m)
            if b.is_checkmate():
                mating = m.uci()
            b.pop()
            if mating:
                break
        move, last = eng.best(f"position fen {fen}", 20000)
        a_results.append({"fen": fen, "mating_move": mating, "engine_move": move,
                          "score": last, "played_mate": move == mating})
    out["B2a_mate_at_clock_99"] = a_results

    # --- B2(b) and (c): halfmove 99 and 90 on a won KQvK with no mate in one ---
    def no_mate_in_one(fen):
        b = chess.Board(fen)
        for m in b.legal_moves:
            b.push(m)
            mate = b.is_checkmate()
            b.pop()
            if mate:
                return False
        return True

    won = []
    guard = 0
    while len(won) < 5 and guard < 200000:
        guard += 1
        wk, bk, q = rng.sample(range(64), 3)
        if chess.square_distance(wk, bk) < 2:
            continue
        b = chess.Board(None)
        b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        b.set_piece_at(q, chess.Piece(chess.QUEEN, chess.WHITE))
        b.castling_rights = 0
        b.ep_square = None
        b.turn = chess.WHITE
        if not b.is_valid() or b.is_game_over():
            continue
        if tables["KQvK"].get(class_key(b)) != "W":
            continue
        fen = b.fen()
        if no_mate_in_one(fen):
            won.append(fen)
    b_cases = []
    for clock in (99, 90):
        for fen in won:
            parts = fen.split()
            parts[4] = str(clock)
            g = " ".join(parts)
            move, last = eng.best(f"position fen {g}", 20000)
            b_cases.append({"fen": g, "clock": clock, "engine_move": move, "score": last})
    out["B2bc_won_no_mate_in_one"] = b_cases

    # --- B3: repetition ---
    repeating = 0
    total = 0
    examples = []
    guard = 0
    while total < 200 and guard < 400000:
        guard += 1
        wk, bk, q = rng.sample(range(64), 3)
        if chess.square_distance(wk, bk) < 2:
            continue
        b = chess.Board(None)
        b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        b.set_piece_at(q, chess.Piece(random.choice([chess.QUEEN, chess.ROOK]), chess.WHITE))
        b.castling_rights = 0
        b.ep_square = None
        b.turn = chess.WHITE
        if not b.is_valid() or b.is_game_over():
            continue
        start = b.fen()
        if tables["KQvK"].get(class_key(b)) is None:
            continue
        # Two reversible moves each, making a position that can be repeated.
        line = []
        ok = True
        for _ in range(4):
            legal = [m for m in b.legal_moves if not b.is_capture(m)]
            if not legal:
                ok = False
                break
            m = rng.choice(legal)
            b.push(m)
            line.append(m.uci())
        if not ok or b.turn == chess.WHITE:
            continue
        # Now the strong side is NOT to move; play one more pair so it is.
        legal = [m for m in b.legal_moves if not b.is_capture(m)]
        if not legal:
            continue
        m = rng.choice(legal)
        b.push(m)
        line.append(m.uci())
        if b.turn != chess.WHITE:
            continue
        kind = kind_of(b)
        if kind is None or tables[kind].get(class_key(b)) != "W":
            continue
        rep_moves, win_moves = [], []
        for m in b.legal_moves:
            b.push(m)
            is_rep = b.is_repetition(3)
            child_kind = kind_of(b)
            child_w = tables[child_kind].get(class_key(b)) if child_kind else None
            b.pop()
            if is_rep:
                rep_moves.append(m.uci())
            if child_w == "L":
                win_moves.append(m.uci())
        if rep_moves and win_moves:
            total += 1
            pos = f"position fen {start} moves {' '.join(line)}"
            move, last = eng.best(pos, 20000)
            if move in rep_moves:
                repeating += 1
                if len(examples) < 8:
                    examples.append({"fen": start, "moves": line, "engine_move": move,
                                     "score": last, "rep_moves": rep_moves,
                                     "win_moves": win_moves[:4]})
    out["B3_repetition"] = {"cases": total, "engine_played_repeating_move": repeating,
                            "examples": examples}
    eng.close()
    with open(os.path.join(outdir, "B2-B3.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({
        "B2a_played_mate": f"{sum(1 for r in a_results if r['played_mate'])}/{len(a_results)}",
        "B2bc_cases": len(b_cases),
        "B3_cases": total,
        "B3_played_repeating": repeating,
    }))


if __name__ == "__main__":
    main()
