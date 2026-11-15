#!/usr/bin/env python3
"""Job 5 part B1: find the SMALLEST earlier search that changes a later search's score.

Target: 2Q3KR/4k3/8/8/8/8/8/8 w - - 0 1, searched at depth 12 (fresh process: mate 4).

For each candidate earlier position P and depth d, run one process that does
  position fen P ; go depth d   (wait for bestmove)
  position fen TARGET ; go depth 12
and record the target's last score. A candidate that changes the target's score is a
minimal witness. The fresh-process score is measured the same way but with no first
search.

Usage: b1_minimal.py <candidates.txt> <out.json>
"""
import json
import queue
import re
import subprocess
import sys
import threading
import time

ENGINE = "/tmp/ds/build-release/forge"
TARGET = "2Q3KR/4k3/8/8/8/8/8/8 w - - 0 1"
TARGET_DEPTH = 12
MATE_RE = re.compile(r"\bscore (mate|cp) (-?\d+)\b")


class Engine:
    def __init__(self):
        self.proc = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.q = queue.Queue()
        self.t = threading.Thread(target=self._read, daemon=True)
        self.t.start()
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

    def search(self, fen, depth, timeout=600):
        self.send(f"position fen {fen}")
        self.send(f"go depth {depth}")
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
                return line.split()[1] if len(line.split()) > 1 else None, last

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


def score_text(line):
    m = MATE_RE.search(line or "")
    return f"{m.group(1)} {m.group(2)}" if m else "none"


def main():
    candidates_path, out_path = sys.argv[1:3]
    with open(candidates_path) as f:
        candidates = [l.strip() for l in f if l.strip()]

    # Fresh baseline, repeated 3 times to show it is stable.
    baselines = []
    for _ in range(3):
        e = Engine()
        _mv, last = e.search(TARGET, TARGET_DEPTH)
        baselines.append(score_text(last))
        e.close()

    witnesses = []
    for fen in candidates:
        for depth in (12, 8, 4):
            e = Engine()
            e.search(fen, depth)
            _mv, last = e.search(TARGET, TARGET_DEPTH)
            got = score_text(last)
            e.close()
            if got != baselines[0]:
                witnesses.append({"before_fen": fen, "before_depth": depth,
                                  "target_score_before": baselines[0],
                                  "target_score_after": got})
                break
    out = {"target": TARGET, "target_depth": TARGET_DEPTH,
           "baseline_scores": baselines, "candidates": len(candidates),
           "witnesses": witnesses}
    with open(out_path, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({"baseline": baselines, "witnesses": len(witnesses)}))
    for w in witnesses[:6]:
        print("  WITNESS", w["before_fen"], "depth", w["before_depth"], "->", w["target_score_after"])


if __name__ == "__main__":
    main()
