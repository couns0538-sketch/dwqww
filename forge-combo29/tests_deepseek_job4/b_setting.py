#!/usr/bin/env python3
"""Job 4 part B: one setting, two criteria, over a fixed position set at a fixed node budget.

For each position: `ucinewgame`, then `position fen`, then `go nodes <N>`, wait for
bestmove. Records the last `info ... score ...` line and the move.

Two criteria, reported separately (job 3's "better way" 7.1):
  * exact distance: the last score is `mate K` with the expected K;
  * shortest-mate move: the move played keeps the shortest mate, proved by brute
    force over the resulting position (b1_score.py's approach).

Usage: b_setting.py <fens.json> <class> <nodes> <out.json> [--setopt name=value ...]
class is mate2 (expect mate 1 = 2 plies) or mate3 (expect mate 2 = 3 plies).
"""
import json
import queue
import re
import subprocess
import sys
import threading
import time

import chess

sys.path.insert(0, "/agent/repos/dwqww/forge-combo29/tests_deepseek_job3")
import b_truth as T

ENGINE = "/tmp/ds/build-release/forge"
MATE_RE = re.compile(r"\bscore mate (-?\d+)\b")


class Engine:
    def __init__(self, setopts):
        self.proc = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.q = queue.Queue()
        self.t = threading.Thread(target=self._read, daemon=True)
        self.t.start()
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

    def send(self, command):
        self.proc.stdin.write(command + "\n")
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

    def search(self, fen, nodes, timeout=120):
        self.send("ucinewgame")
        self.send(f"position fen {fen}")
        self.send(f"go nodes {nodes}")
        last = None
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None, last
            try:
                line = self.q.get(timeout=remaining)
            except queue.Empty:
                return None, last
            if line is None:
                return None, last
            if line.startswith("info") and " score " in line:
                last = line
            elif line.startswith("bestmove"):
                parts = line.split()
                return (parts[1] if len(parts) > 1 else None), last

    def search_at(self, fen, limit, timeout=600):
        """Like search() but `limit` is any go-limit string, e.g. "depth 12"."""
        self.send("ucinewgame")
        self.send(f"position fen {fen}")
        self.send(f"go {limit}")
        last = None
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None, last
            try:
                line = self.q.get(timeout=remaining)
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
        self.t.join(timeout=5)


def keeps_shortest_mate(fen, move_text, plies):
    """True if the move keeps a mate in `plies` (the parent's shortest)."""
    try:
        board = chess.Board(fen)
        move = chess.Move.from_uci(move_text)
    except (ValueError, AttributeError):
        return False
    if move not in board.legal_moves:
        return False
    board.push(move)
    child = T.mate_in(board, max(1, plies - 1))
    if plies <= 1:
        return board.is_checkmate()
    want = -(plies - 1)
    return child == want or (plies == 2 and board.is_checkmate())


def main():
    fens_path, cls, nodes, out_path = sys.argv[1:5]
    setopts = []
    args = sys.argv[5:]
    i = 0
    while i < len(args):
        if args[i] == "--setopt":
            k, v = args[i + 1].split("=", 1)
            setopts.append((k, v))
            i += 2
        else:
            i += 1
    with open(fens_path) as f:
        fens = json.load(f)[cls]
    expected_mate = 1 if cls == "mate2" else 2
    plies = 2 if cls == "mate2" else 3

    eng = Engine(setopts)
    exact = 0
    keeps = 0
    misses_exact = []
    misses_move = []
    t0 = time.time()
    for idx, fen in enumerate(fens):
        move, last = eng.search(fen, nodes)
        m = MATE_RE.search(last or "")
        if m and int(m.group(1)) == expected_mate:
            exact += 1
        else:
            misses_exact.append({"index": idx, "fen": fen, "bestmove": move,
                                 "last_info": last, "expected_mate": expected_mate})
        if keeps_shortest_mate(fen, move, plies):
            keeps += 1
        else:
            misses_move.append({"index": idx, "fen": fen, "bestmove": move,
                                "last_info": last})
    eng.close()
    result = {"class": cls, "positions": len(fens), "nodes": nodes,
              "setopts": setopts,
              "exact_distance": exact, "shortest_mate_move": keeps,
              "wall_s": round(time.time() - t0, 1),
              "misses_exact": misses_exact, "misses_move": misses_move}
    with open(out_path, "w") as f:
        json.dump(result, f, indent=1)
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ("misses_exact", "misses_move")}, sort_keys=True))


if __name__ == "__main__":
    main()
