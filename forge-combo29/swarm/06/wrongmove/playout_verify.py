#!/usr/bin/env python3
"""Independent play-out check of the lone-king defect: GROUND TRUTH, scores ignored.

Both sides played BY THE ENGINE (depth 12, fresh process pool), python-chess adjudicating game end.
Score the survival length in plies for each of White's two candidate first moves. The engine's own
scores are never consulted, so this cannot be affected by the mate sign convention or by
searchmoves-vs-free-choice comparability - the two traps that produced the earlier false alarm.

usage: playout_verify.py EXE LABEL RUNS
"""
import subprocess
import sys

import chess

FEN = "1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183"
FIRST = ["c6d6", "c6c7"]
DEPTH = 12
S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]


def engine_move(exe, fen, depth=DEPTH):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def w(c):
        p.stdin.write(c + "\n"); p.stdin.flush()

    def r():
        l = p.stdout.readline()
        if l == "":
            raise RuntimeError("died")
        return l

    def rd():
        while True:
            if r().strip() == "readyok":
                return

    w("uci")
    while r().strip() != "uciok":
        pass
    for n, v in [("Threads", "1"), ("Hash", "16"), ("OwnBook", "false")] + S14:
        w("setoption name %s value %s" % (n, v)); w("isready"); rd()
    w("ucinewgame"); w("isready"); rd()
    w("position fen " + fen); w("isready"); rd()
    w("go depth %d" % depth)
    bm = None
    while True:
        l = r().strip()
        if l.startswith("bestmove"):
            bm = l.split()[1]; break
    p.kill()
    return bm


def survival(exe, first, max_plies=200):
    b = chess.Board(FEN)
    b.push_uci(first)
    plies = 1
    while plies < max_plies:
        if b.is_game_over(claim_draw=False):
            break
        bm = engine_move(exe, b.fen())
        if bm is None or bm == "0000":
            break
        try:
            mv = chess.Move.from_uci(bm)
        except Exception:
            break
        if mv not in b.legal_moves:
            break
        b.push(mv)
        plies += 1
    return plies, ("checkmate" if b.is_checkmate() else ("stalemate" if b.is_stalemate() else
                    ("draw_claim" if b.can_claim_draw() else "cap")))


def main():
    exe, label, runs = sys.argv[1], sys.argv[2], int(sys.argv[3])
    print("PLAY-OUT GROUND TRUTH — %s" % label)
    print("FEN: " + FEN)
    print("Both sides played by the engine at depth %d; python-chess adjudicates. Scores never consulted." % DEPTH)
    print("")
    print("| first move for White | run | plies survived | end |")
    print("|---|---|---|---|")
    summary = {}
    for first in FIRST:
        tot = []
        for i in range(runs):
            pl, how = survival(exe, first)
            tot.append(pl)
            print("| %s | %d | %d | %s |" % (first, i + 1, pl, how))
        summary[first] = tot
    print("")
    for first in FIRST:
        t = summary[first]
        print("%s: plies %s  -> best %d, median %d" % (first, t, max(t), sorted(t)[len(t) // 2]))
    d = summary["c6d6"]
    c = summary["c6c7"]
    if min(d) > max(c):
        print("")
        print("VERDICT: c6d6 survives strictly longer than c6c7 in every run "
              "(min %d vs max %d). The engine's preference for c6c7 is WRONG by ground truth, "
              "regardless of any score." % (min(d), max(c)))
    else:
        print("")
        print("VERDICT: the two moves overlap in survival length on this sample; no ground-truth "
              "ordering established at %d runs." % runs)


if __name__ == "__main__":
    main()
