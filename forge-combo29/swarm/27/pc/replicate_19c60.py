#!/usr/bin/env python3
"""replicate_19c60.py <exe> <fens> [--n 120] [--depth 12] [--out outdir]

REPLICATION of seat 19's 19-C59 / 19-C60, on my own position set.

THEIR CLAIM. One PC20 switch at a time, all other PC switches held OFF, PC r15, Threads 1, Hash 16, depth 12,
120 real positions, fresh process, interleaved. They report:

    switch        pooled   median  sign-share  IQR     IQR/effect  sign-test p
    TtPruneV2     0.9528   0.928   60.8%       0.462   9.8         1.000
    CuckooRep     0.9914   0.999   52.5%       0.256   28.4        1.000
    CorrHistV2    0.9478   0.959   54.2%       0.413   7.9         1.000
    HistRework    1.0311   1.018   46.7%       0.514   16.6        0.523

Reading: each switch saves/loses 1-5 % of nodes POOLED, but the per-position spread is 8-28x the size of that
effect, and the sign agreement across positions is what a coin flip gives. **So "this switch saves 5 % of nodes"
is not a statement about the switch — it is a statement about the average of a distribution that is mostly
noise.** They also report a FAILED prediction (TtPruneV2 at 60.8 % against a predicted 65-80 %) and they decline
to rescue it by moving their own 60 % kill line.

WHY A REPLICATION IS WORTH RUNNING. Three reasons this is a high-value target:
  1. It is a NEGATIVE result with a stated mechanism, and a negative result is exactly what a second
     implementation should confirm before the owner acts on it.
  2. It CONTRADICTS an intuition ("a hard pruning gate is deterministic, so it must help consistently"),
     which makes it the kind of finding that gets quietly dropped rather than checked.
  3. The distinction between "run-to-run noise" and "per-position spread" is easy to conflate, and my own
     S-C31 (Threads 1 is bit-exact on 40 of 40 positions at depth 12) says the engine is deterministic here.
     So their "coin flip" must be ACROSS POSITIONS, not across runs. This script measures both so the two
     cannot be confused.

DESIGN. Interleaved within each position, fresh process per run, baseline and switch measured back to back so
machine drift cannot masquerade as a switch effect:
    S14 baseline  ->  S14 + switch A  ->  S14 + switch B  -> ...
and every process asserts its own option count, so no row can carry a wrong settings label.

REPORTED PER SWITCH: pooled ratio, median ratio, sign share (fraction of positions where the switch used FEWER
nodes), IQR, IQR/|effect|, and an exact sign-test p. Plus a REPEAT control on a subset: the same cell measured
twice, to show run-to-run spread is zero and the distribution is genuinely position-to-position.
"""
import argparse
import json
import math
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
SWITCHES = {
    "TtPruneV2": "TtPruneV2 true",
    "CuckooRep": "CuckooRep true",
    "CorrHistV2": "CorrHistV2 true",
    "HistRework": "HistRework 2",
}
BASE = ["Hash 16", "Threads 1", "OwnBook false"] + S14
EXPECT_BASE = 17


class Missing(Exception):
    pass


def run(exe, opts, expect, fen, depth, timeout=300):
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
        if n != expect:
            raise Missing("applied %d options, label promises %d" % (n, expect))
        s("ucinewgame"); s("isready")
        until(lambda x: x.strip() == "readyok")
        s("position fen " + fen); s("isready")
        until(lambda x: x.strip() == "readyok")
        s("go depth %d" % depth)
        out, ok = until(lambda x: x.startswith("bestmove"))
        if not ok:
            raise Missing("no bestmove")
        infos = [l for l in out if l.startswith("info depth %d " % depth)]
        if not infos:
            infos = [l for l in out if l.startswith("info depth")]
        if not infos:
            raise Missing("no info depth at all")
        last = infos[-1]
        nd = re.search(r"nodes (\d+)", last)
        sc = re.search(r"score (cp|mate) (-?\d+)", last)
        bm = [l for l in out if l.startswith("bestmove")][0].split()
        return {"nodes": int(nd.group(1)) if nd else None,
                "score": (sc.group(1), int(sc.group(2))) if sc else None,
                "bestmove": bm[1] if len(bm) > 1 else None,
                "n_applied": n, "last": last}
    finally:
        try:
            p.stdin.write("quit\n"); p.stdin.flush(); p.wait(timeout=15)
        except Exception:
            p.kill()


def median(xs):
    s = sorted(xs); n = len(s)
    if not n:
        return None
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def quartiles(xs):
    s = sorted(xs)
    if len(s) < 4:
        return None, None
    n = len(s)
    q1 = s[n // 4]
    q3 = s[(3 * n) // 4]
    return q1, q3


def sign_p(k, n):
    """Exact two-sided binomial vs p=0.5, ties dropped."""
    if n == 0:
        return 1.0
    from math import comb
    obs = comb(n, k)
    tot = sum(comb(n, i) for i in range(n + 1) if comb(n, i) <= obs)
    return min(1.0, tot / (2 ** n))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe"); ap.add_argument("fens")
    ap.add_argument("--n", type=int, default=120)
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--out", default=".")
    ap.add_argument("--baseline", default="s14", choices=["s14","pc20"],
                    help="s14 = add ONE switch to S14 (sufficiency); pc20 = DROP one from full PC20 (necessity)")
    ap.add_argument("--repeat-check", type=int, default=10,
                    help="re-measure this many baseline cells to show run-to-run spread is zero")
    a = ap.parse_args()

    exe = os.path.realpath(a.exe)
    PC20X = ["CuckooRep true", "HistRework 2", "TtPruneV2 true", "CorrHistV2 true", "MateAlphaGuard true"]
    if a.baseline == "pc20":
        BASE_OPTS = ["Hash 16", "Threads 1"] + S14 + PC20X + ["OwnBook false"]
        EXPECT_BASE = 22
        arm = lambda opt: [x for x in BASE_OPTS if x != opt]
        EXP_ARM = 21
        design = "DROP one switch from full PC20 (necessity in the bundle)"
    else:
        BASE_OPTS = ["Hash 16", "Threads 1", "OwnBook false"] + S14
        EXPECT_BASE = 17
        arm = lambda opt: BASE_OPTS + [opt]
        EXP_ARM = 18
        design = "ADD one switch to S14 (sufficiency from baseline)"
    fens, rejected = [], 0
    for ln in open(a.fens):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        try:
            b = chess.Board(ln)
            if not b.is_valid():
                rejected += 1
                continue
        except ValueError:
            rejected += 1
            continue
        fens.append(ln)
        if len(fens) >= a.n:
            break
    if not fens:
        raise SystemExit("no legal positions")

    print("replicating 19-C60: %d positions, depth %d, %d rejected, exe %s"
          % (len(fens), a.depth, rejected, exe))
    print("design: %s" % design)

    R = {"exe": exe, "baseline": a.baseline, "sha256": subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0],
         "depth": a.depth, "n_positions": len(fens), "switches": {}}

    per_switch = {k: [] for k in SWITCHES}
    run_to_run = []

    for i, fen in enumerate(fens):
        base = run(exe, BASE_OPTS, EXPECT_BASE, fen, a.depth)
        if base["nodes"] is None:
            continue
        if i < a.repeat_check:
            again = run(exe, BASE_OPTS, EXPECT_BASE, fen, a.depth)
            run_to_run.append((base["nodes"], again["nodes"]))
        row = {}
        for name, opt in SWITCHES.items():
            r = run(exe, arm(opt), EXP_ARM, fen, a.depth)
            if r["nodes"] is None:
                continue
            row[name] = r["nodes"]
            per_switch[name].append(r["nodes"] / base["nodes"])
        R["switches"][str(i)] = {"fen": fen, "base_nodes": base["nodes"], **row}
        if (i + 1) % 20 == 0:
            print("  %d/%d" % (i + 1, len(fens)))

    print()
    print("=== RUN-TO-RUN CONTROL (same cell measured twice) ===")
    diffs = [abs(b - c) for b, c in run_to_run]
    print("  %d cells re-measured; identical in %d; max node difference %s"
          % (len(run_to_run), sum(1 for d in diffs if d == 0), max(diffs) if diffs else "n/a"))
    print("  -> the spread below is POSITION-TO-POSITION, not noise")
    R["run_to_run"] = {"cells": len(run_to_run), "identical": sum(1 for d in diffs if d == 0),
                       "max_diff": max(diffs) if diffs else None}

    print()
    print("=== REPLICATION TABLE (their figures in brackets) ===")
    print("  switch        pooled  median  sign-share  IQR    IQR/effect  sign p")
    for name, ratios in per_switch.items():
        if not ratios:
            continue
        pooled = math.exp(sum(math.log(x) for x in ratios) / len(ratios))
        med = median(ratios)
        below = sum(1 for x in ratios if x < 1.0)
        ties = sum(1 for x in ratios if x == 1.0)
        q1, q3 = quartiles(ratios)
        iqr = (q3 - q1) if q1 is not None else None
        eff = abs(1.0 - pooled)
        # IQR/effect is DEGENERATE when the pooled effect is ~0: dividing a spread by 0.0002 produced 2327.7
        # for a switch whose ratio was 1.0000 to four decimal places. Report a floor instead of a huge number,
        # because "2327x" invites the reader to think a real effect is being swamped when there is NO effect.
        if iqr is None:
            ratio_ie = None
        elif eff < 1e-3:
            ratio_ie = float("inf")
        else:
            ratio_ie = iqr / eff
        p = sign_p(below, below + (len(ratios) - below - ties))
        R["switches"][name] = {"pooled": pooled, "median": med, "sign_share": below / len(ratios),
                               "n": len(ratios), "iqr": iqr, "iqr_over_effect": ratio_ie, "p": p}
        print("  %-13s %.4f  %.3f   %5.1f%%      %s   %s       %.3f"
              % (name, pooled, med, 100 * below / len(ratios),
                 ("%.3f" % iqr) if iqr is not None else " n/a ",
                 ("none (effect ~0)" if ratio_ie == float("inf") else ("%.1f" % ratio_ie)) if ratio_ie is not None else " n/a", p))

    os.makedirs(a.out, exist_ok=True)
    # the BASELINE MODE must be in the filename: the first run of this script wrote both designs to one
    # path and the drop-one silently overwrote the add-one, losing those 600 cells. A result file whose
    # name does not name its design is not a result file.
    out = os.path.join(a.out, "replicate_19c60_%s_d%d_n%d.json" % (a.baseline, a.depth, len(fens)))
    json.dump(R, open(out, "w"), indent=1)
    print("\nwrote", out)


if __name__ == "__main__":
    main()
