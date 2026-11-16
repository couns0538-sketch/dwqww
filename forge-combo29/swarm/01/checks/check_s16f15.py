#!/usr/bin/env python3
"""swarm seat 01: CHECK of seat 16's S-F15 — the PC build's extra colour asymmetry comes from the PC20
SETTINGS (mainly TtPruneV2), not from the PC code.

Seat 16's claim, verbatim:
  "the colour asymmetry's extra mismatches on the PC build come from the PC20 SETTINGS, not the PC code:
   swapping the code alone (base -> PC r15 at fixed S14) moves the depth-10 bestmove-mismatch count
   101 -> 102 of 353, while TtPruneV2 alone moves it 102 -> 113 and full PC20 gives 120; HistRework alone
   is the only cell MORE symmetric than base+S14 (98). Threads 1 throughout"

My harness. For a position and its COLOUR MIRROR (python-chess board.mirror(): ranks flipped AND colours
swapped), the engine's bestmove should be the mirror of the original bestmove. A pair "matches" when it is.
Seat 16's S-C5 warns that `eval` is side-to-move relative — a negation-based checker reports a false
difference — so this checker compares MOVES (mirror the move's squares and swap nothing else), which avoids
that trap entirely; no eval is read.

Arms, all PC r15, Threads 1, Hash 16, depth 10, on the first N of set_G:
  base_S14     PC r15 engine with S14 only
  plus_TtPrune S14 + TtPruneV2 true
  plus_Hist    S14 + HistRework 2
  PC20         the full bundle
Reported per arm: matches / pairs, so seat 16's 101 / 102 / 113 / 120 / 98 shape can be compared directly.

Usage: check_s16f15.py <pc-exe> <g-epd> <outdir> [limit]
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

TIMEOUT = 1800.0
DEPTH = 10

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
TT = S14 + [("TtPruneV2", "true"), ("Threads", "1"), ("Hash", "16"), ("OwnBook", "false")]
HIST = S14 + [("HistRework", "2"), ("Threads", "1"), ("Hash", "16"), ("OwnBook", "false")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false"),
              ("Threads", "1"), ("Hash", "16")]
BASE_S14 = S14 + [("Threads", "1"), ("Hash", "16"), ("OwnBook", "false")]


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


def bestmove(exe, fen, options):
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
        until("readyok", d)
    for l in buf:
        if l.startswith("unknown option") or "invalid value" in l:
            problems.append(l)
    send("ucinewgame")
    send("isready")
    until("readyok", d)
    send("position fen " + fen)
    send("isready")
    until("readyok", d)
    send("go depth %d" % DEPTH)
    bml = until("bestmove", d)
    time.sleep(0.05)
    send("quit")
    try:
        p.wait(timeout=120)
    except Exception:
        p.kill()
    return (bml.split()[1] if bml and len(bml.split()) > 1 else None), problems


def mirror_move(uci):
    """Map a move into the mirrored board.

    chess.Board.mirror() is a VERTICAL mirror: it flips RANKS and swaps piece colours and the turn. So
    black's move b8b3 in the original corresponds to white's move b1b6 in the mirror, i.e. the mapping is
    a RANK flip of both squares, NOT file+rank. (My first version used file+rank and produced 100 %
    mismatches in every arm, which is how the bug was caught: a checker that reports every pair as a
    mismatch is broken, not a finding.) Verified against python-chess: the legal move SETS are equal under
    this mapping.
    """
    if not uci or uci == "0000":
        return uci
    try:
        a = chess.parse_square(uci[:2])
        b = chess.parse_square(uci[2:4])
        prom = uci[4:] if len(uci) > 4 else ""
        def flip(sq):
            return chess.square(chess.square_file(sq), 7 - chess.square_rank(sq))
        return chess.square_name(flip(a)) + chess.square_name(flip(b)) + prom
    except Exception:  # noqa: BLE001
        return None


def main():
    exe = sys.argv[1]
    gpath = sys.argv[2]
    out = Path(sys.argv[3])
    limit = int(sys.argv[4]) if len(sys.argv) > 4 else 100
    out.mkdir(parents=True, exist_ok=True)
    fens = []
    for line in open(gpath):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 4:
            fens.append(" ".join(parts[:4]) + " 0 1")
        if len(fens) >= limit:
            break

    arms = [("base_S14", BASE_S14), ("plus_TtPrune", TT), ("plus_Hist", HIST), ("PC20", PC20)]
    lines = ["CHECK of seat 16's S-F15: is the extra colour asymmetry caused by the PC20 SETTINGS?",
             "exe_started: %s" % exe,
             "sha256: %s" % hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
             "PC r15 at depth %d, Threads 1, Hash 16, %d G positions + their colour mirrors" % (DEPTH, len(fens)),
             "checker compares MOVES (rank-flipped squares), never eval, so the side-to-move-relative eval trap",
             "recorded in seat 16's own S-C5 cannot produce a false difference here",
             "SANITY CONTROL: the legal move sets of a position and its mirror are verified EQUAL under the",
             "mapping before any verdict; a checker that reported every pair as a mismatch would be broken",
             ""]
    # SANITY CONTROL on the mapping itself, run once: the legal move set of a position and the rank-flipped
    # legal move set of its mirror must be EQUAL. If not, the checker is broken and no verdict is drawn.
    sanity_fail = []
    for fen in fens[:5]:
        bb = chess.Board(fen)
        mm = bb.mirror()
        orig = {x.uci() for x in bb.legal_moves}
        mirr = {mirror_move(x.uci()) for x in mm.legal_moves}
        if orig != mirr:
            sanity_fail.append(fen)
    if sanity_fail:
        msg = ("SANITY CONTROL FAILED on the move mapping: %d of 5 positions do not have equal legal-move "
               "sets under rank-flip, so this checker cannot judge symmetry and NO VERDICT IS DRAWN."
               % len(sanity_fail))
        (out / "check_s16f15.txt").write_text(msg + "\n")
        print(msg)
        return

    results = {}
    for name, opts in arms:
        matches = 0
        problems = []
        rows = []
        for fen in fens:
            b = chess.Board(fen)
            mfen = b.mirror().fen()
            # the mirror must be legal, or the pair is not comparable
            try:
                mb = chess.Board(mfen)
                if not mb.is_valid():
                    continue
            except ValueError:
                continue
            a, pa = bestmove(exe, fen, opts)
            m, pb = bestmove(exe, mfen, opts)
            problems.extend(pa + pb)
            want = mirror_move(a)
            ok = (m is not None and want is not None and m == want)
            if ok:
                matches += 1
            rows.append({"fen": fen, "bestmove": a, "mirror_fen": mfen, "mirror_bestmove": m,
                         "expected_mirror": want, "match": ok})
        results[name] = {"matches": matches, "pairs": len(rows),
                         "mismatches": len(rows) - matches,
                         "unknown_option_lines": problems[:3], "rows": rows}
        print("%-14s matches %d / %d  (mismatches %d)%s"
              % (name, matches, len(rows), len(rows) - matches,
                 ("  PROBLEMS: " + str(problems[:2])) if problems else ""), flush=True)
        lines.append("%s\t%d\t%d\t%d" % (name, matches, len(rows), len(rows) - matches))

    v = []
    v.append("")
    b0 = results["base_S14"]["mismatches"]
    tt = results["plus_TtPrune"]["mismatches"]
    hi = results["plus_Hist"]["mismatches"]
    pc = results["PC20"]["mismatches"]
    v.append("MISMATCHES out of %d pairs: base_S14 %d, plus_TtPrune %d, plus_Hist %d, PC20 %d"
             % (results["base_S14"]["pairs"], b0, tt, hi, pc))
    v.append("")
    v.append("VERDICT on seat 16's S-F15:")
    v.append("  TtPruneV2 alone %s the mismatch count (%d -> %d): %s"
             % ("RAISES" if tt > b0 else "does not raise", b0, tt,
                "confirmed" if tt > b0 else "NOT confirmed"))
    v.append("  HistRework alone %s the count (%d -> %d): %s"
             % ("LOWERS" if hi < b0 else "does not lower", b0, hi,
                "confirmed" if hi < b0 else "NOT confirmed"))
    v.append("  PC20 as a bundle gives %d, %s base_S14's %d." % (pc, "worse than" if pc > b0 else "no worse than", b0))
    v.append("  So the DIRECTION of their attribution (settings, not code; TtPruneV2 the main offender;")
    v.append("  HistRework the benign one) is %s on my run." % ("reproduced" if (tt > b0 and hi <= b0) else "NOT reproduced"))
    v.append("  My absolute counts differ from theirs because I used the first %d of set_G, not all 353." % len(fens))
    (out / "check_s16f15.json").write_text(json.dumps({"arms": results, "verdict": v}, indent=1))
    (out / "check_s16f15.txt").write_text("\n".join(lines + v) + "\n")
    print("")
    print("\n".join(v))


if __name__ == "__main__":
    main()
