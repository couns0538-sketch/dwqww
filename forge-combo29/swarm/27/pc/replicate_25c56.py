#!/usr/bin/env python3
"""replicate_25c56.py <exe> <fens> [--n 120] [--d1 12] [--d2 16] [--cp 50]

REPLICATION of seat 25's S-C56: is the score-change criterion INVERTED relative to the move-change criterion,
as a predictor of MultiPV disagreement?

THEIR CLAIM (R7, 300 boards, base+S14, Threads 1). Strata defined ONLY from selection data (`bestmove` and
`score` at depths 12 and 16), with the outcome kept out of selection:

    move-unstable   bestmove(d12) != bestmove(d16)                          20/35  = 57.1%
    score-unstable  same move AND |score d12 - score d16| >= 50 cp           7/109 =  6.4%
    neither         (remainder)                                            21/156 = 13.5%

The score stratum is LESS THAN HALF the rate of the boards it excludes. Their mechanism: a large score change
with the move held constant means the search has already converged on the CHOICE and is refining the NUMBER, so
MultiPV does not disturb it. "The instability that matters for MultiPV is instability of the CHOICE, not of
the number."

WHY THIS IS WORTH REPLICATING. It is a claim that a plausible proxy is not merely weak but BACKWARDS, which is
the kind of result that changes how a test set is built - and their practical consequence is strong: enriching
by score-change would have been worse than no criterion at all. It also has a clean, falsifiable mechanism.

WHAT THIS SCRIPT MEASURES, per position (fresh process per cell, all settings asserted):
    free search at d1 -> bestmove, score
    free search at d2 -> bestmove, score
    MultiPV 1 at d2   -> bestmove
    MultiPV 3 at d2   -> bestmove
  stratum (from the two free searches only): move-unstable / score-unstable / neither
  outcome: does MultiPV 3's bestmove differ from MultiPV 1's?

The score stratum requires the SAME move at both depths, as theirs does - so the two strata are disjoint by
construction and the comparison is like-for-like.

CONTROLS:
  1. settings count asserted per cell (22 for PC20), so no row carries a wrong label
  2. every FEN validated with python-chess before use
  3. stratn sizes are printed, so a stratum too small to report is visible rather than silently pooled
  4. SENSITIVITY: the overall MultiPV disagreement rate must be non-zero, or the harness is blind
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

import chess

S14 = ["LmrQuietBase 93", "LmrQuietDivisor 205", "LmrNoisyBase 13", "LmrNoisyDivisor 333",
       "LmrHistoryDivisor 5643", "NullMoveBase 5", "LmpBase 8", "HistoryPruneMultiplier 2220",
       "HistoryBonusQuadratic 24", "HistoryBonusLinear 54", "HistoryBonusMax 2212",
       "SingularDepth 6", "IirDepth 2", "NonPawnCorrection true"]
PC20X = ["CuckooRep true", "HistRework 2", "TtPruneV2 true", "CorrHistV2 true",
         "MateAlphaGuard true", "OwnBook false"]
SETTINGS = {"S14": ["Hash 16", "Threads 1", "OwnBook false"] + S14,
            "PC20": ["Hash 16", "Threads 1"] + S14 + PC20X}
EXPECT = {"S14": 17, "PC20": 22}


class Missing(Exception):
    pass


def run(exe, opts, expect, fen, limit, extra=None):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def s(x):
        p.stdin.write(x + "\n"); p.stdin.flush()

    def until(pred, tmo=300):
        t0 = time.monotonic(); out = []
        while time.monotonic() - t0 < tmo:
            ln = p.stdout.readline()
            if not ln:
                break
            y = ln.rstrip("\n"); out.append(y)
            if pred(y):
                return out, True
        return out, False

    try:
        s("uci")
        lines, ok = until(lambda x: x.strip() == "uciok", 30)
        if not ok:
            raise Missing("no uciok")
        adv = {m.group(1) for m in (re.match(r"option name (.+?) type ", l) for l in lines) if m}
        n = 0
        for item in opts:
            name, _, val = item.rpartition(" ")
            if name not in adv:
                raise Missing("option %r not advertised" % name)
            s("setoption name %s value %s" % (name, val))
            s("isready")
            l2, ok2 = until(lambda x: x.strip() == "readyok", 30)
            if not ok2:
                raise Missing("no readyok")
            for l in l2:
                if "unknown option" in l or "invalid value" in l:
                    raise Missing("bad option %r: %s" % (item, l))
            n += 1
        # EXTRA options (e.g. MultiPV) are applied on top and the count re-asserted, because
        # `go depth 16 multipv 3` is NOT how this engine takes MultiPV - the token is silently ignored and the
        # search runs at MultiPV 1. My first version did exactly that, produced 0 disagreements in all three
        # strata, and the SENSITIVITY control is what exposed it: zero everywhere means the harness is blind,
        # not that the engine is stable.
        for item in (extra or []):
            name, _, val = item.rpartition(" ")
            if name not in adv:
                raise Missing("extra option %r not advertised" % name)
            s("setoption name %s value %s" % (name, val))
            s("isready")
            l3, ok3 = until(lambda x: x.strip() == "readyok", 30)
            if not ok3:
                raise Missing("no readyok after extra %r" % item)
            for l in l3:
                if "unknown option" in l or "invalid value" in l:
                    raise Missing("bad extra option %r: %s" % (item, l))
            n += 1
        want = expect + len(extra or [])
        if n != want:
            raise Missing("applied %d options, label promises %d" % (n, want))
        s("ucinewgame"); s("isready")
        until(lambda x: x.strip() == "readyok", 30)
        s("position fen " + fen); s("isready")
        pos, okp = until(lambda x: x.strip() == "readyok", 30)
        if not okp:
            raise Missing("no readyok after position")
        for l in pos:
            if "invalid fen" in l.lower():
                raise Missing("ENGINE REFUSED THE FEN: %s" % l)
        s(limit)
        out, ok2 = until(lambda x: x.startswith("bestmove"))
        if not ok2:
            raise Missing("no bestmove for %r" % limit)
        infos = [l for l in out if l.startswith("info depth")]
        if not infos:
            raise Missing("no info depth for %r" % limit)
        last = infos[-1]
        sc = re.search(r"score (cp|mate) (-?\d+)", last)
        bm = next(l for l in out if l.startswith("bestmove")).split()
        return {"score": (sc.group(1), int(sc.group(2))) if sc else None,
                "bestmove": bm[1] if len(bm) > 1 else None, "n_applied": n}
    finally:
        try:
            p.stdin.write("quit\n"); p.stdin.flush(); p.wait(timeout=15)
        except Exception:
            p.kill()


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (max(0.0, c - h), min(1.0, c + h))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe"); ap.add_argument("fens")
    ap.add_argument("--n", type=int, default=120)
    ap.add_argument("--d1", type=int, default=12)
    ap.add_argument("--d2", type=int, default=16)
    ap.add_argument("--cp", type=int, default=50)
    ap.add_argument("--settings", default="PC20", choices=list(SETTINGS))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    exe = os.path.realpath(a.exe)
    opts, expect = SETTINGS[a.settings], EXPECT[a.settings]

    fens = []
    for ln in open(a.fens):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        try:
            b = chess.Board(ln)
            if not b.is_valid():
                continue
        except ValueError:
            continue
        fens.append(ln)
        if len(fens) >= a.n:
            break
    if not fens:
        raise SystemExit("no legal positions")

    print("replicating 25-C56: %d positions, depths %d/%d, score threshold %d cp, settings %s (%d opts)"
          % (len(fens), a.d1, a.d2, a.cp, a.settings, expect))

    rows = []
    for i, fen in enumerate(fens):
        r1 = run(exe, opts, expect, fen, "go depth %d" % a.d1)
        r2 = run(exe, opts, expect, fen, "go depth %d" % a.d2)
        # MultiPV is a SETOPTION on this engine; a `multipv` token on `go` is ignored.
        m1 = run(exe, opts, expect, fen, "go depth %d" % a.d2, extra=["MultiPV 1"])
        m3 = run(exe, opts, expect, fen, "go depth %d" % a.d2, extra=["MultiPV 3"])
        if not (r1["score"] and r2["score"]):
            continue
        # only comparable when both scores are cp; a mate score is not on the same scale
        if r1["score"][0] != "cp" or r2["score"][0] != "cp":
            rows.append({"fen": fen, "skipped": "mate score", "r1": r1, "r2": r2})
            continue
        same_move = r1["bestmove"] == r2["bestmove"]
        d_score = abs(r1["score"][1] - r2["score"][1])
        if not same_move:
            stratum = "move-unstable"
        elif d_score >= a.cp:
            stratum = "score-unstable"
        else:
            stratum = "neither"
        disagree = m1["bestmove"] != m3["bestmove"]
        rows.append({"fen": fen, "stratum": stratum, "d_score": d_score,
                     "same_move": same_move, "disagree": disagree,
                     "r1": r1, "r2": r2, "m1": m1, "m3": m3})
        if (i + 1) % 20 == 0:
            print("  %d/%d" % (i + 1, len(fens)))

    used = [r for r in rows if "stratum" in r]
    print()
    print("=== STRATA (selection from the two free searches only) -> MultiPV disagreement ===")
    print("  %-16s %5s %5s   %8s   95%% CI" % ("stratum", "n", "dis", "rate"))
    summary = {}
    for name in ("move-unstable", "score-unstable", "neither"):
        g = [r for r in used if r["stratum"] == name]
        d = sum(1 for r in g if r["disagree"])
        lo, hi = wilson(d, len(g))
        summary[name] = {"n": len(g), "disagree": d, "rate": d / len(g) if g else None,
                         "ci": (lo, hi)}
        print("  %-16s %5d %5d   %7.1f%%   [%.3f, %.3f]"
              % (name, len(g), d, 100 * d / len(g) if g else 0,
                 lo or 0, hi or 0))

    print()
    overall_dis = sum(1 for r in used if r["disagree"])
    print("SENSITIVITY: overall MultiPV disagreement %d of %d = %.1f%%"
          % (overall_dis, len(used), 100 * overall_dis / len(used) if used else 0))
    if overall_dis == 0:
        print("FAIL - no disagreement anywhere, the harness is blind")
    skipped = sum(1 for r in rows if "skipped" in r)
    print("skipped (mate score at either depth): %d" % skipped)

    s_rate = summary["score-unstable"]["rate"]
    r_rate = summary["neither"]["rate"]
    print()
    if s_rate is not None and r_rate is not None:
        verdict = ("INVERSION REPRODUCES: score-unstable %.1f%% < remainder %.1f%%"
                   % (100 * s_rate, 100 * r_rate)) if s_rate < r_rate else \
                  ("NO INVERSION: score-unstable %.1f%% >= remainder %.1f%%"
                   % (100 * s_rate, 100 * r_rate))
        print(verdict)

    # the output directory must be explicit: an earlier script of mine wrote two designs to one path and
    # silently destroyed 600 cells (S-C80), so the path is now a parameter and the name carries the settings.
    outdir = a.out or os.path.dirname(os.path.abspath(a.fens)) or "."
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, "replicate_25c56_%s_d%d_%d.json" % (a.settings, a.d2, len(used)))
    json.dump({"settings": a.settings, "depths": [a.d1, a.d2], "cp": a.cp,
               "rows": rows, "summary": summary}, open(out, "w"), indent=1)
    print("wrote", out)


if __name__ == "__main__":
    main()
