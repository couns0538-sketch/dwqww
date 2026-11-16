#!/usr/bin/env python3
"""swarm seat 01, job 2: is the halfmove-clock short circuit a FAULT or correct chess?

The engine, in src/search.cpp around line 2253, has:
    const bool root_drawn = !legal.empty() && (board.is_repetition() || board.halfmove_clock() >= 100
                                               || board.is_insufficient_material());
    if (root_candidates.empty() || root_drawn) { ... report without searching ... }

This script settles three separate questions with evidence, instead of guessing:

Q1. Does the short circuit also fire when the position is CHECKMATE on the board? (It must not: a
    checkmate is not a draw, whatever the counter says.)
Q2. Does it fire when the side to move can FORCE mate inside the remaining half-moves before the
    fifty-move claim? A mate one move away at halfmove 99 must be found. At halfmove 100 the engine's
    own comment at search.cpp:1301 says a mate on the hundredth half-move still wins, so the answer
    should be the mate too.
Q3. Is the answer the same on the release build?

Every case: fresh process, `position fen`, `isready` read to readyok, `go depth 6`, read to bestmove,
then a short settle and `quit`. Nothing is batched.

Usage: analyse_halfmove.py <asan-exe> <release-exe> <outdir>
"""
import json
import os
import select
import subprocess
import sys
import time
from pathlib import Path

import chess

TIMEOUT = 60.0


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


def run(exe, fen, go="go depth 6"):
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
    until("readyok")
    refusal = [l for l in buf if l.startswith("info string invalid FEN")]
    bm = None
    if not refusal:
        send(go)
        bml = until("bestmove")
        if bml:
            bm = bml.split()[1]
        time.sleep(0.2)
    send("quit")
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()
    depth_lines = [l for l in buf if l.startswith("info depth")]
    last = depth_lines[-1] if depth_lines else ""
    fields = last.split()
    nodes = fields[fields.index("nodes") + 1] if "nodes" in fields else ""
    score = ""
    if "score" in fields:
        i = fields.index("score")
        score = " ".join(fields[i + 1:i + 3])
    pv = ""
    if "pv" in fields:
        pv = " ".join(fields[fields.index("pv") + 1:])
    return {"fen": fen, "go": go, "refused": bool(refusal), "refusal": refusal,
            "bestmove": bm, "nodes": nodes, "score": score, "pv": pv,
            "depth_lines": depth_lines,
            "sanitizer": [l for l in buf if "Sanitizer" in l or "runtime error" in l]}


CHECKMATED = "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 0 1"
MATE_IN_1 = "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1"
MATE_IN_2 = "6k1/5ppp/8/8/8/8/5PPP/1R4K1 w - - 0 1"


def mate_distance(fen, limit=5):
    """Smallest number of plies to a forced mate for the side to move (odd numbers), else None."""
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
    asan, release, outdir = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    outdir.mkdir(parents=True, exist_ok=True)
    cases = []
    for hm in (0, 98, 99, 100, 101, 150):
        cases.append(("checkmated_hm%d" % hm, CHECKMATED.replace(" 0 1", " %d 1" % hm)))
    for hm in (0, 97, 98, 99, 100):
        cases.append(("mate1_hm%d" % hm, MATE_IN_1.replace(" 0 1", " %d 1" % hm)))
    for hm in (0, 95, 96, 97, 98, 99, 100):
        cases.append(("mate2_hm%d" % hm, MATE_IN_2.replace(" 0 1", " %d 1" % hm)))
    cases.append(("stalemate_hm100", "7k/5Q2/8/8/8/8/8/K7 b - - 100 1"))

    rows = []
    for name, fen in cases:
        r = run(asan, fen)
        r["case"] = name
        r["exe"] = "asan"
        r["py_mate_plies"] = mate_distance(fen, limit=5)
        rows.append(r)
        print("%-20s bm=%-6s nodes=%-6s score=%-8s py_mate_plies=%s"
              % (name, r["bestmove"], r["nodes"], r["score"], r["py_mate_plies"]), flush=True)

    release_rows = []
    for name, fen in cases:
        if name.endswith(("_hm100", "_hm99", "_hm0", "_hm97", "_hm98")):
            r = run(release, fen)
            r["case"] = name
            r["exe"] = "release"
            r["py_mate_plies"] = mate_distance(fen, limit=5)
            release_rows.append(r)

    def find(case, table=None):
        for r in (table if table is not None else rows):
            if r["case"] == case:
                return r
        return None

    v = []
    c = find("checkmated_hm100")
    v.append("Q1 checkmated board at halfmove 100: bestmove=%s score=%s nodes=%s pv='%s'"
             % (c["bestmove"], c["score"], c["nodes"], c["pv"]))
    v.append("   python-chess agrees the position is checkmate: %s"
             % chess.Board(c["fen"]).is_checkmate())
    v.append("Q2 forced mates across the counter (asan build):")
    for name, _ in cases:
        if name.startswith(("mate1_", "mate2_")):
            r = find(name)
            v.append("   %-14s py_forced_mate_in_plies=%-4s bestmove=%-6s score=%-8s nodes=%-6s pv=%s"
                     % (name, r["py_mate_plies"], r["bestmove"], r["score"], r["nodes"], r["pv"]))
    disagreements = []
    for a in rows:
        b = find(a["case"], release_rows)
        if b is None:
            continue
        if a["bestmove"] != b["bestmove"] or a["score"] != b["score"]:
            disagreements.append((a["case"], a["bestmove"], a["score"], b["bestmove"], b["score"]))
    v.append("Q3 asan vs release: %d compared, %d disagreements"
             % (len(release_rows), len(disagreements)))
    for d in disagreements:
        v.append("   %s asan=%s/%s release=%s/%s" % d)

    (outdir / "analyse_halfmove.json").write_text(json.dumps(
        {"asan": rows, "release": release_rows, "verdicts": v}, indent=1))
    (outdir / "analyse_halfmove.txt").write_text("\n".join(v) + "\n")
    print("")
    print("\n".join(v))


if __name__ == "__main__":
    main()
