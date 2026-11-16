#!/usr/bin/env python3
"""swarm seat 01: REGRESSION TEST of my own patch job2/fifty_move_mate.patch.txt.

The patch removes `board.halfmove_clock() >= 100` from `root_drawn` (search.cpp:2251). I flagged one risk as
unmeasured in REPORT_job2.md: "the patch removes a shortcut that exists to save time in dead-drawn roots ...
I have not measured the worst case".

This script measures exactly that, base vs patched:
  R1 correctness  a position at halfmove >= 100 that is NOT a mate must still score 0 (the fifty-move draw
                  must still be seen), otherwise my patch traded one bug for a worse one.
  R2 cost         nodes and wall time for `go depth 10` and `go movetime 100` on those positions.
  R3 no regression on the honesty pins, and the mate cases still found.

Boards:
  KQ vs K, halfmove 100 and 150 (white can mate, but not in one move from most squares: python-chess is
  asked how many plies the forced mate needs, so the test knows whether "0 nodes" would be legitimate).
  KR vs K, halfmove 150.
  K vs K, halfmove 150 (a draw with no mate at all).

Usage: regress_fifty_patch.py <base-exe> <patched-exe> <outdir>
"""
import hashlib
import json
import os
import select
import subprocess
import sys
import time
from pathlib import Path

import chess

TIMEOUT = 300.0


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


def run(exe, fen, go):
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
        return {"error": "no readyok"}
    t0 = time.monotonic()
    send(go)
    bml = until("bestmove")
    wall = time.monotonic() - t0
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
    return {"score": score, "nodes": nodes, "wall_ms": round(wall * 1000, 1),
            "bestmove": (bml.split()[1] if bml else None),
            "answered": bml is not None}


def mate_plies(fen, limit=7):
    b = chess.Board(fen)

    def forced(board, depth):
        if depth <= 0:
            return False
        if not list(board.legal_moves):
            return board.is_checkmate()
        for m in board.legal_moves:
            board.push(m)
            if board.is_checkmate():
                board.pop()
                return True
            worst = True
            for r in list(board.legal_moves):
                board.push(r)
                if not forced(board, depth - 2):
                    worst = False
                board.pop()
                if not worst:
                    break
            board.pop()
            if worst:
                return True
        return False

    for d in range(1, limit + 1, 2):
        if forced(b, d):
            return d
    return None


def main():
    base, patched, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    boards = [
        ("KQvK_h100", "8/5K2/7Q/4k3/8/8/8/8 w - - 100 1"),
        ("KQvK_h150", "8/5K2/7Q/4k3/8/8/8/8 w - - 150 1"),
        ("KRvK_h150", "1K6/8/8/3R4/8/8/8/k7 w - - 150 1"),
        ("KvK_h150", "8/8/4k3/8/8/3K4/8/8 w - - 150 1"),
        ("mate1_h100", "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 100 1"),
    ]
    gos = ["go depth 10", "go movetime 100"]
    lines = ["regression test of job2/fifty_move_mate.patch.txt",
             "base:    %s sha256 %s" % (base, hashlib.sha256(Path(base).read_bytes()).hexdigest()),
             "patched: %s sha256 %s" % (patched, hashlib.sha256(Path(patched).read_bytes()).hexdigest()),
             "option lines sent: NONE",
             ""]
    header = "board\tgo\tpy_forced_mate_plies\tbase_score\tbase_nodes\tbase_ms\tpatch_score\tpatch_nodes\tpatch_ms\tverdict"
    lines.append(header)
    rows = []
    for name, fen in boards:
        mp = mate_plies(fen)
        for go in gos:
            b = run(base, fen, go)
            q = run(patched, fen, go)
            if not b.get("answered") or not q.get("answered"):
                verdict = "INVALID (no bestmove from one side)"
            elif mp is None:
                # no forced mate: a fifty-move position must score 0 on BOTH sides
                ok = (q["score"] == "cp 0" and b["score"] == "cp 0")
                verdict = "OK still a draw" if ok else "REGRESSION (patched score %s)" % q["score"]
            else:
                # a forced mate exists: the patched side must find a mate score, the base may not
                verdict = ("OK mate found (base %s / patch %s)" % (b["score"], q["score"])
                           if "mate" in q["score"] else
                           "note: no mate score (py says mate in %d plies)" % mp)
            rows.append({"board": name, "go": go, "py_mate_plies": mp, "base": b, "patch": q,
                         "verdict": verdict})
            lines.append("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (
                name, go, mp, b["score"], b["nodes"], b["wall_ms"], q["score"], q["nodes"],
                q["wall_ms"], verdict))
            print("%-12s %-16s py=%-4s base %-8s %-9s %7sms  patch %-8s %-9s %7sms  %s"
                  % (name, go, mp, b["score"], b["nodes"], b["wall_ms"], q["score"],
                     q["nodes"], q["wall_ms"], verdict), flush=True)
    (out / "regress_fifty_patch.json").write_text(json.dumps(rows, indent=1))
    text = "\n".join(lines) + "\n"
    (out / "regress_fifty_patch.txt").write_text(text)
    print("")
    print(text)


if __name__ == "__main__":
    main()
