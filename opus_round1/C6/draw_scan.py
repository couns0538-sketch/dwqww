#!/usr/bin/env python3
"""Fixed-depth scores with CuckooRep off and on (C6 search-level evidence).

For each position (FEN + optional moves) and each depth, runs `go depth d` in a
fresh `ucinewgame` with Threads 1, Hash 16, OwnBook false, once with CuckooRep
false and once with CuckooRep true, and prints the final score of each.
usage: draw_scan.py <forge.exe> <positions.txt> <min_depth> <max_depth>
positions.txt: one position per line, `name | fen | moves` (moves may be empty).
"""
import subprocess
import sys


class Engine:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
        self.send("uci")
        self.wait("uciok")
        for line in ("setoption name Threads value 1", "setoption name Hash value 16",
                     "setoption name OwnBook value false"):
            self.send(line)

    def send(self, line):
        self.p.stdin.write(line + "\n")
        self.p.stdin.flush()

    def wait(self, token):
        lines = []
        while True:
            line = self.p.stdout.readline()
            if not line:
                raise SystemExit("engine exited")
            lines.append(line.rstrip("\n"))
            if line.startswith(token):
                return lines

    def search(self, fen, moves, depth, cuckoo):
        self.send("setoption name CuckooRep value " + ("true" if cuckoo else "false"))
        self.send("ucinewgame")
        self.send("isready")
        self.wait("readyok")
        self.send("position fen " + fen + (" moves " + moves if moves else ""))
        self.send("go depth %d" % depth)
        lines = self.wait("bestmove")
        score, nodes = None, None
        for line in lines:
            if line.startswith("info depth"):
                parts = line.split()
                if "score" in parts:
                    i = parts.index("score")
                    score = parts[i + 1] + " " + parts[i + 2]
                if "nodes" in parts:
                    nodes = int(parts[parts.index("nodes") + 1])
        return score, nodes, lines[-1].split()[1]

    def quit(self):
        self.send("quit")
        self.p.wait(timeout=30)


def main():
    exe, pos_file, lo, hi = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    engine = Engine(exe)
    for raw in open(pos_file, encoding="utf-8"):
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        name, fen, moves = [field.strip() for field in raw.split("|")]
        for depth in range(lo, hi + 1):
            off = engine.search(fen, moves, depth, False)
            on = engine.search(fen, moves, depth, True)
            flag = "ON_DRAW_ONLY" if on[0] == "cp 0" and off[0] != "cp 0" else ""
            print(f"{name} d{depth} OFF {off[0]} nodes {off[1]} bm {off[2]} | ON {on[0]} nodes {on[1]} bm {on[2]} {flag}",
                  flush=True)
    engine.quit()


if __name__ == "__main__":
    main()
