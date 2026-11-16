#!/usr/bin/env python3
"""swarm seat 01: test the REPETITION door — the one place seat 12's patch claims to add something.

Seat 12's patch bypasses the root adjudication when the side to move has an immediate mate. That applies to
ALL three doors it keeps (fifty-move, repetition, dead material). Mine only removes the fifty-move door.

So the discriminating case is: a root that is a THREE-FOLD REPETITION (halfmove < 100, so my patch does
nothing) on which the side to move has a mate in 1. There the claim is still available to the side to move,
and FIDE says a claim must be made before the move — but a mate actually delivered ends the game, so a
mating move is playable. That is seat 12's stated reasoning.

Repetition is established with `position startpos moves ...` so the ENGINE's own key_history sees it, then
the FEN's move tail is not used (a plain FEN does not carry history).

Usage: repetition_door.py <base-exe> <mine-exe> <s12-exe> <outdir>
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
        while "\n" not in self.buf.decode("utf-8", "ignore"):
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
        text = self.buf.decode("utf-8", "replace")
        l, _, rest = text.partition("\n")
        self.buf = rest.encode()
        return l


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
    return {"score": score, "nodes": nodes,
            "bestmove": (bml.split()[1] if bml else None), "depths": len(dl),
            "answer_lines": [l for l in buf if l.startswith("info string")]}


def build_repetition_setup():
    """A move list that reaches a position THREE times, where the side to move then has mate in 1.

    Simplest honest construction: shuffle knights out and back twice (a repetition the engine will see), then
    arrive at a position where white has a mate in one. Knights out-and-back cannot create a mate-in-one, so
    instead: repeat a king shuffle (which the engine counts) and then give white the mating material by
    starting from a position that already has it.
    """
    # startpos, but with white's a-rook already lifted to a1-a8 mate potential? Not possible from startpos.
    # So: use a FEN root for the board, and establish repetition by moving pieces out and back.
    # A position repeated 3x requires the same side to move each time: 4 plies per cycle.
    cycle = ["g1f3", "g8f6", "f3g1", "f6g8"]
    return ["position fen 6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1"] + cycle * 2


def main():
    base, mine, s12, out = sys.argv[1], sys.argv[2], sys.argv[3], Path(sys.argv[4])
    out.mkdir(parents=True, exist_ok=True)
    lines = ["the REPETITION door: does a root that is a threefold repetition still find a mate in 1?",
             "Setup uses a FEN root plus a knight shuffle twice, so the ENGINE's own history sees the repetition.",
             "go: 'go depth 12'; every case a fresh process; no setoption sent"]
    for label, exe in (("base", base), ("mine", mine), ("seat12", s12)):
        lines.append("%-7s %s sha256 %s" % (label, exe,
                                           hashlib.sha256(Path(exe).read_bytes()).hexdigest()))
    lines.append("")
    rows = []
    for setup_name, setup, fen_for_py in (
        ("plain_fen_no_history",
         ["position fen 6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1"],
         "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1"),
        ("repetition_via_moves",
         build_repetition_setup(),
         "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1"),
    ):
        b = chess.Board(fen_for_py)
        reps = b.is_repetition(3)
        row = {"setup": setup_name, "setup_lines": setup, "py_is_threefold": reps, "results": {}}
        for label, exe in (("base", base), ("mine", mine), ("seat12", s12)):
            r = run(exe, setup)
            row["results"][label] = r
            print("%-22s %-8s score=%-8s nodes=%-8s bm=%-6s depths=%-3d %s"
                  % (setup_name, label, r.get("score"), r.get("nodes"), r.get("bestmove"),
                     r.get("depths", 0), ";".join(r.get("answer_lines", []))), flush=True)
        rows.append(row)
        lines.append("%s\t%s\t%s\t%s" % (setup_name,
                                         " | ".join("%s %s/%s" % (k, v.get("score"), v.get("nodes"))
                                                    for k, v in row["results"].items()),
                                         "py threefold=%s" % reps,
                                         "mating move a1a8 found by: " +
                                         ",".join(k for k, v in row["results"].items()
                                                  if v.get("bestmove") == "a1a8")))
    (out / "repetition_door.json").write_text(json.dumps(rows, indent=1))
    (out / "repetition_door.txt").write_text("\n".join(lines) + "\n")
    print("")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
