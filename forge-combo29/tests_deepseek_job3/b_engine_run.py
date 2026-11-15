#!/usr/bin/env python3
"""Job 3 part B: run the optimised engine over a set of positions and record its verdict.

For each FEN: `position fen`, `go <limit>`, wait for bestmove (nothing piped ahead), then
record the LAST `info ... score ...` line (depth, score cp or mate), the bestmove, and
whether that move is legal. Legality is checked with python-chess against the FEN sent.

`score mate N` is reported by the engine in MOVES (as UCI requires): `mate 2` means the
side to move mates in 2 moves. Truth from b_truth.py is in PLIES, so a truth of +3
plies is `mate 2` moves.

Usage: b_engine_run.py <fens-json> <key> <limit> <out.json> [net]
  fens-json: a JSON list of FENs, or a JSON object with a "positions" list / per-class lists
  net:       optional path; when given, NNUEArchFile is set and NNUEArch true
"""
import json
import queue
import re
import subprocess
import sys
import threading
import time

import chess

ENGINE = "/tmp/ds/build-release/forge"
MATE_RE = re.compile(r"\bscore mate (-?\d+)\b")
CP_RE = re.compile(r"\bscore cp (-?\d+)\b")
DEPTH_RE = re.compile(r"^info depth (\d+)")


class Engine:
    def __init__(self, threads=1, hash_mb=16, net=None, out_path=None):
        kwargs = {}
        if out_path:
            self.out = open(out_path, "w")
            kwargs["stdout"] = subprocess.PIPE
        else:
            self.out = None
        self.proc = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.q = queue.Queue()
        self.t = threading.Thread(target=self._read, daemon=True)
        self.t.start()
        self.send(f"setoption name Threads value {threads}")
        self.send(f"setoption name Hash value {hash_mb}")
        if net:
            self.send(f"setoption name NNUEArchFile value {net}")
            self.send("setoption name NNUEArch value true")
        else:
            self.send("setoption name NNUEArch value false")
        self.send("isready")
        self.until("readyok", 300)

    def _read(self):
        for line in self.proc.stdout:
            if self.out:
                self.out.write(line)
                self.out.flush()
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

    def search(self, fen, limit, timeout=900):
        """Returns (bestmove, last_info_line, all_info_lines)."""
        self.send(f"position fen {fen}")
        self.send(f"go {limit}")
        infos = []
        last = None
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None, last, infos
            try:
                line = self.q.get(timeout=remaining)
            except queue.Empty:
                return None, last, infos
            if line is None:
                return None, last, infos
            if line.startswith("info"):
                infos.append(line)
                if " score " in line:
                    last = line
            elif line.startswith("bestmove"):
                parts = line.split()
                move = parts[1] if len(parts) > 1 else None
                return move, last, infos

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
        self.t.join(timeout=10)
        if self.out:
            self.out.close()


def legal(fen, move_text):
    if not move_text or move_text == "(none)":
        return False, "no move"
    try:
        board = chess.Board(fen)
        move = chess.Move.from_uci(move_text)
    except ValueError:
        return False, "unparsable"
    return (move in board.legal_moves), ("" if move in board.legal_moves else "illegal")


def score_of(line):
    if not line:
        return None
    mate = MATE_RE.search(line)
    if mate:
        return {"kind": "mate", "value": int(mate.group(1))}
    cp = CP_RE.search(line)
    if cp:
        return {"kind": "cp", "value": int(cp.group(1))}
    return None


def main():
    fens_json, key, limit, out_path = sys.argv[1:5]
    net = sys.argv[5] if len(sys.argv) > 5 else None
    with open(fens_json) as f:
        data = json.load(f)
    if isinstance(data, dict):
        fens = data[key] if key in data else data.get("positions", [])
    else:
        fens = data
    # The mates file stores FEN strings per class; the stalemate file stores objects.
    if fens and isinstance(fens[0], dict):
        fens = [entry["fen"] for entry in fens]

    eng = Engine(threads=1, hash_mb=16, net=net, out_path=out_path + ".stdout.log")
    results = []
    t0 = time.time()
    for i, fen in enumerate(fens):
        move, last, infos = eng.search(fen, limit)
        ok, why = legal(fen, move)
        results.append({
            "index": i, "fen": fen, "bestmove": move, "legal": ok, "illegal_reason": why,
            "last_info": last, "score": score_of(last),
            "depth_reached": max((int(DEPTH_RE.match(l).group(1)) for l in infos
                                  if DEPTH_RE.match(l)), default=None),
            "info_lines": len(infos),
            "no_bestmove": move is None,
        })
    eng.close()
    with open(out_path, "w") as f:
        json.dump({"positions": len(fens), "limit": limit, "net": net,
                   "engine_seconds": round(time.time() - t0, 1), "results": results}, f, indent=1)
    print(json.dumps({"positions": len(fens), "limit": limit,
                      "no_bestmove": sum(1 for r in results if r["no_bestmove"]),
                      "illegal": sum(1 for r in results if not r["legal"]),
                      "engine_seconds": round(time.time() - t0, 1)}))


if __name__ == "__main__":
    main()
