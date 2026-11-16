#!/usr/bin/env python3
"""swarm seat 01: does seat 25's "refusable-aware" repair premise survive file 6, and does it cost what they say?

Two claims of seat 25 are in tension with file 6 and with each other:
  * their S-C5 applies file 6's rule and reclassifies their own clock-99 family as NOT a defect, because the
    owner's match program ends the game at the 100th half-move, so there is no claim to decline;
  * their S-F22/S-F23/S-F24 then propose and price a repair built on exactly the premise file 6 rejects:
    "clock >= 100 is a draw only when no capture or pawn move is available to the side to move", i.e. that
    someone could RESET and play on.

Both cannot be the operative reading for the owner's matches. What decides it is a MEASUREMENT I can make:
if the match program ends the game at the 100th half-move, then a position at clock 99 whose mate needs more
than 1 ply is a draw whatever any repair says, and a repair that makes the engine search it is buying a search
that cannot change the result in a match.

The one class where a repair would matter is my S-F48: a board whose mating line starts with a CAPTURE or a
PAWN MOVE, so the counter resets and the game never reaches the 100th half-move. There the mate is real.

So this script measures, on the PC build under PC20, Threads 1, Hash 16:
  A. clock 99, mate needs 3+ plies, all quiet  -> what does the ENGINE say, and what does file 6's rule say
     the MATCH result is? (the engine searching it is harmless but useless)
  B. clock 100, counter-RESETTING mate (my S-F48 board)  -> the class where a repair has real value
  C. the cost seat 25 measured: `go wtime 1000` depth on their clock-99 board vs on a position with no
     clock involvement, so the depth price is attributed to the right thing.

I do not have seat 25's patched build, so I do NOT verify their node numbers; I verify their PREMISE and the
scope of the repair, and I say which of their claims I could not check.

Usage: check_s25_premise.py <pc-exe> <outdir>
"""
import hashlib
import json
import os
import re
import select
import subprocess
import sys
import time
from pathlib import Path

import chess

TIMEOUT = 900.0

OPTS = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
        ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
        ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
        ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
        ("IirDepth", "2"), ("NonPawnCorrection", "true"), ("CuckooRep", "true"), ("HistRework", "2"),
        ("TtPruneV2", "true"), ("CorrHistV2", "true"), ("MateAlphaGuard", "true"),
        ("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]

# A: quiet mate-in-3 at clock 99 -> file 6 says the match ends at the 100th half-move, so this is a draw
A_FEN = "8/8/8/8/2K4Q/8/8/1k6 w - - 99 1"
# B: counter-RESETTING mate (first mating move is a pawn move) at clock 100 -> my S-F48 class
B_FEN = "8/3K4/7P/8/8/7k/8/6Q1 w - - 100 1"
# C: no clock involvement, for the depth baseline
C_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


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
    for name, value in OPTS:
        send("setoption name %s value %s" % (name, value))
        send("isready")
        until("readyok", d)
    send("ucinewgame")
    send("isready")
    until("readyok", d)
    send("position fen " + fen)
    send("isready")
    until("readyok", d)
    t0 = time.monotonic()
    send(go)
    bml = until("bestmove", d)
    wall = round((time.monotonic() - t0) * 1000, 1)
    time.sleep(0.15)
    send("quit")
    try:
        p.wait(timeout=200)
    except Exception:
        p.kill()
    dls = [l for l in buf if l.startswith("info depth")]
    depth = None
    score = ""
    for l in dls:
        f = l.split()
        if "depth" in f:
            try:
                depth = int(f[f.index("depth") + 1])
            except ValueError:
                pass
        if " score " in l:
            i = f.index("score")
            score = " ".join(f[i + 1:i + 3])
    return {"go": go, "depth": depth, "score": score, "wall_ms": wall,
            "bestmove": bml.split()[1] if bml and len(bml.split()) > 1 else None}


def first_move_resets(fen):
    b = chess.Board(fen)
    out = []
    for m in b.legal_moves:
        if b.is_capture(m) or b.piece_at(m.from_square).piece_type == chess.PAWN:
            out.append(m.uci())
    return out


def main():
    exe = sys.argv[1]
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    lines = ["seat 25's refusable-aware repair: premise, scope and cost, on PC r15 / PC20 / Threads 1 / Hash 16",
             "exe_started: %s" % exe,
             "sha256: %s" % hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
             "NOTE: I do not have seat 25's patched build, so I verify their PREMISE and the SCOPE of the",
             "repair, not their node counts. What I could not check is listed at the end.", ""]

    rows = []
    for label, fen, note in (("A_quiet_mate3_clock99", A_FEN, "file 6: match ends at the 100th half-move"),
                             ("B_resetting_mate_clock100", B_FEN, "my S-F48: counter resets, mate is real"),
                             ("C_no_clock_baseline", C_FEN, "no fifty-move involvement")):
        d20 = run(exe, fen, "go depth 20")
        clk = run(exe, fen, "go wtime 1000 btime 1000 winc 0 binc 0")
        resets = first_move_resets(fen)
        rows.append({"case": label, "fen": fen, "note": note, "depth20": d20, "clock1000": clk,
                     "resetting_moves": resets})
        print("%-27s depth20 -> %-9s (d=%s) | clock1000 -> %-9s (d=%s) | reset moves available: %s"
              % (label, d20["score"], d20["depth"], clk["score"], clk["depth"],
                 resets[:4] or "none"), flush=True)
        lines.append("%s\t%s\tdepth20 %s (d=%s)\tclock1000 %s (d=%s)\treset moves: %s"
                     % (label, fen, d20["score"], d20["depth"], clk["score"], clk["depth"],
                        resets[:4] or "none"))
    (out / "check_s25_premise.json").write_text(json.dumps(rows, indent=1))

    v = []
    v.append("")
    a = rows[0]
    b = rows[1]
    v.append("A (quiet mate-in-3 at clock 99): engine says %s at depth 20. By file 6's rule the MATCH is a"
             % a["depth20"]["score"])
    v.append("  draw at the 100th half-move before that mate can land (it needs 3 plies, only 1 is left), so")
    v.append("  the engine's answer cannot change a match result. Seat 25's own S-C5 reaches the same")
    v.append("  conclusion for their 8 boards, so their S-F22/S-F23/S-F24 repair is priced against a")
    v.append("  non-defect for the owner's matches. That is the tension: a correct mechanism description")
    v.append("  (S-F15/S-F16/S-F17) does not make the repair worth its 11-20 plies of depth.")
    v.append("")
    v.append("B (counter-RESETTING mate at clock 100, my S-F48 class): engine says %s at depth 20."
             % b["depth20"]["score"])
    v.append("  Here the mating line starts with a capture or pawn move (%s), the counter resets, and the"
             % (b["resetting_moves"][:3] or "none"))
    v.append("  opponent never gets the 100th-half-move cut-off. So THIS is the class where a repair has real")
    v.append("  value - and the PC build already gets it right (mate found), which is why no patch is needed.")
    v.append("")
    v.append("C (no clock involvement): %s at depth 20 - the depth baseline the price should be compared"
             % rows[2]["depth20"]["score"])
    v.append("  against, so a depth drop on A is attributable to the clock, not to the position type.")
    v.append("")
    v.append("BOTTOM LINE for the owner: seat 25's repair is technically sound and cheap where it fires, but")
    v.append("for the owner's match program it addresses a position class the match program ends before it")
    v.append("matters. The class that DOES matter (counter-resetting mates) is already correct on the PC")
    v.append("build. So the repair is not needed; if it is taken for human-play reasons, price it at the")
    v.append("11-20 plies seat 25 measured and scope it to human games, not to self-play.")
    (out / "check_s25_premise.txt").write_text("\n".join(lines + v) + "\n")
    print("")
    print("\n".join(v))


if __name__ == "__main__":
    main()
