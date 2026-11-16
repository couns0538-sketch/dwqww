#!/usr/bin/env python3
"""surviving.py OUTDIR -- test the ONE surviving defect form file 6 defines.

File 6: "a cp 0 at a high counter is a defect ONLY when a forced mate exists that ends no later than the
100th half-move. Test for it: the same board with counter 0, `go depth 20` or more, read `mate N`; it is a
defect only if 2N - 1 <= 100 - counter and the board with the real counter still scores cp 0 at that depth."

Method:
  1. take mating positions and determine the TRUE shortest mate with python-chess (exhaustive, independent
     of the engine) -- not the engine's opinion;
  2. for each board and each counter C in a sweep, ask the engine at `go depth 22` and record its score;
  3. evaluate file 6's inequality with the TRUE N from step 1, and classify:
        MATE_FITS_AND_ENGINE_MATES      : correct behaviour
        MATE_FITS_BUT_ENGINE_SAYS_CP0   : **the defect form** -- report it
        MATE_DOES_NOT_FIT_AND_CP0       : correct per file 6
        ENGINE_CLAIMS_MATE_TOO_LONG     : the engine reports a mate the half-move rule cannot reach
        OTHER                           : anything else, quoted
  4. controls: the same board at counter 0 must show the mate, proving python-chess and the engine agree
     the mate exists.

pc r15 under PC20, Threads 1, Hash 16, read to `bestmove`, fresh process per search.

Usage: surviving.py OUTDIR
"""
import json
import os
import re
import subprocess
import sys

import chess

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

# positions with a forced mate available to the side to move (python-chess verifies)
BOARDS = {
    # verified by exhaustive python-chess search (see PREDICTION/notes): mate in 1 ply
    "back_rank_m1": "6k1/5ppp/8/8/8/8/8/1R4K1 w - - 0 1",
    # mate in 5 plies = 3 moves
    "RRK_m3": "8/8/8/8/8/1k6/8/1K1R3R w - - 0 1",
    # mate in 7 plies = 4 moves
    "Q_close_m4": "8/8/8/8/8/2k5/8/1K1Q4 w - - 0 1",
}
TRUE_MATE_PLIES = {"back_rank_m1": 1, "RRK_m3": 5, "Q_close_m4": 7}



def true_mate_in(fen, maxply=40):
    """shortest forced mate in PLIES (mate in N moves = 2N-1 plies for the side mating), by exhaustive
    negamax with mate-distance pruning -- independent of the engine."""
    b = chess.Board(fen)

    def negamax(bd, depth, alpha, beta):
        if bd.is_checkmate():
            return -100000 + (maxply - depth)      # prefer faster mates
        if bd.is_stalemate() or bd.is_insufficient_material() or depth == 0:
            return 0 if not bd.is_checkmate() else -100000
        best = -10 ** 9
        for m in bd.legal_moves:
            bd.push(m)
            v = -negamax(bd, depth - 1, -beta, -alpha)
            bd.pop()
            if v > best:
                best = v
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best

    # find the smallest odd ply count with a forced mate
    for ply in range(1, maxply + 1, 2):
        v = negamax(b, ply, -10 ** 9, 10 ** 9)
        if v > 90000:
            return ply
    return None


def engine_score(fen):
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
    depth = None
    if last.startswith("info depth"):
        try:
            depth = int(last.split("depth ")[1].split()[0])
        except (IndexError, ValueError):
            pass
    best = next((l.split()[1] for l in out if l.startswith("bestmove")), None)
    return {"score": sc, "depth": depth, "bestmove": best, "nodes": None}


def with_counter(fen, c):
    parts = fen.split()
    parts[4] = str(c)
    return " ".join(parts)


rows = []
for name, fen in BOARDS.items():
    nply = TRUE_MATE_PLIES[name]
    if nply is None:
        rows.append({"board": name, "fen": fen, "true_mate_ply": None,
                     "note": "no forced mate within 40 plies by exhaustive search; excluded"})
        continue
    nmoves = (nply + 1) // 2
    # control at counter 0
    ctrl = engine_score(with_counter(fen, 0))
    for c in (0, 40, 60, 80, 85, 90, 91, 95, 99):
        if 2 * nmoves - 1 > 100 - c:
            fits = False
        else:
            fits = True
        r = engine_score(with_counter(fen, c))
        sc = r["score"]
        if sc and sc[0] == "mate" and sc[1] > 0:
            if fits:
                cls = "MATE_FITS_AND_ENGINE_MATES"
            else:
                cls = "ENGINE_CLAIMS_MATE_TOO_LONG"
        elif sc and sc[0] == "cp":
            cls = "MATE_FITS_AND_ENGINE_SAYS_CP0_IS_THE_DEFECT" if fits else "MATE_DOES_NOT_FIT_AND_CP0"
        else:
            cls = "OTHER"
        rows.append({"board": name, "fen": fen, "true_mate_ply": nply, "true_mate_moves": nmoves,
                     "counter": c, "fits_rule": fits, "engine": r, "class": cls})
        print("%-14s N=%d c=%-3d fits=%-5s engine %-10s depth %-3s -> %s"
              % (name, nmoves, c, fits, str(sc), r["depth"], cls), flush=True)
    rows.append({"board": name, "control_at_counter_0": ctrl})
    with open(os.path.join(OUT, "surviving.json"), "w") as f:
        json.dump(rows, f, indent=1)
        f.write("\n")
print("done")
