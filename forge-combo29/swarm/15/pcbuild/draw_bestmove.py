#!/usr/bin/env python3
"""draw_bestmove.py EXE --regime R

The question the split leaves open, and the one a GUI hits: when the root is declared DRAWN,
what does `bestmove` say — `0000` (a null move) or a real move?

A root adjudicated drawn by repetition is still a position with legal moves: if the opponent does not
claim the draw the game continues, so a GUI needs a real move to play. `0000` is the UCI null move and
means "no move", so returning it here would be wrong for a GUI.

Cases, each in a fresh process, Threads 1, stdout read until bestmove:
  1. thrice-repeated root                 -> drawn; bestmove should be a REAL move
  2. twice-repeated root (control)        -> searched; real move
  3. plain startpos (control)             -> searched; real move
  4. checkmated root (control)            -> NO legal move; bestmove MUST be 0000
  5. stalemated root (control)            -> NO legal move; bestmove MUST be 0000
  6. insufficient material (control)      -> drawn, but legal moves EXIST; bestmove should be REAL

Cases 4 and 5 are the controls that make case 1 and 6 meaningful: they prove the harness can see a
0000 when one is correct, so a real move at case 1/6 is a real distinction and not the harness
failing to read a 0000.
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
REP3 = "g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8"
REP2 = "g1f3 g8f6 f3g1 f6g8"


def opts(regime):
    return [] if regime == "none" else (S14 if regime == "S14" else S14 + PC20_EXTRA)


def run(exe, o, poscmd, depth=10, limit=180):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    q = queue.Queue()

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
    if bm in ("TIMEOUT", "EOF"):
        return {"bestmove": "ABSENT(%s)" % bm, "tok": None}
    t = bm.split()
    return {"bestmove": bm, "tok": t[1] if len(t) > 1 else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--regime", default="PC20")
    a = ap.parse_args()
    o = opts(a.regime)
    print("exe: %s  regime: %s  Threads 1" % (a.exe, a.regime), flush=True)
    print("%-44s %-8s %-10s %-6s %s" %
          ("case", "legal", "bestmove", "is0000", "expected"), flush=True)

    cases = [
        ("1 thrice-repeated root", "position startpos moves " + REP3, "REAL move"),
        ("2 twice-repeated root (control)", "position startpos moves " + REP2, "REAL move"),
        ("3 plain startpos (control)", "position startpos", "REAL move"),
        ("4 CHECKMATED root (control)", "position fen 8/8/8/8/8/6K1/8/Q5k1 b - - 0 1", "0000"),
        ("5 STALEMATED root (control)", "position fen 7k/5Q2/6K1/8/8/8/8/8 b - - 0 1", "0000"),
        ("6 insufficient material (control)", "position fen 8/8/4k3/8/8/4K3/8/8 w - - 0 1", "REAL move"),
    ]
    for label, poscmd, expect in cases:
        if poscmd.startswith("position fen "):
            b = chess.Board(poscmd[len("position fen "):])
            legal = b.legal_moves.count()
        else:
            b = chess.Board()
            for u in poscmd.split(" moves ")[1].split() if " moves " in poscmd else []:
                b.push(chess.Move.from_uci(u))
            legal = b.legal_moves.count()
        r = run(a.exe, o, poscmd)
        is0 = "YES" if r["tok"] == "0000" else ("no" if r["tok"] else "?")
        got = "0000" if r["tok"] == "0000" else "REAL"
        want = "0000" if expect == "0000" else "REAL"
        verdict = "ok" if got == want else ("WRONG" if r["tok"] else "UNREAD")
        print("%-44s %-8d %-10s %-6s %-9s %s" %
              (label, legal, r["tok"] or r["bestmove"], is0, expect, verdict), flush=True)


if __name__ == "__main__":
    main()
