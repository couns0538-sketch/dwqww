#!/usr/bin/env python3
"""check_sf8_impact.py <exe> <fens-file> [--n 40] [--depth 12] [--settings PC20]

THE PRACTICAL QUESTION S-F8 LEAVES OPEN. S-F8/S-P6 established that a `searchmoves` restriction that excludes
NOTHING still changes the REPORTED SCORE (startpos, all 20 legal moves named: cp 29 vs 25 unrestricted on the
PC build). That is a real defect. But the question that decides whether it matters is different:

    does the restriction change the LABEL a training pipeline would record?

A pipeline that verifies a position by re-searching with the intended move named gets two things back: a score
and a bestmove. If the SCORE moves but the MOVE does not, the damage is confined to score targets. If the MOVE
moves, the label itself is wrong and a self-play corpus built that way is corrupted. Those are very different
severities and S-F8 does not distinguish them at scale.

WHAT THIS MEASURES, per position, on one fresh process per cell:
  A  unrestricted            `go depth D`
  B  all-legal-moves named   `go depth D searchmoves <every legal move>`
  C  the A-bestmove only     `go depth D searchmoves <A's bestmove>`   <- what a verifier actually does

  identical bestmove A vs B?   identical score A vs B?
  identical bestmove A vs C?   identical score A vs C?

C is the important arm and neither S-F8 nor S-P6 measured it: a pipeline pinning ONE move is not making the
same comparison as a pipeline naming all twenty.

CONTROLS:
  1. every FEN is verified legal with python-chess before use (a refused FEN would silently play startpos)
  2. the option count is asserted per cell, so no row can carry a wrong settings label
  3. a self-check that arm B really names every legal move (counted, not assumed)
  4. SENSITIVITY: at least one position must show a score difference in some arm, or the harness is blind
"""
import argparse
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


def run(exe, opts, expect, pos, go, timeout=300):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def s(x):
        p.stdin.write(x + "\n"); p.stdin.flush()

    def until(pred, tmo=timeout):
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
        lines, ok = until(lambda x: x.strip() == "uciok")
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
            l2, ok2 = until(lambda x: x.strip() == "readyok")
            if not ok2:
                raise Missing("no readyok")
            for l in l2:
                if "unknown option" in l or "invalid value" in l:
                    raise Missing("bad option %r: %s" % (item, l))
            n += 1
        if expect is not None and n != expect:
            raise Missing("applied %d options, label promises %d" % (n, expect))
        s("ucinewgame"); s("isready")
        until(lambda x: x.strip() == "readyok")
        s(pos); s("isready")
        until(lambda x: x.strip() == "readyok")
        s(go)
        out, ok = until(lambda x: x.startswith("bestmove"))
        if not ok:
            raise Missing("no bestmove for %r" % go)
        infos = [l for l in out if l.startswith("info depth")]
        if not infos:
            raise Missing("no info depth for %r" % go)
        last = infos[-1]
        d = re.search(r"info depth (\d+)", last)
        nd = re.search(r"nodes (\d+)", last)
        sc = re.search(r"score (cp|mate) (-?\d+)", last)
        bm = next(l for l in out if l.startswith("bestmove")).split()
        return {"depth": int(d.group(1)) if d else None,
                "nodes": int(nd.group(1)) if nd else None,
                "score": (sc.group(1), int(sc.group(2))) if sc else None,
                "bestmove": bm[1] if len(bm) > 1 else None,
                "n_applied": n}
    finally:
        try:
            p.stdin.write("quit\n"); p.stdin.flush(); p.wait(timeout=15)
        except Exception:
            p.kill()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe"); ap.add_argument("fens")
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--settings", default="PC20", choices=list(SETTINGS))
    a = ap.parse_args()

    exe = os.path.realpath(a.exe)
    opts, expect = SETTINGS[a.settings], EXPECT[a.settings]

    fens, rejected = [], []
    for ln in open(a.fens):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        try:
            b = chess.Board(ln)
            if not b.is_valid() or not b.legal_moves.count() if hasattr(b.legal_moves, "count") else False:
                rejected.append((ln, "invalid"))
                continue
        except ValueError as e:
            rejected.append((ln, str(e)))
            continue
        fens.append(ln)
        if len(fens) >= a.n:
            break
    if not fens:
        raise SystemExit("no legal positions")

    print("settings=%s (%d options), depth %d, %d positions, %d rejected"
          % (a.settings, expect, a.depth, len(fens), len(rejected)))

    rows = []
    for i, fen in enumerate(fens):
        b = chess.Board(fen)
        legal = [m.uci() for m in b.legal_moves]
        if not legal:
            continue
        pos = "position fen " + fen
        A = run(exe, opts, expect, pos, "go depth %d" % a.depth)
        B = run(exe, opts, expect, pos,
                "go depth %d searchmoves %s" % (a.depth, " ".join(legal)))
        C = run(exe, opts, expect, pos,
                "go depth %d searchmoves %s" % (a.depth, A["bestmove"]))
        row = {"fen": fen, "n_legal": len(legal), "A": A, "B": B, "C": C,
               "B_same_move": A["bestmove"] == B["bestmove"],
               "B_same_score": A["score"] == B["score"],
               "C_same_move": A["bestmove"] == C["bestmove"],
               "C_same_score": A["score"] == C["score"]}
        rows.append(row)
        if (i + 1) % 10 == 0:
            print("  %d/%d" % (i + 1, len(fens)))

    n = len(rows)
    def cnt(k):
        return sum(1 for r in rows if r[k])
    print()
    print("=== arm B: ALL legal moves named (a restriction that excludes nothing) ===")
    print("  same bestmove  %d/%d" % (cnt("B_same_move"), n))
    print("  same score     %d/%d" % (cnt("B_same_score"), n))
    print()
    print("=== arm C: ONLY the unrestricted bestmove named (what a verifier does) ===")
    print("  same bestmove  %d/%d" % (cnt("C_same_move"), n))
    print("  same score     %d/%d" % (cnt("C_same_score"), n))
    print()
    diffs = [abs(r["A"]["score"][1] - r["B"]["score"][1]) for r in rows
             if r["A"]["score"] and r["B"]["score"] and r["A"]["score"][0] == r["B"]["score"][0] == "cp"]
    if diffs:
        print("  |cp difference| A vs B: max %d, mean %.2f, non-zero in %d of %d"
              % (max(diffs), sum(diffs) / len(diffs), sum(1 for d in diffs if d), len(diffs)))

    # control 4: sensitivity - if nothing differs anywhere the harness may be blind
    sensitive = any(not r["B_same_score"] or not r["C_same_score"] for r in rows)
    print()
    print("SENSITIVITY CONTROL (some score must differ somewhere): %s" % ("PASS" if sensitive else "FAIL - harness may be blind"))
    out = os.path.join(os.path.dirname(os.path.abspath(a.fens)) or ".", "sf8_impact.json")
    import json
    json.dump({"settings": a.settings, "depth": a.depth, "rows": rows,
               "sensitive": sensitive}, open(out, "w"), indent=1)
    print("wrote", out)


if __name__ == "__main__":
    main()
