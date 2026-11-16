#!/usr/bin/env python3
"""swarm seat 01: settle seat 12's REPETITION claim properly (my first attempt measured nothing, S-F25).

Seat 12's patch bypasses the root adjudication when the side to move has an immediate mate, and that bypass
sits inside the shared condition, so it should also rescue a root drawn by THREE-FOLD REPETITION.

Construction that actually works: start from the standard start position via `position startpos moves ...`
so the engine's own key history is real, shuffle knights out and back TWICE (4 plies per cycle, same side to
move at each cycle end), which makes the start-like position occur three times, and then check what the
engine answers.

But the start position has no mate in 1, so to test the MATE I need a repeated position that also has mate in
1. Solution: repeat a cycle that RETURNS TO A POSITION WITH MATE IN 1. Use a root FEN that HAS knights, shuffle
two knight pairs out and back (repeatable), and confirm with python-chess that the final board is a threefold
AND has a mate in 1.

Verification of the setup is part of the test: if python-chess does not report a threefold, the case is
reported as SETUP FAILED and no verdict is drawn (that is exactly the mistake S-F25 records).

Usage: repetition_door2.py <base-exe> <mine-exe> <s12-exe> <outdir>
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


def run(exe, setup, go="go depth 12"):
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

    for line in setup:
        send(line)
    send("isready")
    if until("readyok") is None:
        p.kill()
        return {"error": "no readyok"}
    bad = [l for l in buf if l.startswith("info string illegal move")
           or l.startswith("info string invalid FEN")]
    send(go)
    bml = until("bestmove")
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
    return {"score": score, "nodes": nodes, "bestmove": bml.split()[1] if bml else None,
            "depths": len(dl), "rejected_lines": bad}


def find_threefold_with_mate(root_fen, cycle, max_cycles=3):
    """Replay root_fen + cycle*n with python-chess, return (moves, is_threefold, has_mate_in_1, mate_move)."""
    for n in range(2, max_cycles + 1):
        b = chess.Board(root_fen)
        moves = []
        ok = True
        for _ in range(n):
            for m in cycle:
                try:
                    mv = chess.Move.from_uci(m)
                except ValueError:
                    ok = False
                    break
                if mv not in b.legal_moves:
                    ok = False
                    break
                b.push(mv)
                moves.append(m)
            if not ok:
                break
        if not ok:
            continue
        threefold = b.is_repetition(3)
        mate = None
        for m in b.legal_moves:
            b.push(m)
            if b.is_checkmate():
                mate = m.uci()
            b.pop()
        if threefold and mate:
            return moves, threefold, mate
    return None, False, None


def main():
    base, mine, s12, out = sys.argv[1], sys.argv[2], sys.argv[3], Path(sys.argv[4])
    out.mkdir(parents=True, exist_ok=True)
    # A root WITH knights (so a shuffle is legal) and with a rook mate available after the shuffle.
    candidates = [
        ("knights_and_rook",
         "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/R1BQKBNR w KQkq - 0 1",
         ["g1f3", "g8f6", "f3g1", "f6g8"]),
        ("both_knights",
         "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
         ["g1f3", "g8f6", "f3g1", "f6g8"]),
    ]
    lines = ["settling seat 12's repetition claim — setup is VERIFIED with python-chess before any verdict",
             "go: 'go depth 12'; every case a fresh process; no setoption sent"]
    for label, exe in (("base", base), ("mine", mine), ("seat12", s12)):
        lines.append("%-7s %s sha256 %s" % (label, exe,
                                           hashlib.sha256(Path(exe).read_bytes()).hexdigest()))
    lines.append("")
    rows = []
    for name, root, cycle in candidates:
        moves, threefold, mate = find_threefold_with_mate(root, cycle)
        setup = ["position fen " + root]
        if moves:
            setup.append("position fen " + root + " moves " + " ".join(moves))
        row = {"case": name, "root": root, "moves": moves, "py_threefold": threefold,
               "py_mate_in_1": mate, "result": {}}
        if not threefold or not mate:
            row["verdict"] = "SETUP FAILED — no verdict drawn (a threefold root with a mate in 1 was not built)"
            lines.append("%s\tSETUP FAILED (threefold=%s mate=%s)" % (name, threefold, mate))
            print("%-18s SETUP FAILED threefold=%s mate=%s" % (name, threefold, mate), flush=True)
            rows.append(row)
            continue
        for label, exe in (("base", base), ("mine", mine), ("seat12", s12)):
            r = run(exe, setup)
            row["result"][label] = r
            print("%-18s %-7s score=%-8s nodes=%-7s bm=%-6s rejected=%s"
                  % (name, label, r.get("score"), r.get("nodes"), r.get("bestmove"),
                     len(r.get("rejected_lines", []))), flush=True)
        found = [k for k, v in row["result"].items() if v.get("bestmove") == mate]
        row["verdict"] = ("mate in 1 (%s) found by: %s" % (mate, ",".join(found))) if found else "NOBODY found it"
        lines.append("%s\tthreefold=yes mate=%s\t%s\t%s" % (
            name, mate,
            " | ".join("%s %s/%s" % (k, v.get("score"), v.get("nodes")) for k, v in row["result"].items()),
            row["verdict"]))
        rows.append(row)
    (out / "repetition_door2.json").write_text(json.dumps(rows, indent=1))
    (out / "repetition_door2.txt").write_text("\n".join(lines) + "\n")
    print("")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
