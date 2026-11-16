#!/usr/bin/env python3
"""s14_sums.py EXE FENS OUTDIR DEPTH

Repeats the brief's "known sums" check, which is simultaneously:
  * a test of uci.cpp's setoption path (if any S14 option silently fails to apply, the node
    count cannot land on the published number), and
  * a check that this seat's harness sends exactly what the brief specifies
    (ucinewgame + isready before every `go`, Threads 1, Hash 16).

Asserts each number was FOUND and parses as an integer. A missing "nodes" field, a timeout or a
zero is a hard error, never a pass.
"""
import json
import os
import queue
import re
import subprocess
import sys
import threading

S14 = [
    "LmrQuietBase value 93", "LmrQuietDivisor value 205", "LmrNoisyBase value 13",
    "LmrNoisyDivisor value 333", "LmrHistoryDivisor value 5643", "NullMoveBase value 5",
    "LmpBase value 8", "HistoryPruneMultiplier value 2220",
    "HistoryBonusQuadratic value 24", "HistoryBonusLinear value 54",
    "HistoryBonusMax value 2212", "SingularDepth value 6", "IirDepth value 2",
    "NonPawnCorrection value true",
]


class Reader:
    def __init__(self, stream):
        self.q = queue.Queue()
        threading.Thread(target=self._pump, args=(stream,), daemon=True).start()

    def _pump(self, stream):
        for line in stream:
            self.q.put(line)
        self.q.put(None)

    def readline(self, timeout=180.0):
        try:
            return self.q.get(timeout=timeout)
        except queue.Empty:
            return None


def go(exe, fen, depth):
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, bufsize=1)
    r = Reader(proc.stdout)

    def send(c):
        proc.stdin.write(c + "\n")
        proc.stdin.flush()

    def drain(tag):
        while True:
            line = r.readline()
            if line is None:
                raise SystemExit(f"FAIL no readyok after {tag}")
            if line.strip() == "readyok":
                return

    send("uci")
    while True:
        line = r.readline()
        if line is None or line.strip() == "uciok":
            break
    for opt in ["Hash value 16", "Threads value 1"] + S14:
        send("setoption name " + opt)
        send("isready")
        drain(opt)
    send("ucinewgame")
    send("isready")
    drain("ucinewgame")
    send("position fen " + fen)
    send("isready")
    drain("position")
    send(f"go depth {depth}")
    nodes = None
    score = None
    while True:
        line = r.readline(300.0)
        if line is None:
            raise SystemExit(f"FAIL no bestmove for fen {fen}")
        if line.startswith("info depth") and " nodes " in line and " pv " in line:
            m = re.search(r" nodes (\d+) ", line)
            if m:
                nodes = int(m.group(1))
        if line.startswith("info depth") and " score " in line:
            m = re.search(r" score (cp|mate) (-?\d+)", line)
            if m:
                score = line.strip()
        if line.startswith("bestmove"):
            break
    send("quit")
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
    if nodes is None:
        raise SystemExit(f"FAIL no nodes figure parsed for fen {fen}: cannot compare")
    return nodes, score


def main():
    exe, fens_path, outdir, depth = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    os.makedirs(outdir, exist_ok=True)
    fens = [l.strip() for l in open(fens_path, encoding="utf-8") if l.strip()]
    rows = []
    total = 0
    for i, fen in enumerate(fens):
        nodes, score = go(exe, fen, depth)
        rows.append({"index": i, "fen": fen, "nodes": nodes, "last_score_line": score})
        total += nodes
        if i < 3:
            print(f"  first{i+1}: nodes {nodes}")
    print(f"positions {len(rows)} depth {depth}")
    print(f"SUM {total}")
    json.dump({"depth": depth, "fens": fens_path, "rows": rows, "sum": total},
              open(os.path.join(outdir, f"sum_d{depth}.json"), "w"), indent=1)
    if total == 0:
        raise SystemExit("FAIL sum is zero: nothing was measured")


if __name__ == "__main__":
    main()
