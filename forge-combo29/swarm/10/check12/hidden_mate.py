#!/usr/bin/env python3
"""hidden_mate.py OUTDIR -- the widening my own scope note (10-N3) named: a mate that HIDES BEHIND A LONG
NON-MATING LINE, at a counter where file 6's inequality BARELY holds.

Boards, each with its shortest forced mate established by `mate_solver.py` (python-chess, transposition
table, independent of the engine):
  KQ_far   8/8/8/8/3k4/8/8/1K1Q4   mate in 13 plies = 7 moves   <- the hidden one: the king is far away,
                                                                 many quiet queen moves exist
  KQ_edge  8/8/8/8/8/1k6/8/1K2Q3   mate in 9 plies  = 5 moves
  KQ_near  8/8/8/8/8/2k5/8/1K1Q4   mate in 7 plies  = 4 moves
For each, the counter is chosen so file 6's inequality 2N-1 <= 100-counter holds by a THIN margin
(1, 3 and 5 half-moves of slack), plus the exact boundary and one past it.

Recorded per (board, counter): the engine's score at `go depth 22`, its reported mate distance, and the
classification. A cp 0 on a board where the inequality holds is THE DEFECT; a mate where it does not hold is
also a defect (claiming an unreachable mate).

PC r15 under PC20, Threads 1, Hash 16, fresh process per search, read to `bestmove`.

Usage: hidden_mate.py OUTDIR
"""
import json
import os
import re
import subprocess
import sys

PC = os.path.expanduser("~/builds/pc/forge")
OUT = os.path.abspath(sys.argv[1])
os.makedirs(OUT, exist_ok=True)
DEPTH = 22

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

# (fen, true mate in PLIES from mate_solver.py)
BOARDS = {
    "KQ_far_m7": ("5k2/8/8/8/8/8/8/1K1Q4 w - - 0 1", 13),
    "KQ_far2_m7": ("6k1/8/8/8/8/8/8/1K1Q4 w - - 0 1", 13),
}
# slack in half-moves: the counter is set so (100-counter) - (2N-1) equals this
SLACKS = [7, 5, 3, 1, 0, -1]


def with_counter(fen, c):
    p = fen.split()
    p[4] = str(c)
    return " ".join(p)


def engine(fen):
    lines = ["uci", "isready", "setoption name Threads value 1", "setoption name Hash value 16"]
    lines += ["setoption name %s value %s" % kv for kv in PC20]
    lines += ["isready", "ucinewgame", "isready", "position fen " + fen, "isready",
              "go depth %d" % DEPTH]
    p = subprocess.Popen([PC], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    for l in lines:
        p.stdin.write(l + "\n")
        p.stdin.flush()
    out = []
    while True:
        line = p.stdout.readline()
        if not line:
            break
        out.append(line.rstrip())
        if line.startswith("bestmove"):
            break
    p.stdin.write("quit\n")
    try:
        p.stdin.flush()
    except Exception:
        pass
    try:
        p.wait(timeout=300)
    except Exception:
        p.kill()
    last = [l for l in out if l.startswith("info depth")]
    last = last[-1] if last else ""
    sc = None
    m = re.search(r" score (cp|mate) (-?\d+)", last)
    if m:
        sc = (m.group(1), int(m.group(2)))
    d = None
    if last.startswith("info depth"):
        try:
            d = int(last.split("depth ")[1].split()[0])
        except (IndexError, ValueError):
            pass
    nodes = None
    if " nodes " in last:
        try:
            nodes = int(last.split(" nodes ")[1].split()[0])
        except (IndexError, ValueError):
            pass
    refused = any("invalid FEN" in l for l in out)
    return {"score": sc, "depth": d, "nodes": nodes, "refused": refused,
            "bestmove": next((l.split()[1] for l in out if l.startswith("bestmove")), None)}


import chess as _chess


def assert_legal(fen):
    """A constructed FEN is only usable if python-chess calls it valid AND the engine does not refuse it.
    An illegal FEN makes the engine keep the PREVIOUS position (startpos), and every reading after that is
    about startpos, not about the board under test. This check exists because exactly that happened."""
    b = _chess.Board(fen)
    if not b.is_valid():
        raise SystemExit("REFUSING to test an invalid FEN: " + fen + " status=" + str(b.status()))
    if b.is_checkmate() or b.is_stalemate():
        raise SystemExit("REFUSING to test a terminal FEN: " + fen)
    return True


rows = []
for name, (fen, nply) in BOARDS.items():
    nmoves = (nply + 1) // 2
    for slack in SLACKS:
        # 2N-1 <= 100-c  ->  c <= 100-(2N-1);  slack = (100-c) - (2N-1)
        c = 100 - nply - slack
        if c < 0 or c > 100:
            continue
        target = with_counter(fen, c)
        assert_legal(target)
        r = engine(target)
        # the engine must NOT have refused this FEN: an info string invalid FEN means the search was on
        # the previous position and the row is meaningless
        if r.get("refused"):
            raise SystemExit("engine refused " + target + " -- row discarded")
        fits = (2 * nmoves - 1) <= (100 - c)
        sc = r["score"]
        report_mate = sc[0] == "mate" and sc[1] > 0 if sc else False
        if fits and report_mate:
            cls = "MATE_FOUND_CORRECT"
        elif fits and sc and sc[0] == "cp":
            cls = "DEFECT_cp0_where_mate_fits"
        elif (not fits) and sc and sc[0] == "cp":
            cls = "CP0_CORRECT_per_file6"
        elif (not fits) and report_mate:
            cls = "DEFECT_claims_unreachable_mate"
        else:
            cls = "OTHER"
        row = {"board": name, "fen": target, "true_mate_plies": nply,
               "true_mate_moves": nmoves, "counter": c, "slack_halfmoves": slack,
               "fits": fits, "engine": r, "class": cls}
        rows.append(row)
        print("%-11s N=%d c=%-3d slack=%+3d fits=%-5s engine %-10s depth %-3s -> %s"
              % (name, nmoves, c, slack, fits, str(sc), r["depth"], cls), flush=True)
        with open(os.path.join(OUT, "hidden_mate.json"), "w") as f:
            json.dump(rows, f, indent=1)
            f.write("\n")

defects = [r for r in rows if r["class"].startswith("DEFECT")]
summary = {"boards": len(BOARDS), "searches": len(rows),
           "defects": len(defects),
           "classes": {k: sum(1 for r in rows if r["class"] == k)
                       for k in sorted({r["class"] for r in rows})},
           "defect_rows": defects}
with open(os.path.join(OUT, "hidden_mate_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)
    f.write("\n")
print(json.dumps(summary, indent=2))
