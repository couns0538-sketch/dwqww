#!/usr/bin/env python3
"""swarm seat 01: what does seat 12's two_doors_mate patch fix that MY one-line patch does not?

Seat 12's patch does not simply remove the halfmove>=100 test. It keeps every root adjudication and only
bypasses it when the side to move has a move that mates IMMEDIATELY (it makes each legal move and checks for
checkmate with no reply). Mine removes the counter from the root test entirely.

So the two patches differ exactly where a mate is reachable but NOT in one ply:
  board at halfmove 100 where the side to move has a mate in 3 plies (mate in 2 moves).
  Prediction: mine finds it (the root is searched), seat 12's does not (no immediate mate, so the root is
  still adjudicated drawn).
And a board with an IMMEDIATE mate (mate in 1) must come out right on BOTH.

Usage: compare_two_fixes.py <mine-exe> <s12-exe> <outdir>
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


def run(exe, fen, go="go depth 8"):
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
    send(go)
    bml = until("bestmove")
    time.sleep(0.1)
    send("quit")
    try:
        p.wait(timeout=60)
    except Exception:
        p.kill()
    dl = [l for l in buf if l.startswith("info depth")]
    score = nodes = pv = ""
    if dl:
        f = dl[-1].split()
        if "score" in f:
            i = f.index("score")
            score = " ".join(f[i + 1:i + 3])
        if "nodes" in f:
            nodes = f[f.index("nodes") + 1]
        if "pv" in f:
            pv = " ".join(f[f.index("pv") + 1:])
    return {"score": score, "nodes": nodes, "pv": pv,
            "bestmove": (bml.split()[1] if bml else None), "answered": bml is not None}


def mate_in_n(fen, limit=5):
    """Smallest ODD number of plies to a forced mate for the side to move, else None."""
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
    mine, s12, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    boards = [
        # immediate mate (1 ply) - both patches must fix this
        ("mate_in_1_ply", "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 100 1"),
        # mate in 3 plies (verified by a forced-mate search, not by eye): needs a real search,
        # so this is where the two patches must differ
        ("mate_in_3_plies", "8/8/8/8/2K4Q/8/8/1k6 w - - 100 1"),
        # no mate at all in a bare endgame: both must still say cp 0
        ("no_mate_KQvK", "8/5K2/7Q/4k3/8/8/8/8 w - - 150 1"),
    ]
    lines = ["what seat 12's two_doors_mate fixes that my one-line patch does not",
             "mine: %s sha256 %s" % (mine, hashlib.sha256(Path(mine).read_bytes()).hexdigest()),
             "s12 : %s sha256 %s" % (s12, hashlib.sha256(Path(s12).read_bytes()).hexdigest()),
             "go: 'go depth 8', no setoption sent", ""]
    lines.append("board\tpy_forced_mate_plies\tmine_score\tmine_nodes\ts12_score\ts12_nodes\tverdict")
    rows = []
    for name, fen in boards:
        mp = mate_in_n(fen)
        a = run(mine, fen)
        b = run(s12, fen)
        if mp is None:
            verdict = ("both draw (correct)" if a["score"] == "cp 0" and b["score"] == "cp 0"
                       else "MISMATCH: mine %s s12 %s" % (a["score"], b["score"]))
        else:
            mine_ok = "mate" in a["score"]
            s12_ok = "mate" in b["score"]
            if mine_ok and not s12_ok:
                verdict = "MINE FINDS IT, SEAT 12 DOES NOT"
            elif mine_ok and s12_ok:
                verdict = "both find it"
            elif not mine_ok and not s12_ok:
                verdict = "NEITHER finds it"
            else:
                verdict = "seat 12 finds it, mine does not"
        rows.append({"board": name, "fen": fen, "py_mate_plies": mp, "mine": a, "s12": b,
                     "verdict": verdict})
        lines.append("%s\t%s\t%s\t%s\t%s\t%s\t%s" % (name, mp, a["score"], a["nodes"],
                                                     b["score"], b["nodes"], verdict))
        print("%-16s py=%-4s mine %-8s %-7s  s12 %-8s %-7s  %s"
              % (name, mp, a["score"], a["nodes"], b["score"], b["nodes"], verdict), flush=True)
    (out / "compare_two_fixes.json").write_text(json.dumps(rows, indent=1))
    text = "\n".join(lines) + "\n"
    (out / "compare_two_fixes.txt").write_text(text)
    print("")
    print(text)


if __name__ == "__main__":
    main()
