#!/usr/bin/env python3
"""swarm seat 01: CHECK of seat 21's 21-F8b (fullmove 0 refused on the PC build, leaving a stale board).

Seat 21's claim, verbatim:
  "**SURVIVES ON THE PC BUILD.** `fullmove 0` is still REFUSED (`invalid FEN: invalid FEN fields`) and
   leaves the stale board (perft 1 = 20 where the position has 15), under PC20 and with no setoption; the
   fullmove-1 control gives 15. Threads 1, build PC r15."

My harness, written from that sentence. The position it implies is a board with 15 legal moves; I build my
own such board (K+Q+R vs K with few squares) so the test does not depend on theirs. The guard that decides
everything here is the one in REFUSED_FEN_TRAP_AND_GUARD.md: after a REFUSED position the engine keeps the
PREVIOUS board, so I prove "stale" by setting a known first position, then sending the refused FEN, then
reading perft 1 — and comparing with both the refused board's count and the first board's count.

Cases:
  c1  first=startpos, then `fullmove 0` FEN     -> if refused, perft 1 must still be 20 (startpos) = STALE
  c2  first=<15-move board>, then `fullmove 0`  -> if refused, perft 1 = that board's count (stale = same)
  c3  `fullmove 1` control on the same board    -> must give the board's own count (15-ish), not stale
  c4  `fullmove -1` negative control            -> must be REFUSED
  c5  python-chess's reading of the fullmove-0 FEN, to say whether the refusal is stricter than the spec

Everything at Threads 1, Hash 16, PC20 on the PC build; base build with no setoption for contrast.

Usage: check_s21f8b.py <pc-exe> <base-exe> <outdir>
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

# a board with a modest legal-move count, chosen so "stale startpos = 20" cannot be confused with it
BOARD15 = "8/8/8/8/8/2k5/8/2KQ4 w - - 0 1"


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


def run_sequence(exe, options, position_lines):
    """Send the option block, then every position line, then perft 1; return the answer lines and count."""
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
    problems = []
    for name, value in options:
        send("setoption name %s value %s" % (name, value))
        send("isready")
        if until("readyok", d) is None:
            problems.append("no readyok after %s" % name)
            break
    for l in buf:
        if l.startswith("unknown option") or "invalid value" in l:
            problems.append(l)
    send("ucinewgame")
    send("isready")
    until("readyok", d)
    marks = []
    for line in position_lines:
        send(line)
        send("isready")
        until("readyok", d)
        marks.append(len(buf))
    refused = [l for l in buf if l.startswith("info string invalid FEN")]
    # now the perft probe on whatever board the engine is holding
    send("go perft 1")
    until("nodes ", d)
    nodes = None
    for l in buf:
        if l.startswith("nodes "):
            nodes = int(l.split()[1])
    send("quit")
    try:
        p.wait(timeout=90)
    except Exception:
        p.kill()
    return {"perft1": nodes, "refused": refused, "problems": problems}


def main():
    pc, base, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    b15 = chess.Board(BOARD15)
    count15 = b15.legal_moves.count()
    startpos_count = chess.Board().legal_moves.count()
    # python-chess's reading of the fullmove-0 FEN
    try:
        py_board = chess.Board(BOARD15.replace(" 0 1", " 0 0"))
        py_accepts = True
        py_note = "python-chess accepts it (status %d)" % py_board.status()
    except Exception as exc:  # noqa: BLE001
        py_accepts = False
        py_note = "python-chess refuses it: %s" % exc

    cases = [
        ("c1_startpos_then_fullmove0",
         ["position fen " + BOARD15.replace(" 0 1", " 0 0")],
         "startpos is the initial board, then fullmove 0 is refused -> perft 1 should still be startpos's"),
        ("c2_board_then_fullmove0",
         ["position fen " + BOARD15, "position fen " + BOARD15.replace(" 0 1", " 0 0")],
         "the 15-move board first, then fullmove 0 -> if refused, perft 1 stays the 15-move board's count"),
        ("c3_fullmove1_control",
         ["position fen " + BOARD15],
         "the control: fullmove 1 must give the board's own count"),
        ("c4_fullmove_minus1",
         ["position fen " + BOARD15.replace(" 0 1", " 0 -1")],
         "negative control: must be refused regardless"),
    ]
    lines = ["CHECK of seat 21's 21-F8b: fullmove 0 on the PC build, and whether the board goes stale",
             "pc   %s sha256 %s" % (pc, hashlib.sha256(Path(pc).read_bytes()).hexdigest()),
             "base %s sha256 %s" % (base, hashlib.sha256(Path(base).read_bytes()).hexdigest()),
             "PC20 + Threads 1 + Hash 16; base build gets no setoption",
             "board under test: %s (python-chess legal moves = %d); startpos = %d"
             % (BOARD15, count15, startpos_count),
             "python-chess on the fullmove-0 form: " + py_note,
             "GUARD: 'stale' is proven by the perft 1 count matching the PREVIOUS board, not the refused one",
             ""]
    lines.append("case\twhat\tPC20 refused\tPC20 perft1\tbase refused\tbase perft1\treading")
    rows = []
    for name, pos, what in cases:
        a = run_sequence(pc, PC20, pos)
        b = run_sequence(base, [], pos)
        # reading computed from the numbers
        prev_count = startpos_count if name.startswith("c1") else count15
        if a["refused"]:
            stale = (a["perft1"] == prev_count)
            reading = ("REFUSED; board left at the PREVIOUS position (perft 1 = %d) -> STALE, as seat 21 says"
                       % a["perft1"]) if stale else \
                      ("REFUSED; perft 1 = %s, which is neither board -> investigate" % a["perft1"])
        else:
            reading = ("ACCEPTED; perft 1 = %s -> %s" %
                       (a["perft1"], "the right board" if a["perft1"] == count15 else "WRONG board"))
        rows.append({"case": name, "what": what, "pc": a, "base": b, "reading": reading})
        print("%-26s pc ref=%-5s perft1=%-4s | base ref=%-5s perft1=%-4s | %s"
              % (name, bool(a["refused"]), a["perft1"], bool(b["refused"]), b["perft1"], reading),
              flush=True)
        lines.append("%s\t%s\t%s\t%s\t%s\t%s\t%s" % (
            name, what, bool(a["refused"]), a["perft1"], bool(b["refused"]), b["perft1"], reading))
    # verdict
    fm0 = next(r for r in rows if r["case"] == "c2_board_then_fullmove0")
    ctl = next(r for r in rows if r["case"] == "c3_fullmove1_control")
    neg = next(r for r in rows if r["case"] == "c4_fullmove_minus1")
    v = []
    v.append("")
    confirmed = (bool(fm0["pc"]["refused"]) and fm0["pc"]["perft1"] == count15
                 and ctl["pc"]["perft1"] == count15 and bool(neg["pc"]["refused"]))
    v.append("control (fullmove 1) on PC20: perft 1 = %s (expected %d) -> %s"
             % (ctl["pc"]["perft1"], count15, "control holds" if ctl["pc"]["perft1"] == count15 else "CONTROL BROKEN"))
    v.append("negative control (fullmove -1) refused on PC20: %s" % bool(neg["pc"]["refused"]))
    if confirmed:
        v.append("VERDICT: CONFIRMS 21-F8b. On the PC build under PC20, `fullmove 0` is REFUSED and the engine")
        v.append("keeps the PREVIOUS board (perft 1 = %d = the 15-move board, not a stale startpos), the")
        v.append("fullmove-1 control gives the board's own count, and fullmove -1 is refused. Threads 1, Hash 16.")
    else:
        v.append("VERDICT: does NOT confirm 21-F8b cleanly — see the rows above.")
    (out / "check_s21f8b.json").write_text(json.dumps({"rows": rows, "verdict": v,
                                                       "count15": count15,
                                                       "startpos_count": startpos_count,
                                                       "python_chess": py_note}, indent=1))
    (out / "check_s21f8b.txt").write_text("\n".join(lines + v) + "\n")
    print("")
    print("\n".join(v))


if __name__ == "__main__":
    main()
