#!/usr/bin/env python3
"""repcount.py EXE --regime none|S14|PC20

Does the build declare a root drawn at the SECOND occurrence or only the THIRD?
File 3 of the handoff says the PC "also needs a THIRD occurrence: a second one is searched normally"
(Board::is_repetition, matches >= 2). This tests it directly.

For each repetition count 1 (no repeat), 2 (once repeated) and 3 (twice repeated) build a
`position startpos moves ...` line whose final position has occurred exactly that many times,
verify the count with python-chess, then search and report score + nodes.

Same board every time; only the amount of history differs. That isolates the repetition rule from
any evaluation difference.
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

CYCLE = ["g1f3", "g8f6", "f3g1", "f6g8"]   # returns the board to the same position


def key(b):
    return (b.board_fen(), b.turn, b.castling_xfen(), b.ep_square)


def build_line(cycles):
    """cycles = 0 -> start position only; 1 -> position occurred twice; 2 -> three times."""
    b = chess.Board()
    moves = []
    counts = {key(b): 1}
    for _ in range(cycles):
        for u in CYCLE:
            b.push(chess.Move.from_uci(u))
            moves.append(u)
            counts[key(b)] = counts.get(key(b), 0) + 1
    return b, moves, counts[key(b)]


def opts_for(regime):
    return [] if regime == "none" else (S14 if regime == "S14" else S14 + PC20_EXTRA)


def run(exe, opts, poscmd, go="depth 10", limit=120):
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
    for k, v in opts:
        send("setoption name %s value %s" % (k, v))
    send("isready"); wait(lambda l: l == "readyok", 30)
    send("ucinewgame"); send("isready"); wait(lambda l: l == "readyok", 30)
    send(poscmd); send("isready"); wait(lambda l: l == "readyok", 30)
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
    return score, nodes, bm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--regime", default="PC20", choices=["none", "S14", "PC20"])
    ap.add_argument("--label", default="")
    a = ap.parse_args()
    opts = opts_for(a.regime)
    print("exe: %s  regime: %s %s  Threads 1" % (a.exe, a.regime, a.label), flush=True)
    print("%-10s %-6s %-12s %-10s %-12s %s" %
          ("occurrences", "plies", "score", "nodes", "bestmove", "verdict"), flush=True)
    for cycles, want in ((0, 1), (1, 2), (2, 3)):
        b, moves, occ = build_line(cycles)
        assert occ == want, "built %d occurrences, wanted %d" % (occ, want)
        # verify with python-chess's own repetition notion where applicable
        pc = ""
        if moves:
            bb = chess.Board()
            for u in moves:
                bb.push(chess.Move.from_uci(u))
            pc = "python-chess is_repetition(2)=%s is_repetition(3)=%s" % (
                bb.is_repetition(2), bb.is_repetition(3))
        cmd = "position startpos" + (" moves " + " ".join(moves) if moves else "")
        score, nodes, bm = run(a.exe, opts, cmd)
        bm_s = bm if bm not in ("TIMEOUT", "EOF") else "ABSENT(%s)" % bm
        drawn = (score == "cp 0" and nodes == 0)
        print("%-10d %-6d %-12s %-10s %-12s %s   [%s]" %
              (occ, len(moves), score, nodes, bm_s,
               "DECLARED DRAWN (0 nodes)" if drawn else "searched", pc), flush=True)


if __name__ == "__main__":
    main()
