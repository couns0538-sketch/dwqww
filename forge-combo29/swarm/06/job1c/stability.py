#!/usr/bin/env python3
"""Is the colour-mirror search asymmetry STABLE per position, or does it flip in and out?

For every position that mismatched in a first pass, search the pair again in FRESH processes, the same
number of times, and count how often it still mismatches. A position that mismatches every time is
deterministic; one that flips is a margin tie-break, which is a different thing to fix.

Each search is the FIRST search in a new process (so no state carries in), ucinewgame + isready before
every go, Threads always 1.

usage: stability.py EXE FENFILE MODE RUNS OUTFILE
  MODE = S14 (base-style) or PC20
"""
import json
import subprocess
import sys

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
BAD = ("unknown option", "invalid value", "ERROR")


def one_search(exe, fen, depth, options):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def w(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def r():
        line = p.stdout.readline()
        if line == "":
            raise RuntimeError("died")
        return line

    def ready():
        while True:
            line = r().strip()
            if any(m in line for m in BAD):
                raise RuntimeError(line)
            if line == "readyok":
                return

    w("uci")
    while r().strip() != "uciok":
        pass
    for n, v in [("Threads", "1"), ("Hash", "16")] + options:
        w("setoption name %s value %s" % (n, v))
        w("isready")
        ready()
    w("ucinewgame")
    w("isready")
    ready()
    w("position fen " + fen)
    w("isready")
    ready()
    w("go depth %d" % depth)
    last = None
    while True:
        line = r().strip()
        if " pv " in line and line.startswith("info"):
            last = line
        if line.startswith("bestmove"):
            bm = line.split()[1]
            break
    p.kill()
    t = last.split() if last else []
    return {"bm": bm,
            "kind": t[t.index("score") + 1] if "score" in t else None,
            "score": int(t[t.index("score") + 2]) if "score" in t else None}


def mir(u):
    return (chess.square_name(chess.parse_square(u[0:2]) ^ 56) +
            chess.square_name(chess.parse_square(u[2:4]) ^ 56) + (u[4:] or ""))


def main():
    exe, fenfile, mode, runs, outfile = sys.argv[1:6]
    runs = int(runs)
    options = PC20 if mode == "PC20" else S14
    fens = [l.strip() for l in open(fenfile) if l.strip()]
    out = open(outfile, "w")
    always = sometimes = never = 0
    for i, fen in enumerate(fens):
        mfen = chess.Board(fen).mirror().fen()
        bm_hits = sc_hits = 0
        sample = []
        for _ in range(runs):
            a = one_search(exe, fen, 10, options)
            b = one_search(exe, mfen, 10, options)
            bm_bad = b["bm"] != mir(a["bm"])
            sc_bad = a["kind"] != b["kind"] or a["score"] != b["score"]
            bm_hits += 1 if bm_bad else 0
            sc_hits += 1 if sc_bad else 0
            if len(sample) < 2:
                sample.append([a, b])
        if bm_hits == runs:
            always += 1
        elif bm_hits == 0:
            never += 1
        else:
            sometimes += 1
        out.write(json.dumps({"index": i, "fen": fen, "runs": runs,
                              "bm_mismatch_hits": bm_hits, "score_diff_hits": sc_hits,
                              "sample": sample}) + "\n")
        out.flush()
    out.close()
    print("positions tested: %d, runs each: %d" % (len(fens), runs))
    print("  bestmove mismatch in EVERY run (deterministic): %d" % always)
    print("  bestmove mismatch in SOME runs (flips):         %d" % sometimes)
    print("  bestmove mismatch in NO run:                    %d" % never)


if __name__ == "__main__":
    main()
