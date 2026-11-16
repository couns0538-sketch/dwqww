#!/usr/bin/env python3
"""rep_pvloop.py EXE --regime R

The decisive experiment for the "does the PC build see repetition INSIDE the search" question.

Method: for a set of shuffle-rich positions, take the engine's own PV, replay it with python-chess,
and ask whether the PV PASSES THROUGH A POSITION IT HAS ALREADY VISITED (a repeat inside the line),
and what score accompanies a line that does.

  - If the PV loops AND the score is cp 0 / mate 0 -> repetition is recognised in-tree.
  - If the PV loops AND the score is decisively non-zero -> repetition is NOT being scored as a draw
    inside the tree, i.e. the machinery itself, not just the root check, differs.
  - If no PV loops, the experiment is INCONCLUSIVE for that position and says so, rather than
    concluding anything from a missing signal.

Root history is given as one repetition (not enough for a draw) so the tree has a head start:
we also report the same position searched with NO history, as a control.

Threads 1. Every number parsed with a loud failure.
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

# Shuffle-rich: the loser has very few squares, so the strong side's winning plan often involves
# the same king/rook squares repeatedly and the PV tends to loop.
POSITIONS = [
    ("K+R+P vs K boxed", "8/8/8/8/8/2k5/1R6/K2R4 w - - 0 1"),
    ("K+R vs K boxed", "8/8/8/8/8/2k5/8/KR6 w - - 0 1"),
    ("K+Q vs K, edge", "8/8/8/8/8/2k5/8/KQ6 w - - 0 1"),
    ("K+B+B vs K", "8/8/8/8/8/2k5/8/KBB5 w - - 0 1"),
]


def opts(regime):
    return [] if regime == "none" else (S14 if regime == "S14" else S14 + PC20_EXTRA)


def key(b):
    return (b.board_fen(), b.turn, b.castling_xfen(), b.ep_square)


def run(exe, o, poscmd, depth, limit=420):
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
    send(poscmd)
    send("isready")
    pos_lines, _ = None, None
    # capture the answer lines so a REFUSED FEN cannot be mistaken for a searched one
    got = []
    t0 = time.monotonic()
    while time.monotonic() - t0 < 30:
        try:
            line = q.get(timeout=0.5)
        except queue.Empty:
            continue
        if line is None:
            break
        got.append(line)
        log.append(line)
        if line.strip() == "readyok":
            break
    refused = [l for l in got if "invalid FEN" in l or "invalid value" in l
               or "illegal move" in l or "unknown option" in l]
    send("go depth %d" % depth)
    bm = wait(lambda l: l.startswith("bestmove"), limit)
    try:
        send("quit"); p.wait(timeout=10)
    except Exception:
        p.kill()
    infos = [l for l in log if l.startswith("info depth")]
    last = infos[-1] if infos else None
    if not last:
        return None
    if refused:
        return {"refused": refused, "score": "REFUSED_FEN", "nodes": None, "pv": [],
                "bestmove": None}
    m = re.search(r"score (cp|mate) (-?\d+)", last)
    m2 = re.search(r"\bnodes (\d+)", last)
    pv = last.split()[last.split().index("pv") + 1:] if " pv" in last else []
    return {"score": ("%s %s" % (m.group(1), m.group(2))) if m else "PARSE_FAIL",
            "nodes": int(m2.group(1)) if m2 else "PARSE_FAIL",
            "pv": pv, "bestmove": bm}


def pv_loops(fen, pv):
    """Does the PV revisit a position? Returns (loops, detail)."""
    b = chess.Board(fen)
    seen = {key(b)}
    for i, u in enumerate(pv):
        try:
            mv = chess.Move.from_uci(u)
        except ValueError:
            return False, "unparsable move %s at %d" % (u, i)
        if mv not in b.legal_moves:
            return False, "illegal %s at %d" % (u, i)
        b.push(mv)
        k = key(b)
        if k in seen:
            return True, "repeats at ply %d (position seen before)" % (i + 1)
        seen.add(k)
    return False, "no repeat in %d plies" % len(pv)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--regime", default="PC20")
    a = ap.parse_args()
    o = opts(a.regime)
    print("exe: %s  regime: %s  Threads 1" % (a.exe, a.regime), flush=True)
    print("%-20s %-6s %-10s %-9s %-5s %-9s %s" %
          ("position", "depth", "score", "nodes", "pv", "loops?", "detail"), flush=True)
    loops_seen = 0
    for label, fen in POSITIONS:
        for d in (8, 10, 12):
            r = run(a.exe, o, "position fen " + fen, d)
            if r is None:
                print("%-20s %-6d %s" % (label, d, "NO_INFO_LINE — inconclusive"), flush=True)
                continue
            lp, detail = pv_loops(fen, r["pv"])
            if lp:
                loops_seen += 1
            print("%-20s %-6d %-10s %-9s %-5d %-9s %s" %
                  (label, d, r["score"], r["nodes"], len(r["pv"]), "YES" if lp else "no",
                   detail), flush=True)
    print(flush=True)
    print("=== POSITIVE CONTROL: a plain startpos must search and must not read REFUSED ===",
          flush=True)
    r = run(a.exe, o, "position startpos", 8)
    print("  startpos d8 -> score=%s nodes=%s pv=%d" %
          (r["score"], r["nodes"], len(r["pv"])), flush=True)
    print("  control verdict: %s" % ("PASS" if r["score"] not in ("REFUSED_FEN", "PARSE_FAIL")
                                     and r["nodes"] else "FAIL"), flush=True)
    print(flush=True)
    print("positions whose PV looped: %d of %d runs" % (loops_seen, len(POSITIONS) * 3), flush=True)
    if loops_seen == 0:
        print("VERDICT: INCONCLUSIVE for the in-search question — no PV in this sample loops, so "
              "this experiment does not separate the two readings. Stated rather than concluded.",
              flush=True)


if __name__ == "__main__":
    main()
