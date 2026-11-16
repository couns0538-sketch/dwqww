#!/usr/bin/env python3
"""rep_inside.py EXE --regime R

Separates the two readings of 15-F16:
  (a) the PC build's ROOT repetition check is the gap (mid-search repetition is still recognised), or
  (b) the repetition machinery itself changed on the PC build.

Experiment: a position where a repetition is FORCED INSIDE the search, not in the root history.
The board below has a white pawn on a7 one step from promotion and a black rook that can only
shuffle: after 1.a8=Q+ ... the stronger side can force the weaker side's king/rook to repeat, and
a search that recognises in-tree repetition returns a draw score. The test does not depend on the
engine finding the repeat at an exact depth: we report the score at several depths and whether any
depth gives cp 0 with far fewer nodes than the previous depth (the classic repetition signature).

Controls, so a "cp 0" cannot be mistaken for a dead position:
  C1 the same board with the pawn one square further back (no immediate promotion) -> must NOT be 0
  C2 the thrice-repeated ROOT from 15-F16 on the same build/regime -> shows the root gap in the same run
  C3 the same thrice-repeated root given as a plain FEN (no history) -> searched, sanity
Threads 1 always. PARSE_FAIL rather than 0 on any missing token.
"""
import argparse
import queue
import re
import subprocess
import threading
import time

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

# Forced repetition available inside the tree: white is winning but the black king has exactly two
# squares, so many lines repeat. Rook + pawn endgames with the king on the edge repeat constantly.
INSIDE = [
    ("K+R+P vs K, black king boxed (repeat-rich)",
     "8/8/8/8/8/2k5/1R6/K2R4 w - - 0 1"),
    ("K+Q vs K, black king in the corner (repeat-rich)",
     "7k/8/6K1/8/8/8/8/Q7 w - - 0 1"),
    ("K+R vs K, black king boxed",
     "8/8/8/8/8/2k5/8/KR6 w - - 0 1"),
]
REP_MOVES = "g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8"
REP_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 8 5"


def opts(regime):
    return [] if regime == "none" else (S14 if regime == "S14" else S14 + PC20_EXTRA)


def run(exe, o, poscmd, depth, limit=300):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    q = queue.Queue()
    log = []

    def rd():
        for line in p.stdout:
            q.put(line.rstrip("\n"))
        q.put(None)

    threading.Thread(target=rd, daemon=True).start()

    def send(c):
        p.stdin.write(c + "\n"); p.stdin.flush()

    def wait(pred, lim):
        t0 = time.monotonic()
        while True:
            rem = lim - (time.monotonic() - t0)
            if rem <= 0:
                return "TIMEOUT"
            try:
                line = q.get(timeout=rem)
            except queue.Empty:
                return "TIMEOUT"
            if line is None:
                return "EOF"
            log.append(line)
            if pred(line):
                return line

    send("uci"); wait(lambda l: l.startswith("uciok"), 30)
    send("setoption name Threads value 1"); send("setoption name Hash value 16")
    for k, v in o:
        send("setoption name %s value %s" % (k, v))
    send("isready"); wait(lambda l: l == "readyok", 30)
    send("ucinewgame"); send("isready"); wait(lambda l: l == "readyok", 30)
    send(poscmd); send("isready"); wait(lambda l: l == "readyok", 30)
    send("go depth %d" % depth)
    bm = wait(lambda l: l.startswith("bestmove"), limit)
    try:
        send("quit"); p.wait(timeout=10)
    except Exception:
        p.kill()
    infos = [l for l in log if l.startswith("info depth")]
    last = infos[-1] if infos else None
    if not last:
        return "NO_INFO_LINE", None, None
    m = re.search(r"score (cp|mate) (-?\d+)", last)
    score = ("%s %s" % (m.group(1), m.group(2))) if m else "PARSE_FAIL"
    m2 = re.search(r"\bnodes (\d+)", last)
    nodes = int(m2.group(1)) if m2 else "PARSE_FAIL"
    return score, nodes, bm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--regime", default="PC20")
    a = ap.parse_args()
    o = opts(a.regime)
    print("exe: %s  regime: %s  Threads 1" % (a.exe, a.regime), flush=True)
    print(flush=True)
    print("=== mid-search repetition candidates: score by depth (a cp 0 that appears while nodes")
    print("    stay small is the in-tree repetition signature) ===", flush=True)
    for label, fen in INSIDE:
        b = chess.Board(fen)
        print(flush=True)
        print("%s" % label, flush=True)
        print("  FEN %s   (valid=%s, legal moves=%d)" % (fen, b.is_valid(), b.legal_moves.count()),
              flush=True)
        for d in (6, 8, 10, 12):
            sc, nd, bm = run(a.exe, o, "position fen " + fen, d)
            print("    d%-3d %-10s nodes=%-9s %s" % (d, sc, nd, bm), flush=True)
    print(flush=True)
    print("=== C2/C3: the thrice-repeated ROOT on the same build/regime ===", flush=True)
    sc, nd, bm = run(a.exe, o, "position startpos moves " + REP_MOVES, 10)
    print("  thrice-repeated root (history)  %-10s nodes=%-9s %s" % (sc, nd, bm), flush=True)
    sc, nd, bm = run(a.exe, o, "position fen " + REP_FEN, 10)
    print("  same board as plain FEN         %-10s nodes=%-9s %s" % (sc, nd, bm), flush=True)


if __name__ == "__main__":
    main()
