#!/usr/bin/env python3
"""fiftythread.py EXE --regime none|S14|PC20 [--label L]

The four cases of the drawn-root / fifty-move thread, run on one build in one regime.
Every case in a fresh process; stdout read until bestmove; ABSENT reported distinctly from 0.
A case whose engine line cannot be parsed is reported PARSE_FAIL, never 0.

Case 1  mate in one at halfmove 99        board 6k1/5ppp/8/8/8/8/8/R5K1 w - - 99 1   -> expect mate 1 / a1a8
Case 2  mate in one at halfmove 100       same board, counter 100                     -> BASE TREE FAULT: cp 0, 0 nodes
Case 3  threefold-repetition root         position startpos moves g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8
                                                                                       -> expect cp 0
Case 4  counter-resetting pawn-move mate  a board where the mating move is a PAWN move, counter 100
                                                                                       -> expect the mate to be found
"""
import argparse
import queue
import re
import subprocess
import threading
import time

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

# Case 1/2: black king g8 with f7/g7/h7 pawns, white rook a1, white king g1 -> Ra8#.
MATE1 = "6k1/5ppp/8/8/8/8/8/R5K1 w - - {} 1"
# Case 4: white pawn on b7, black king a7 ... the mating move is b7b8=Q ; counter 100.
# Board: black king h8 boxed by white king f7 and white pawn g7; white pawn b7 can go b8=Q#? build it
# so the ONLY mate is a pawn move, which resets the counter.
MATE_PAWN = "8/P7/k7/P7/2K5/8/7Q/8 w - - {} 1"   # the only mate is the PAWN move a7a8=Q#

REP_MOVES = "g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8"


def opts_for(regime):
    if regime == "none":
        return []
    if regime == "S14":
        return S14
    return S14 + PC20_EXTRA


def run(exe, opts, position_cmd, go="depth 8", limit=120):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    q = queue.Queue()
    log = []

    def reader():
        for line in p.stdout:
            q.put(line.rstrip("\n"))
        q.put(None)

    threading.Thread(target=reader, daemon=True).start()

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

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
    for k, v in opts:
        send("setoption name %s value %s" % (k, v))
    send("isready"); wait(lambda l: l == "readyok", 30)
    send("ucinewgame"); send("isready"); wait(lambda l: l == "readyok", 30)
    send(position_cmd); send("isready"); wait(lambda l: l == "readyok", 30)
    send("go " + go)
    bm = wait(lambda l: l.startswith("bestmove"), limit)
    try:
        send("quit"); p.wait(timeout=10)
    except Exception:
        p.kill()
    infos = [l for l in log if l.startswith("info depth")]
    last = infos[-1] if infos else None
    score = nodes = None
    if last:
        m = re.search(r"score (cp|mate) (-?\d+)", last)
        score = "%s %s" % (m.group(1), m.group(2)) if m else "PARSE_FAIL"
        m2 = re.search(r"\bnodes (\d+)", last)
        nodes = int(m2.group(1)) if m2 else "PARSE_FAIL"
    return {"bestmove": bm, "score": score, "nodes": nodes,
            "info_lines": len(infos), "last": last}


def show(label, r, expect):
    bm = r["bestmove"] if r["bestmove"] not in ("TIMEOUT", "EOF") else "ABSENT(%s)" % r["bestmove"]
    print("  %-38s score=%-12s nodes=%-8s info_lines=%-3s %s" %
          (label, r["score"] or "NO_INFO_LINE", r["nodes"], r["info_lines"], bm), flush=True)
    print("      expected: %s" % expect, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--regime", default="PC20", choices=["none", "S14", "PC20"])
    ap.add_argument("--label", default="")
    a = ap.parse_args()
    opts = opts_for(a.regime)
    print("exe: %s  regime: %s  (%d setoptions)%s" %
          (a.exe, a.regime, len(opts), (" " + a.label) if a.label else ""), flush=True)
    print(flush=True)

    print("CASE 1  mate in one, halfmove 99 (control: must find it)", flush=True)
    show("6k1/5ppp/8/8/8/8/8/R5K1 w - - 99 1",
         run(a.exe, opts, "position fen " + MATE1.format(99)),
         "score mate 1, bestmove a1a8, nodes > 0")

    print(flush=True)
    print("CASE 2  mate in one, halfmove 100 (the base-tree fault)", flush=True)
    show("6k1/5ppp/8/8/8/8/8/R5K1 w - - 100 1",
         run(a.exe, opts, "position fen " + MATE1.format(100)),
         "score mate 1, bestmove a1a8  (base tree gives cp 0 / 0 nodes)")

    print(flush=True)
    print("CASE 3  threefold repetition root (must be a draw: cp 0)", flush=True)
    show("startpos moves " + REP_MOVES,
         run(a.exe, opts, "position startpos moves " + REP_MOVES),
         "score cp 0")

    show("SAME final position given as a plain FEN (no history)",
         run(a.exe, opts, "position fen " + __import__("chess").Board().fen()),
         "control: without history the engine should search normally (NOT cp 0)")
    print(flush=True)
    print("CASE 4  counter-resetting PAWN-move mate at halfmove 100", flush=True)
    show("8/P7/k7/P7/2K5/8/7Q/8 w - - 100 1",
         run(a.exe, opts, "position fen " + MATE_PAWN.format(100)),
         "a7a8=Q# is the only mate and it is a PAWN move -> expect mate 1")
    show("same board at halfmove 99 (control)", run(a.exe, opts,
         "position fen " + MATE_PAWN.format(99)), "mate 1")

    print(flush=True)
    print("CASE 5  already-checkmated root: does it still print 'score mate 0'?", flush=True)
    show("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1 (STALEMATE)",
         run(a.exe, opts, "position fen 7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"),
         "bestmove 0000; note whether the score says 'mate 0' or 'cp 0'")
    show("8/8/8/8/8/6K1/8/Q5k1 b - - 0 1 (CHECKMATE)", run(a.exe, opts,
         "position fen 8/8/8/8/8/6K1/8/Q5k1 b - - 0 1"),
         "bestmove 0000; checkmate must NOT be reported as 'cp 0'")


if __name__ == "__main__":
    main()
