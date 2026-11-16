#!/usr/bin/env python3
"""book_moves.py EXE OUTDIR [PLIES]

In NORMAL PLAY the built-in book answers clock and movetime searches (uci.cpp:525-527), and
`decode_move` (src/book.cpp:75-95) maps a book entry by scanning `board.legal_moves()`, so the
book can only ever return a legal move. This test checks that claim from the outside:

  * plays a self-game with OwnBook ON and clock searches, so the book is actually consulted;
  * records every `info string book move X` line the engine prints;
  * asserts X is legal in the position that was sent, and that `bestmove` equals X;
  * counts how many plies were answered by the book, and fails if zero (a book test that never
    touches the book measures nothing).

Book Depth is raised so the book is consulted for the whole game.
"""
import os
import queue
import re
import subprocess
import sys
import threading

import chess

BOOK_LINE = re.compile(r"info string book move (\S+)")


class Reader:
    def __init__(self, s):
        self.q = queue.Queue()
        threading.Thread(target=self._pump, args=(s,), daemon=True).start()

    def _pump(self, s):
        for line in s:
            self.q.put(line)
        self.q.put(None)

    def get(self, t):
        try:
            return self.q.get(timeout=t)
        except queue.Empty:
            return None


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    plies = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    os.makedirs(outdir, exist_ok=True)
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, bufsize=1)
    r = Reader(proc.stdout)
    log = open(os.path.join(outdir, "transcript.txt"), "w")
    failures, book_plies, played = [], 0, 0

    def send(c):
        proc.stdin.write(c + "\n")
        proc.stdin.flush()
        log.write(">> " + c + "\n")

    def drain():
        while True:
            line = r.get(60)
            if line is None:
                raise RuntimeError("no readyok")
            log.write("<< " + line)
            if line.strip() == "readyok":
                return

    send("uci")
    while True:
        line = r.get(30)
        if line is None or line.strip() == "uciok":
            break
        log.write("<< " + line)
    for opt in ["Hash value 16", "Threads value 1", "OwnBook value true", "Book Depth value 100"]:
        send("setoption name " + opt)
        send("isready")
        drain()

    board = chess.Board()
    for ply in range(plies):
        if board.is_game_over():
            break
        send("position fen " + board.fen())
        send("isready")
        drain()
        send("go wtime 2000 btime 2000 winc 0 binc 0")
        book_move = None
        best = None
        while True:
            line = r.get(60)
            if line is None:
                failures.append(f"ply {ply}: no bestmove")
                break
            m = BOOK_LINE.search(line)
            if m:
                book_move = m.group(1)
            if line.startswith("bestmove"):
                best = line.split()[1]
                break
        if best is None:
            break
        legal = [mv.uci() for mv in board.legal_moves]
        if best not in legal:
            failures.append(f"ply {ply}: bestmove {best} illegal in {board.fen()}")
            break
        if book_move is not None:
            book_plies += 1
            if book_move not in legal:
                failures.append(f"ply {ply}: BOOK MOVE {book_move} illegal in {board.fen()}")
                break
            if book_move != best:
                failures.append(f"ply {ply}: book move {book_move} but bestmove {best}")
                break
        played += 1
        board.push(chess.Move.from_uci(best))
    send("quit")
    try:
        proc.wait(timeout=20)
    except subprocess.TimeoutExpired:
        proc.kill()
    log.close()

    print(f"plies played {played}, plies answered by the book {book_plies}")
    for f in failures:
        print("  FAIL " + f)
    if failures:
        print(f"RESULT: {len(failures)} failure(s)")
        sys.exit(1)
    if book_plies == 0:
        print("RESULT: the book was never consulted, so this run says nothing about it")
        sys.exit(2)
    print("RESULT: every book move was legal and matched the bestmove the engine printed")


if __name__ == "__main__":
    main()
