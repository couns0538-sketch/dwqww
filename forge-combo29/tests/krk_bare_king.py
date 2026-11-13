#!/usr/bin/env python3
"""KRK mate must survive a previous search and a second worker.

Fresh depth 10 already plays the mate in 3. A depth-9 search of an unrelated
position used to leave history that made depth 14 play Re4 instead. The same
mate was missed by two fresh workers. Both must play d5c5.
"""

import subprocess
import sys
import time

KRK = "4R3/8/8/k2K4/8/8/8/8 w - - 0 1"
POISONS = (
    "8/8/8/8/3k4/8/3K4/3Q4 w - - 0 1",
    "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1",
    "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
)


class Engine:
    def __init__(self, exe):
        self.proc = subprocess.Popen(
            [exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1
        )

    def send(self, line):
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def until(self, pred, timeout=60):
        deadline = time.perf_counter() + timeout
        lines = []
        while time.perf_counter() < deadline:
            line = self.proc.stdout.readline()
            if line == "":
                raise RuntimeError("engine closed")
            line = line.rstrip("\n")
            lines.append(line)
            if pred(line):
                return lines
        raise TimeoutError(lines[-3:])

    def ready(self):
        self.send("isready")
        self.until(lambda line: line == "readyok")

    def setup(self, threads):
        self.send("uci")
        self.until(lambda line: line == "uciok")
        self.send("setoption name UseNNUE value true")
        self.send("setoption name Hash value 16")
        self.send(f"setoption name Threads value {threads}")
        self.ready()

    def new_game(self):
        self.send("ucinewgame")
        self.ready()

    def go(self, fen, depth):
        self.send("position fen " + fen)
        self.send(f"go depth {depth}")
        lines = self.until(lambda line: line.startswith("bestmove"))
        info = next(line for line in reversed(lines) if line.startswith("info depth"))
        parts = info.split()
        move = parts[parts.index("pv") + 1]
        score = " ".join(parts[parts.index("score"):parts.index("score") + 3])
        nodes = int(parts[parts.index("nodes") + 1])
        best = lines[-1].split()[1]
        return move, score, nodes, best

    def close(self):
        self.send("quit")
        self.proc.wait(timeout=5)


def main():
    if len(sys.argv) != 2:
        print("usage: krk_bare_king.py /path/to/forge", file=sys.stderr)
        return 2
    failures = 0
    engine = Engine(sys.argv[1])
    engine.setup(1)
    engine.new_game()
    move, score, nodes, best = engine.go(KRK, 10)
    print(f"fresh depth 10: {score} {move} nodes {nodes}")
    if move != "d5c5" or score != "score mate 3" or best != "d5c5":
        failures += 1
    for fen in POISONS:
        engine.new_game()
        engine.go(fen, 9)
        move, score, nodes, best = engine.go(KRK, 14)
        print(f"after poison: {score} {move} nodes {nodes}")
        if move != "d5c5" or score != "score mate 3" or best != "d5c5":
            failures += 1
    engine.close()

    engine = Engine(sys.argv[1])
    engine.setup(2)
    misses = 0
    for i in range(40):
        engine.new_game()
        move, score, nodes, best = engine.go(KRK, 14)
        if move != "d5c5" or best != "d5c5" or score != "score mate 3":
            misses += 1
            print(f"threads 2 miss {i}: {score} {move}")
    print(f"threads 2 fresh: {misses} misses / 40")
    failures += misses
    engine.close()
    print(f"failures {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
