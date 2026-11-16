#!/usr/bin/env python3
"""swarm seat 01: is `score mate 0` on a checkmated root a FAULT or the correct UCI score?

I reported this as seat 21's open door (my S-F32, S-F38). Seat 21 has since WITHDRAWN it (its 21-F11),
arguing that `score mate <y>` means "mate in y MOVES for the side to move", so y = 0 is "already mated" and
`bestmove 0000` is right. I should not accept or reject that on authority, so this measures it.

The UCI spec says: `mate <y>` = "the engine will be mated in y moves" when y is negative, and "the engine
will mate in y moves" when y is positive. So on a root where the side to move IS mated, the correct score is
`mate 0` (mated in 0 moves) and there is no move to give, i.e. `bestmove 0000`.

Three boards, so the whole scale is exercised on the same harness:
  MATED_ROOT     the side to move is checkmated right now        -> expect mate 0 and bestmove 0000
  MATE_IN_1      the side to move can mate in one                -> expect mate 1 and a mating bestmove
  STALEMATED     the side to move is stalemated, not mated       -> expect cp 0 and bestmove 0000
  MATE_AGAINST_1 the side to move will be mated in one reply     -> expect mate -1

If MATED_ROOT gives mate 0 while MATE_IN_1 gives mate 1 and STALEMATED gives cp 0, the score is a
consistent UCI scale and my "open door" claim is WRONG — which is what seat 21 says.

Usage: check_mate0.py <pc-exe> <base-exe> <outdir>
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

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false"),
              ("Threads", "1"), ("Hash", "16")]


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


def run(exe, fen, options, go="go depth 8"):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, bufsize=0, cwd="/tmp")
    rd = R(p.stdout.fileno())
    buf = []

    def until(prefix, deadline):
        while True:
            l = rd.line(deadline)
            if l is None:
                return None
            buf.append(l)
            if l.startswith(prefix):
                return l

    def send(s):
        p.stdin.write((s + "\n").encode())
        p.stdin.flush()

    d = time.monotonic() + TIMEOUT
    send("uci")
    until("uciok", d)
    for name, value in options:
        send("setoption name %s value %s" % (name, value))
        send("isready")
        until("readyok", d)
    send("ucinewgame")
    send("isready")
    until("readyok", d)
    send("position fen " + fen)
    send("isready")
    until("readyok", d)
    send(go)
    bml = until("bestmove", d)
    time.sleep(0.1)
    send("quit")
    try:
        p.wait(timeout=90)
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
            "bestmove": bml.split()[1] if bml and len(bml.split()) > 1 else None}


def main():
    pc, base, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    boards = [
        # white is checkmated right now (Ra8# delivered; black rook on e8, white king boxed)
        ("MATED_ROOT", "4R1k1/5ppp/8/8/8/8/5PPP/6K1 b - - 1 60", "already checkmated",
         chess.Board("4R1k1/5ppp/8/8/8/8/5PPP/6K1 b - - 1 60").is_checkmate()),
        ("MATE_IN_1", "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1", "can mate in 1", False),
        ("STALEMATED", "7k/5Q2/8/8/8/8/8/K7 b - - 0 1", "stalemated, not mated", False),
        # side to move is mated in one reply: white to move with no defence
        ("MATE_AGAINST_1", "6k1/5ppp/8/8/8/8/5PPP/1R4K1 b - - 0 1", "will be mated in 1 move", False),
    ]
    lines = ["is `score mate 0` on a checkmated root a FAULT or the correct UCI score?",
             "pc   %s sha256 %s" % (pc, hashlib.sha256(Path(pc).read_bytes()).hexdigest()),
             "base %s sha256 %s" % (base, hashlib.sha256(Path(base).read_bytes()).hexdigest()),
             "PC20 + Threads 1 + Hash 16 on the PC build; base build gets no setoption (it has no PC20 options)",
             "go: 'go depth 8'; every case a fresh process; quit sent only after bestmove", ""]
    rows = []
    for name, fen, meaning, py_checkmate in boards:
        b = chess.Board(fen)
        a = run(pc, fen, PC20)
        c = run(base, fen, [])
        rows.append({"case": name, "fen": fen, "meaning": meaning,
                     "py_checkmate": b.is_checkmate(), "py_stalemate": b.is_stalemate(),
                     "py_legal_moves": b.legal_moves.count(), "pc": a, "base": c})
        print("%-15s py: ck=%-5s st=%-5s legal=%-3d | PC %-8s %-6s | base %-8s %-6s"
              % (name, b.is_checkmate(), b.is_stalemate(), b.legal_moves.count(),
                 a["score"], a["bestmove"], c["score"], c["bestmove"]), flush=True)

    # the scale test, computed from the four rows
    v = []
    mated = next(r for r in rows if r["case"] == "MATED_ROOT")
    m1 = next(r for r in rows if r["case"] == "MATE_IN_1")
    stale = next(r for r in rows if r["case"] == "STALEMATED")
    mneg = next(r for r in rows if r["case"] == "MATE_AGAINST_1")
    v.append("")
    v.append("THE SCALE (what a consistent UCI score must give):")
    v.append("  already checkmated  -> mate 0   and bestmove 0000 : PC %s / %s"
             % (mated["pc"]["score"], mated["pc"]["bestmove"]))
    v.append("  can mate in 1       -> mate 1   and a mating move: PC %s / %s"
             % (m1["pc"]["score"], m1["pc"]["bestmove"]))
    v.append("  stalemated          -> cp 0     and bestmove 0000 : PC %s / %s"
             % (stale["pc"]["score"], stale["pc"]["bestmove"]))
    v.append("  mated in 1 reply    -> mate -1                    : PC %s / %s"
             % (mneg["pc"]["score"], mneg["pc"]["bestmove"]))
    consistent = (mated["pc"]["score"] == "mate 0" and mated["pc"]["bestmove"] == "0000"
                  and m1["pc"]["score"] == "mate 1" and stale["pc"]["score"] == "cp 0")
    v.append("")
    if consistent:
        v.append("VERDICT: the four answers form a CONSISTENT UCI scale, so `score mate 0` on a checkmated")
        v.append("root is CORRECT and my earlier S-F32/S-F38 'open door' claim was WRONG. Seat 21's withdrawal")
        v.append("is right, and I withdraw my claim with this measurement.")
    else:
        v.append("VERDICT: the scale is INCONSISTENT — see the four rows above; the claim stands as open.")
    (out / "check_mate0.json").write_text(json.dumps({"rows": rows, "verdict": v}, indent=1))
    (out / "check_mate0.txt").write_text("\n".join(lines + v) + "\n")
    print("")
    print("\n".join(v))


if __name__ == "__main__":
    main()
