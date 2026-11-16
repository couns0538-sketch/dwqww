#!/usr/bin/env python3
"""mate0_parser.py EXE --regime none|S14|PC20

What does a real UCI parser do with the engine's terminal-root lines?
python-chess is used as the parser because it is the library every seat in this swarm uses and the
one behind most non-GUI tooling; its docs state the Mate(0) / MateGiven distinction explicitly.

For the three terminal cases the script:
  1. sends the position and a `go depth 8`, capturing the final info line and the bestmove;
  2. feeds that exact `info` line to python-chess's own UCI score parser;
  3. reports what python-chess makes of it: .mate(), .is_mate(), the ordering against Mate(-1)
     and MateGiven, and - crucially - what a GUI showing a WDL/ordering would do with it.
"""
import argparse
import queue
import re
import subprocess
import threading
import time

import chess
import chess.engine

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

CASES = [
    ("CHECKMATE", "8/8/8/8/8/6K1/8/Q5k1 b - - 0 1"),
    ("STALEMATE", "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"),
    ("INSUFFICIENT (K v K)", "8/8/4k3/8/8/4K3/8/8 w - - 0 1"),
    ("INSUFFICIENT (KN v K)", "8/8/4k3/8/8/4K3/5N2/8 w - - 0 1"),
]


def opts_for(regime):
    return [] if regime == "none" else (S14 if regime == "S14" else S14 + PC20_EXTRA)


def run(exe, opts, fen, go="depth 8", limit=120):
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
    send("position fen " + fen); send("isready"); wait(lambda l: l == "readyok", 30)
    send("go " + go)
    bm = wait(lambda l: l.startswith("bestmove"), limit)
    try:
        send("quit"); p.wait(timeout=10)
    except Exception:
        p.kill()
    infos = [l for l in log if l.startswith("info depth")]
    return bm, (infos[-1] if infos else None), len(infos)


def parse_with_python_chess(info_line, fen):
    """Feed the engine's exact info line to python-chess's own UCI info parser."""
    if info_line is None:
        return "NO_INFO_LINE (nothing to parse)"
    board = chess.Board(fen)
    try:
        info = chess.engine._parse_uci_info(info_line, board)
    except Exception as e:
        return "PARSE_FAIL: %s" % e
    if "score" not in info:
        return "python-chess found NO 'score' key in: %s" % info_line
    pov = info["score"].pov(board.turn)   # score relative to the side to move
    return ("python-chess: %r  mate()=%s is_mate()=%s  as_cp(mate_score=100000)=%s"
            % (info["score"], pov.mate(), pov.is_mate(), pov.score(mate_score=100000)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--regime", default="PC20", choices=["none", "S14", "PC20"])
    a = ap.parse_args()
    opts = opts_for(a.regime)
    print("exe: %s  regime: %s  Threads 1" % (a.exe, a.regime), flush=True)
    for name, fen in CASES:
        bm, last, n = run(a.exe, opts, fen)
        sc = re.search(r"score (cp|mate) (-?\d+)", last) if last else None
        shown = "%s %s" % (sc.group(1), sc.group(2)) if sc else "NONE"
        print(flush=True)
        print("%-24s %s" % (name, fen), flush=True)
        print("   engine : score=%-9s info_lines=%-3d %s" % (shown, n, bm), flush=True)
        print("   python-chess reads it as:", parse_with_python_chess(last, fen), flush=True)


if __name__ == "__main__":
    main()
