#!/usr/bin/env python3
"""regimes.py OUTDIR -- map the interruption regimes precisely, on BOTH builds.

For each (build, settings, position, delay) one FRESH process:
  1. write the setup, wait for readyok, send `go depth 12`
  2. sleep exactly `delay` ms (monotonic, from the moment the go line is flushed)
  3. send `quit` and read everything to exit
and separately the FINISHED answer for the same build/settings/position (read to bestmove, no interruption).

Recorded per cell: info lines, last score, bestmove, and whether it EQUALS the finished answer
(move and score both). The score error is |interrupted score - finished score| in centipawns where both are
numeric; a mate/absent score is reported as such rather than coerced to a number.

Positions: startpos, two middlegame FENs from set G, and a tactical position, so the score error is not a
property of one board.

Threads 1, Hash 16, OwnBook false throughout (seat 04's rule).

Usage: regimes.py OUTDIR [builds]   builds = "both" (default) | "base" | "pc"
"""
import json
import os
import statistics
import subprocess
import sys
import time

BASE = os.path.expanduser("~/builds/release/forge")
PC = os.path.expanduser("~/builds/pc/forge")
OUT = os.path.abspath(sys.argv[1])
WHICH = sys.argv[2] if len(sys.argv) > 2 else "both"
os.makedirs(OUT, exist_ok=True)
DEPTH = 12
DELAYS = [0, 5, 10, 15, 20, 25, 30, 35, 40, 50, 75]

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

POSITIONS = {
    "startpos": "position startpos",
    "G_black_mid": "position fen r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PPG1/1R1Q1RK1 b - - 0 1".replace("PPG1", "PP1"),
    "G_knight_out": "position fen 1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1",
    "tactical": "position fen r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 0 1",
}


def setup(regime):
    lines = ["uci", "isready", "setoption name Threads value 1",
             "setoption name Hash value 16", "setoption name OwnBook value false"]
    lines += ["setoption name %s value %s" % kv for kv in (S14 if regime == "s14" else PC20)]
    lines += ["isready", "ucinewgame", "isready"]
    return lines


def score_of(lines):
    for l in reversed(lines):
        if " score cp " in l:
            try:
                return ("cp", int(l.split(" score cp ")[1].split()[0]))
            except (IndexError, ValueError):
                return None
        if " score mate " in l:
            try:
                return ("mate", int(l.split(" score mate ")[1].split()[0]))
            except (IndexError, ValueError):
                return None
    return None


def parse(lines):
    info = [l for l in lines if l.startswith("info depth")]
    bm = None
    for l in lines:
        if l.startswith("bestmove"):
            bm = l.split()[1]
    return {"info_lines": len(info), "score": score_of(info), "bestmove": bm}


def finished(exe, regime, pos):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    for l in setup(regime) + [pos]:
        p.stdin.write(l + "\n")
        p.stdin.flush()
    p.stdin.write("isready\n")
    p.stdin.flush()
    p.stdin.write("go depth %d\n" % DEPTH)
    p.stdin.flush()
    lines = []
    while True:
        line = p.stdout.readline()
        if not line:
            break
        lines.append(line.rstrip())
        if line.startswith("bestmove"):
            break
    p.stdin.write("quit\n")
    try:
        p.stdin.flush()
    except Exception:
        pass
    try:
        p.wait(timeout=30)
    except Exception:
        p.kill()
    return parse(lines)


def interrupted(exe, regime, pos, delay_ms):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    for l in setup(regime) + [pos, "isready"]:
        p.stdin.write(l + "\n")
        p.stdin.flush()
    t0 = time.monotonic()
    p.stdin.write("go depth %d\n" % DEPTH)
    p.stdin.flush()
    target = t0 + delay_ms / 1000.0
    while time.monotonic() < target:
        time.sleep(max(0.0, min(0.001, target - time.monotonic())))
    elapsed = (time.monotonic() - t0) * 1000.0
    try:
        p.stdin.write("quit\n")
        p.stdin.flush()
    except Exception:
        pass
    try:
        out = p.communicate(timeout=120)[0]
    except Exception:
        p.kill()
        out = p.communicate()[0]
    rec = parse(out.splitlines())
    rec["delay_ms"] = delay_ms
    rec["actual_ms"] = round(elapsed, 1)
    return rec


def score_delta(fin, got):
    """centipawn difference, or a marker string when not comparable"""
    if fin is None or got is None:
        return None
    if fin[0] != got[0]:
        return "%s->%s" % (fin[0], got[0])
    d = got[1] - fin[1]
    if fin[0] == "mate":
        return "mate %+d" % d
    return d


def main():
    builds = []
    if WHICH in ("both", "base"):
        builds.append(("base_s14", BASE, "s14"))
    if WHICH in ("both", "pc"):
        builds.append(("pc20", PC, "pc20"))
    out = {"depth": DEPTH, "delays": DELAYS, "builds": {}}
    for bname, exe, regime in builds:
        out["builds"][bname] = {}
        for pname, pos in POSITIONS.items():
            fin = finished(exe, regime, pos)
            rows = []
            for d in DELAYS:
                r = interrupted(exe, regime, pos, d)
                r["score_delta_vs_finished"] = score_delta(fin["score"], r["score"])
                r["same_move_as_finished"] = (r["bestmove"] == fin["bestmove"])
                r["equals_finished"] = (r["bestmove"] == fin["bestmove"]
                                        and r["score"] == fin["score"])
                rows.append(r)
            out["builds"][bname][pname] = {"finished": fin, "rows": rows}
            with open(os.path.join(OUT, "regimes.json"), "w") as f:
                json.dump(out, f, indent=2)
                f.write("\n")
            bad = [r for r in rows if not r["equals_finished"]]
            print("%-9s %-14s finished %-6s %-10s  %d/%d cells differ from finished"
                  % (bname, pname, fin["bestmove"], str(fin["score"]), len(bad), len(rows)),
                  flush=True)

    # boundary analysis: for each build, the largest delay that still differs, per position
    summary = {}
    for bname in out["builds"]:
        per_pos = {}
        for pname, block in out["builds"][bname].items():
            differ = [r["delay_ms"] for r in block["rows"] if not r["equals_finished"]]
            deltas = [r["score_delta_vs_finished"] for r in block["rows"]]
            numeric = [d for d in deltas if isinstance(d, int)]
            per_pos[pname] = {
                "largest_delay_that_still_differs_ms": max(differ) if differ else None,
                "differing_cells": len(differ),
                "max_numeric_score_error_cp": max((abs(x) for x in numeric), default=None),
                "score_deltas": deltas,
            }
        summary[bname] = per_pos
    out["summary"] = summary
    with open(os.path.join(OUT, "regimes.json"), "w") as f:
        json.dump(out, f, indent=2)
        f.write("\n")
    print(json.dumps(summary, indent=2))


main()
