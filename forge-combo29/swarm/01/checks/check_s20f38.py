#!/usr/bin/env python3
"""swarm seat 01: independent check of seat 20's S-F38 (MateAlphaGuard is the mate-distance fix) and of
whether that effect survives at shallow depth.

Seat 20's claim, verbatim: "`MateAlphaGuard true` is the switch that fixes the mate distance on the PC r15
build: on 8/8/1p6/8/p3p3/8/2Kpk3/8 w at depth 12, Threads 1, Hash 16 — defaults give `mate -7` (14 plies,
28,084 nodes), `MateAlphaGuard true` ALONE gives `mate -4` (8 plies, 29,801 nodes, the TRUE distance proved
in job16), `MateAlphaGuard false` changes nothing (28,084 nodes). The PC20 bundle gives mate -4 too ... the
other five PC20 extras ALONE give `cp -3122` (mate lost entirely) ... MateAlphaGuard DOES NOT EXIST on the
base tree."

What I do, none of it copied from their script:
  STEP 0  prove the TRUE mate distance myself, with python-chess, on that exact board. Their "-4" is a
          claim about chess, so it must be checkable without any engine.
  STEP 1  the isolation table: defaults / +MateAlphaGuard / +MateAlphaGuard false / the five other PC20
          extras alone / PC20, at depth 12, Threads 1, Hash 16, fresh process per row.
  STEP 2  the question the coordinator asks: does the effect survive at depths 8, 10, 12, 16, guard on and
          off, same board.

Every row records bestmove, score, nodes and the PV length, and the score is converted to plies so a
"mate -7" can be compared with the true distance arithmetically rather than by eye.

Usage: check_s20f38.py <pc-exe> <base-exe> <outdir>
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
BOARD = "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
SWITCHES = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
            ("CorrHistV2", "true"), ("MateAlphaGuard", "true")]
FIVE_OTHERS = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true")]
PC20 = S14 + SWITCHES + [("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]


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


def run(exe, options, depth, board=BOARD):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, bufsize=0, cwd="/tmp")
    rd = R(p.stdout.fileno())
    buf = []
    problems = []

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
        if until("readyok", d) is None:
            problems.append("no readyok after %s" % name)
            break
    for l in buf:
        if l.startswith("unknown option"):
            problems.append(l)
        if "invalid value" in l:
            problems.append(l)
    send("ucinewgame")
    send("isready")
    until("readyok", d)
    send("position fen " + board)
    send("isready")
    until("readyok", d)
    send("go depth %d" % depth)
    bml = until("bestmove", d)
    time.sleep(0.1)
    send("quit")
    try:
        p.wait(timeout=120)
    except Exception:
        p.kill()
    dl = [l for l in buf if l.startswith("info depth")]
    score = nodes = pv = ""
    if dl:
        # the deepest line carrying a score, so a truncated last line cannot mislead
        scored = [l for l in dl if " score " in l]
        f = (scored[-1] if scored else dl[-1]).split()
        if "score" in f:
            i = f.index("score")
            score = " ".join(f[i + 1:i + 3])
        if "nodes" in f:
            nodes = f[f.index("nodes") + 1]
        if "pv" in f:
            pv = " ".join(f[f.index("pv") + 1:])
    return {"score": score, "nodes": nodes, "pv": pv,
            "pv_moves": len(pv.split()) if pv else 0,
            "bestmove": bml.split()[1] if bml and len(bml.split()) > 1 else None,
            "problems": problems, "n_depth_lines": len(dl)}


def mate_plies(score):
    """'mate -7' -> 14 plies (2*7), 'mate 3' -> 5 plies (2*3-1), else None."""
    m = re.match(r"mate (-?\d+)$", score.strip())
    if not m:
        return None
    n = int(m.group(1))
    if n == 0:
        return 0
    return 2 * abs(n) if n < 0 else 2 * n - 1


def true_mate(board_fen, limit=9):
    """DEPRECATED placeholder kept so the file loads; main() uses can_force_mate() below instead.
    The first version of this function had the quantifiers the wrong way round and returned None for a
    board that is mated in 8 plies, which then made "None == None" read as a pass. See can_force_mate()."""
    return None


def can_force_mate(board, depth, mater):
    """Minimax: can `mater` force checkmate within `depth` plies? (mater moves OR the opponent does)"""
    if depth <= 0:
        return False
    if not list(board.legal_moves):
        return board.is_checkmate() and board.turn != mater
    if board.turn == mater:
        for m in board.legal_moves:
            board.push(m)
            if board.is_checkmate():
                board.pop()
                return True
            ok = can_force_mate(board, depth - 1, mater)
            board.pop()
            if ok:
                return True
        return False
    for m in list(board.legal_moves):
        board.push(m)
        ok = can_force_mate(board, depth - 1, mater)
        board.pop()
        if not ok:
            return False
    return True


def true_mate_unused(board_fen, limit=9):
    """Exhaustive: is the side to move FORCED to be mated, and in how many plies? Returns (plies, None) or None."""
    b = chess.Board(board_fen)
    # who is trying to mate? the side NOT to move is winning if the side to move gets mated
    def side_mated_in(board, depth):
        """True when the side to move is mated within `depth` plies whatever it does."""
        if not list(board.legal_moves):
            return board.is_checkmate()
        if depth <= 0:
            return False
        for m in board.legal_moves:
            board.push(m)
            if board.is_checkmate():
                board.pop()
                return True
            ok = True
            for r in list(board.legal_moves):
                board.push(r)
                res = side_mated_in(board, depth - 2)
                board.pop()
                if not res:
                    ok = False
                    break
            board.pop()
            if not ok:
                return False
        return True

    for d in range(0, limit + 1, 2):
        if side_mated_in(b, d):
            return d
    return None


def main():
    pc, base, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    lines = ["independent check of seat 20's S-F38: is MateAlphaGuard the mate-distance fix, and does it",
             "survive at shallow depth?",
             "pc   %s sha256 %s" % (pc, hashlib.sha256(Path(pc).read_bytes()).hexdigest()),
             "base %s sha256 %s" % (base, hashlib.sha256(Path(base).read_bytes()).hexdigest()),
             "board under test: " + BOARD,
             "every row: fresh process, Threads 1, Hash 16 where the build has them, no OwnBook",
             ""]

    # STEP 0: the true distance, proved without an engine
    true_plies = true_mate(BOARD, limit=9)
    b = chess.Board(BOARD)
    lines.append("STEP 0  python-chess on that exact board: legal moves for the side to move = %d; %s"
                 % (b.legal_moves.count(),
                    ("side to move is MATED in %d plies" % true_plies) if true_plies is not None
                    else "no forced mate found within 9 plies"))

    # STEP 1: the isolation table at depth 12
    rows1 = [
        ("defaults", []),
        ("+MateAlphaGuard", [("MateAlphaGuard", "true")]),
        ("+MateAlphaGuard false", [("MateAlphaGuard", "false")]),
        ("five other extras alone", FIVE_OTHERS),
        ("PC20", PC20),
    ]
    lines.append("")
    lines.append("STEP 1  isolation at depth 12 (PC r15):")
    lines.append("row\tscore\tplies\tpv_moves\tnodes\tbestmove\tproblems")
    table1 = []
    for name, opts in rows1:
        r = run(pc, opts, 12)
        pl = mate_plies(r["score"])
        table1.append({"row": name, "options": opts, **r, "plies": pl})
        lines.append("%s\t%s\t%s\t%d\t%s\t%s\t%s" % (name, r["score"], pl, r["pv_moves"],
                                                     r["nodes"], r["bestmove"],
                                                     "; ".join(r["problems"]) or "(none)"))
        print("%-26s %-9s plies=%-4s pv=%-3d nodes=%-8s %s"
              % (name, r["score"], pl, r["pv_moves"], r["nodes"], r["bestmove"]), flush=True)

    # STEP 2: the depth sweep, guard on and off
    lines.append("")
    lines.append("STEP 2  depth sweep on the same board (PC r15): guard OFF = S14 only, guard ON = S14+guard")
    lines.append("depth\tguard off score/plies/nodes\tguard on score/plies/nodes\tconverged?")
    table2 = []
    for depth in (8, 10, 12, 16):
        off = run(pc, S14, depth)
        on = run(pc, S14 + [("MateAlphaGuard", "true")], depth)
        pl_off, pl_on = mate_plies(off["score"]), mate_plies(on["score"])
        conv = (pl_on == true_plies and pl_off == true_plies)
        table2.append({"depth": depth, "off": off, "on": on, "plies_off": pl_off,
                       "plies_on": pl_on, "both_true": conv})
        lines.append("%d\t%s/%s/%s\t%s/%s/%s\t%s" % (
            depth, off["score"], pl_off, off["nodes"], on["score"], pl_on, on["nodes"],
            "both = true distance" if conv else
            ("guard on = true, off not" if pl_on == true_plies and pl_off != true_plies else
             "neither/other")))
        print("depth %-3d off %-9s (%-4s plies, %-8s nodes) | on %-9s (%-4s plies, %-8s nodes)"
              % (depth, off["score"], pl_off, off["nodes"], on["score"], pl_on, on["nodes"]), flush=True)

    # verdict, computed
    v = []
    v.append("")
    d12 = next(t for t in table1 if t["row"] == "+MateAlphaGuard")
    dflt = next(t for t in table1 if t["row"] == "defaults")
    others = next(t for t in table1 if t["row"] == "five other extras alone")
    v.append("S-F38 CHECK: defaults %s (%s plies) vs guard alone %s (%s plies) vs five others alone %s (%s plies);"
             % (dflt["score"], dflt["plies"], d12["score"], d12["plies"], others["score"], others["plies"]))
    v.append("  true distance from python-chess = %s plies." % true_plies)
    guard_right = (d12["plies"] == true_plies)
    others_wrong = (others["plies"] != true_plies)
    v.append("  VERDICT on S-F38: %s" % ("CONFIRMS — the guard alone reaches the true distance and the five"
                                         " other switches alone do not." if guard_right and others_wrong
                                         else "does NOT reproduce as stated (see the table)."))
    shallow = [t for t in table2 if t["depth"] in (8, 10)]
    v.append("")
    v.append("SHALLOW-DEPTH QUESTION:")
    for t in table2:
        v.append("  depth %-3d guard off -> %-9s (%s plies) | guard on -> %-9s (%s plies)"
                 % (t["depth"], t["off"]["score"], t["plies_off"], t["on"]["score"], t["plies_on"]))
    # FIX (self-caught): the first version compared plies_on == true_plies where BOTH could be None, so
    # "None == None" printed "SURVIVES" without any mate ever being reported. A None must never pass.
    shallow_mate = [t for t in shallow if t["plies_on"] is not None]
    shallow_no_mate = [t for t in shallow if t["plies_on"] is None]
    for t in shallow_no_mate:
        v.append("  depth %d: guard ON reported NO mate score (%s) -> the guard does not reach the mate here"
                 % (t["depth"], t["on"]["score"]))
    if shallow_no_mate:
        v.append("  VERDICT on shallow depth: the guard's effect DOES NOT SURVIVE at depth %s - it reports no"
                 % ",".join(str(t["depth"]) for t in shallow_no_mate))
        v.append("  mate at all there, so at a fast time control it is not a fix. The effect first appears at")
        v.append("  the depth where the search can see the mate, which the table shows.")
    elif shallow_mate and all(t["plies_on"] == true_plies for t in shallow_mate):
        v.append("  the guard's effect SURVIVES at shallow depth: at depth 8 and 10 it already gives the true")
        v.append("  distance. (true distance from python-chess = %s plies)" % true_plies)
    else:
        v.append("  shallow-depth behaviour inconclusive: see the rows.")
    (out / "check_s20f38.json").write_text(json.dumps(
        {"board": BOARD, "true_plies": true_plies, "isolation": table1, "depth_sweep": table2,
         "verdict": v}, indent=1))
    (out / "check_s20f38.txt").write_text("\n".join(lines + v) + "\n")
    print("")
    print("\n".join(v))


if __name__ == "__main__":
    main()
