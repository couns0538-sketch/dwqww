#!/usr/bin/env python3
"""ladder.py EXE FEN D1 D2 ... : one fresh process per depth, full info stream kept.

Prints one line per depth: depth, score, PV length, whether the PV replays as a legal line ending in checkmate,
and the number of distinct mate numbers seen so far. Used to test whether a reported mate number ever FALLS as
depth rises, on a single board where depth 12 said mate 6 and depth 20 said mate 4.
"""
import json
import re
import shlex
import subprocess
import sys

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]


def search(exe, fen, depth):
    p = subprocess.Popen(shlex.split(exe), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in S14:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"go depth {depth}\n"); p.stdin.flush()
    lines, best = [], None
    for line in p.stdout:
        s = line.rstrip("\n")
        if s.startswith("info depth"):
            lines.append(s)
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=120)
    except subprocess.TimeoutExpired:
        p.kill()
    return lines, best


def pv_replay(fen, pv):
    b = chess.Board(fen)
    for mv in pv:
        try:
            m = chess.Move.from_uci(mv)
        except ValueError:
            return "BAD-UCI"
        if m not in b.legal_moves:
            return "ILLEGAL"
        b.push(m)
    return "MATE" if b.is_checkmate() else "nomate"


def main():
    exe, fen = sys.argv[1], sys.argv[2]
    depths = [int(x) for x in sys.argv[3:]]
    for d in depths:
        lines, best = search(exe, fen, d)
        score, pv = "?", []
        if lines:
            m = re.search(r"score (cp|mate) (-?\d+)", lines[-1])
            score = m.group(0) if m else "?"
            t = lines[-1].split()
            pv = t[t.index("pv") + 1:] if "pv" in t else []
        need = None
        mm = re.search(r"mate (-?\d+)", score)
        if mm:
            v = int(mm.group(1))
            need = 2 * v - 1 if v > 0 else 2 * abs(v)
        ends = pv_replay(fen, pv) if pv else "EMPTY"
        print(json.dumps({"depth": d, "score": score, "pv_len": len(pv), "need": need,
                          "pv_ends": ends, "bestmove": best, "pv": pv}), flush=True)


if __name__ == "__main__":
    main()
