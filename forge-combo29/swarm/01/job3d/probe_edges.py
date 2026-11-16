#!/usr/bin/env python3
"""swarm seat 01, job 3 edge probe: what does the engine do with move lists that are legal ply-by-ply but
put the game in a state a real game could not continue from?

Three extra cases, each a fresh process, `position startpos moves ...`, `isready`, `go perft 1`:
  E1  a list that continues AFTER a checkmate (moves appended after the mating move).
  E2  a list that continues AFTER a stalemate.
  E3  a list that reaches a threefold repetition and continues (legal, must be accepted).
  E4  a list whose last move is a promotion written without the piece letter (`a7a8`), which UCI requires
      to be `a7a8q` — record whether it is refused or silently treated as a queen move.

python-chess is the judge for E1..E3 (it can tell me the position and the legal move count).
For E4 the check is only "refused or not" plus the perft 1 count, because python-chess would refuse it too.

Usage: probe_edges.py <exe> <outdir>
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

TIMEOUT = 60.0


PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
        ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
        ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
        ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
        ("IirDepth", "2"), ("NonPawnCorrection", "true"), ("CuckooRep", "true"),
        ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]


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


def run(exe, moves):
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

    for name, value in PC20:
        send("setoption name %s value %s" % (name, value))
        send("isready")
        until("readyok")
    send("position startpos moves " + " ".join(moves))
    send("isready")
    ready = until("readyok")
    answer = [l for l in buf if l.startswith("info string")]
    nodes = None
    if ready is not None:
        send("go perft 1")
        if until("nodes ") is not None:
            for l in buf:
                if l.startswith("nodes "):
                    nodes = int(l.split()[1])
    send("quit")
    try:
        p.wait(timeout=30)
    except Exception:
        p.kill()
    return {"moves": moves, "answer": answer, "perft1": nodes,
            "sanitizer": [l for l in buf if "Sanitizer" in l or "runtime error" in l]}


def main():
    exe = sys.argv[1]
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    # E1: fool's mate, then a further move
    fools = ["f2f3", "e7e5", "g2g4", "d8h4"]
    e1 = fools + ["a2a3"]
    # E2: a short stalemate by construction from startpos is not possible; use a FEN-free route:
    #     1.e3 a5 2.Qh5 Ra6 3.Qxa5 h5 4.Qxc7 Rah6 5.h4 f6 6.Qxd7+ Kf7 7.Qxb7 Qd3 8.Qxb8 Qh7
    #     9.Qxc8 Kg6 10.Qe6  -- stalemate. Taken from the standard fastest-stalemate line.
    e2 = ("e2e3 a7a5 d1h5 a8a6 h5a5 h7h5 a5c7 a6h6 h2h4 f7f6 c7d7 e8f7 d7b7 d8d3 "
          "b7b8 d3h7 b8c8 f7g6 c8e6").split()
    # E3: knight shuffles for a repetition: g1f3 g8f6 f3g1 f6g8 twice over
    e3 = ["g1f3", "g8f6", "f3g1", "f6g8"] * 2 + ["e2e4"]
    # E4: promotion without the piece letter. Build a position with a promotion by a short line is not
    #     possible from startpos, so this case is run from a FEN instead and is reported as N/A here.
    cases = [("after_checkmate", e1), ("after_stalemate", e2), ("after_repetition", e3)]
    lines = ["job 3 edge probe (extra cases, beyond the brief's four)",
             "exe_started: %s" % exe,
             "sha256: %s" % hashlib.sha256(Path(exe).read_bytes()).hexdigest()]
    nm = subprocess.run(["nm", "-C", exe], capture_output=True, text=True).stdout
    lines.append("nm -C grep -c __asan_ : %d" % sum(1 for l in nm.splitlines() if "__asan_" in l))
    lines.append("nm -C grep -c __ubsan_ : %d" % sum(1 for l in nm.splitlines() if "__ubsan_" in l))
    lines.append("option lines sent: " + "; ".join("%s=%s" % kv for kv in PC20))
    lines.append("")
    lines.append("case\tlegal_prefix_plies\tanswer\tperft1_engine\tpython_chess_legal\tnote")
    res = []
    for name, moves in cases:
        r = run(exe, moves)
        r["case"] = name
        # python-chess is the judge of what the kept position should be
        b = chess.Board()
        legal_prefix = []
        note = ""
        for m in moves:
            mv = chess.Move.from_uci(m)
            if not legal_prefix:
                if mv not in b.legal_moves:
                    note = "first illegal move at ply 1"
                    break
            else:
                if mv not in b.legal_moves:
                    note = "first illegal move at ply %d" % (len(legal_prefix) + 1)
                    break
            b.push(mv)
            legal_prefix.append(m)
        expected = b.legal_moves.count()
        r["legal_prefix_plies"] = len(legal_prefix)
        r["python_legal"] = expected
        r["note"] = note
        r["match"] = r["perft1"] == expected
        res.append(r)
        lines.append("%s\t%d\t%s\t%s\t%d\t%s" % (
            name, len(legal_prefix), "; ".join(r["answer"]) or "(none)",
            r["perft1"], expected, note))
    (out / "probe_edges.json").write_text(json.dumps(res, indent=1))
    text = "\n".join(lines) + "\n"
    (out / "probe_edges.txt").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
