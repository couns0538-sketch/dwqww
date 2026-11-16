#!/usr/bin/env python3
"""swarm seat 01: is seat 05's "fifty-move draw applied 9 plies early" a FAULT or the depth-10 horizon?

Seat 05 S-F3 claims the fifty-move draw is applied about 9 plies early, because the score on
  1K6/8/8/3R4/8/8/8/k7 w - - H 1
is non-zero for H <= 90 and exactly 0 from H = 91.

The alternative explanation, which needs no fault at all: `is_draw()` (search.cpp:1302) returns true at
board.halfmove_clock() >= 100, and a depth-D search from halfmove H reaches halfmove H + D - 1 at its
furthest leaf. So the draw is first visible exactly when H + D - 1 >= 100, i.e. H >= 101 - D. At D = 10
that is H >= 91. Under that reading the cliff must MOVE with the depth: 101 - D.

This script tests the prediction `first_zero_halfmove == 101 - depth` for depth 4, 6, 8, 10, 12.
If it holds, the "9 plies early" is the search horizon and the finding's framing is REFUTED even though
its numbers are right.

Usage: check_s05f3_depth.py <exe> <outdir>
"""
import hashlib
import json
import os
import select
import subprocess
import sys
import time
from pathlib import Path

TIMEOUT = 600.0
BOARD = "1K6/8/8/3R4/8/8/8/k7 w - - %d 1"


class R:
    def __init__(self, fd):
        self.fd, self.buf, self.eof = fd, b"", False

    def line(self, deadline):
        while b"\n" not in self.buf:
            if self.eof:
                return None
            remain = deadline - time.monotonic()
            if remain <= 0:
                return None
            r, _, _ = select.select([self.fd], [], [], remain)
            if not r:
                return None
            c = os.read(self.fd, 65536)
            if not c:
                self.eof = True
                return None
            self.buf += c
        l, _, self.buf = self.buf.partition(b"\n")
        return l.decode("utf-8", "replace")


def one(exe, fen, depth):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, bufsize=0, cwd="/tmp")
    rd = R(p.stdout.fileno())
    buf = []

    def until(prefix):
        d = time.monotonic() + TIMEOUT
        while True:
            l = rd.line(d)
            if l is None:
                return None
            buf.append(l)
            if l.startswith(prefix):
                return l

    def send(s):
        p.stdin.write((s + "\n").encode())
        p.stdin.flush()

    send("position fen " + fen)
    send("isready")
    if until("readyok") is None:
        p.kill()
        return None
    send("go depth %d" % depth)
    if until("bestmove") is None:
        p.kill()
        return None
    time.sleep(0.1)
    send("quit")
    try:
        p.wait(timeout=60)
    except Exception:
        p.kill()
    dl = [l for l in buf if l.startswith("info depth")]
    score = nodes = ""
    if dl:
        f = dl[-1].split()
        if "score" in f:
            i = f.index("score")
            score = " ".join(f[i + 1:i + 3])
        if "nodes" in f:
            nodes = f[f.index("nodes") + 1]
    return {"score": score, "nodes": nodes, "n_lines": len(dl)}


def main():
    exe = sys.argv[1]
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    dep = [(4, 10), (6, 10), (8, 10), (10, 10), (12, 4)]
    lines = ["does the fifty-move cliff move with depth?  prediction: first_zero == 101 - depth",
             "board: " + BOARD,
             "exe_started: %s" % exe,
             "sha256: %s" % hashlib.sha256(Path(exe).read_bytes()).hexdigest()]
    nm = subprocess.run(["nm", "-C", exe], capture_output=True, text=True).stdout
    lines.append("nm -C grep -c __asan_ : %d" % sum(1 for l in nm.splitlines() if "__asan_" in l))
    lines.append("option lines sent: NONE")
    lines.append("")
    lines.append("depth\texpected_first_zero\tswept_halfmoves\tobserved_first_zero\tverdict")
    rows = []
    for depth, span in dep:
        expected = 101 - depth
        lo = max(0, expected - span)
        hi = expected + span
        observed = None
        table = []
        for hm in range(lo, hi + 1):
            r = one(exe, BOARD % hm, depth)
            if r is None:
                table.append((hm, "PROCESS FAILED", ""))
                continue
            table.append((hm, r["score"], r["nodes"]))
            print("depth %-3d H=%-4d score=%-10s nodes=%s" % (depth, hm, r["score"], r["nodes"]),
                  flush=True)
            if observed is None and r["score"] == "cp 0" and hm > 0:
                observed = hm
        rows.append({"depth": depth, "expected": expected, "observed": observed, "table": table})
        lines.append("%d\t%d\t%d..%d\t%s\t%s" % (depth, expected, lo, hi, observed,
                                                 "MOVES WITH DEPTH" if observed == expected
                                                 else "DOES NOT MATCH (%s vs %s)" % (observed, expected)))
    (out / "check_s05f3_depth.json").write_text(json.dumps(rows, indent=1))
    text = "\n".join(lines) + "\n"
    (out / "check_s05f3_depth.txt").write_text(text)
    print("")
    print(text)


if __name__ == "__main__":
    main()
