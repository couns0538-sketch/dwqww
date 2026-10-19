#!/usr/bin/env python3
"""UCI regression: depth-1 forced stalemate must score exactly 0 cp.

Run from a Forge checkout:
  python tools/audit/uci_qsearch_stalemate.py ./build/forge
Expected on repaired engine: PASS.
Known affected baseline: 9108d012; not executed against baseline in this audit.
"""
import argparse
import queue
import re
import subprocess
import sys
import threading
import time

FEN = "7k/8/5K2/6Q1/8/8/8/8 w - - 0 1"
MOVE = "g5g6"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("engine")
    ap.add_argument("--timeout", type=float, default=20.0)
    args = ap.parse_args()
    process = subprocess.Popen([args.engine], stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, encoding="utf-8", errors="replace", bufsize=1)
    responses = queue.Queue()

    def read_output():
        for line in process.stdout:
            responses.put(line.rstrip("\r\n"))
        responses.put(None)
    threading.Thread(target=read_output, daemon=True).start()

    def send(command):
        print("> " + command, flush=True)
        process.stdin.write(command + "\n")
        process.stdin.flush()

    def read_until(predicate):
        deadline = time.monotonic() + args.timeout
        collected = []
        while time.monotonic() < deadline:
            try:
                line = responses.get(timeout=max(.01, deadline - time.monotonic()))
            except queue.Empty:
                break
            if line is None:
                raise RuntimeError("engine stdout closed")
            print("< " + line, flush=True)
            collected.append(line)
            if predicate(line):
                return collected
        raise TimeoutError("engine response timeout")

    try:
        send("uci")
        read_until(lambda s: s == "uciok")
        send("setoption name OwnBook value false")
        send("setoption name UseNNUE value false")
        send("isready")
        read_until(lambda s: s == "readyok")
        send("position fen " + FEN)
        send("go depth 1 searchmoves " + MOVE)
        output = read_until(lambda s: s.startswith("bestmove "))
        best = [s for s in output if s.startswith("bestmove ")][-1].split()[1]
        scores = [int(match.group(1)) for line in output
                  if (match := re.search(r"^info depth 1\b.*\bscore cp (-?\d+)\b", line))]
        if best != MOVE or not scores or scores[-1] != 0:
            raise AssertionError(f"expected bestmove={MOVE}, cp=0; got bestmove={best}, scores={scores}")
        print("PASS: forced g5g6 creates stalemate scored cp 0")
    finally:
        if process.poll() is None:
            try:
                send("quit")
                process.wait(timeout=2)
            except (BrokenPipeError, subprocess.TimeoutExpired):
                process.kill()
                process.wait(timeout=2)

if __name__ == "__main__":
    try:
        sys.exit(main())
    except (AssertionError, RuntimeError, TimeoutError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        sys.exit(1)
