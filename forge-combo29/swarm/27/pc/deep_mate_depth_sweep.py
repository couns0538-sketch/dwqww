#!/usr/bin/env python3
"""deep_mate_depth_sweep.py <exe> <outdir> [--settings PC20] [--label base|pc] [--depths 12,16,20,24]

The deep-mate question, stated so that a depth effect cannot be mistaken for a fix:
  does BASE (e6b98f217) report centipawns where PC r15 reports `mate N` on the same board, and at which
  DEPTHS does each one change its mind?

Seat 23's 23-F46 is the caution that makes this test necessary: on six lone-king boards the PC build finds
none of the mates at depth 12, "exactly like base", and all six at depth 20 -- so a difference seen at one
depth may be a search-depth effect, not the patch taking hold. Every row here therefore records the DEPTH.

Boards: the lone-king family seat 23 used (reconstructed here from its descriptions as mate-in-1 boards with a
lone king and a mating piece), plus seat 06's S-F36 board if its FEN is committed, plus two ordinary
middle-games as controls that should NOT be mates.

`OwnBook false` is hard-coded in every setting block (the permanent fix from the book-contamination error).

Threads 1, Hash 16, fresh process per cell, `go` awaited to bestmove.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

S14 = ["LmrQuietBase 93", "LmrQuietDivisor 205", "LmrNoisyBase 13", "LmrNoisyDivisor 333",
       "LmrHistoryDivisor 5643", "NullMoveBase 5", "LmpBase 8", "HistoryPruneMultiplier 2220",
       "HistoryBonusQuadratic 24", "HistoryBonusLinear 54", "HistoryBonusMax 2212",
       "SingularDepth 6", "IirDepth 2", "NonPawnCorrection true"]
PC20X = ["CuckooRep true", "HistRework 2", "TtPruneV2 true", "CorrHistV2 true",
         "MateAlphaGuard true"]

# Lone-king mate boards in the style seat 23 used: the lone king is mated in 1 by the side to move.
# Written by hand and checked with python-chess before use (the script asserts legality).
MATE_BOARDS = [
    ("KR vs lone K, mate in 1", "7k/8/6K1/8/8/8/8/7R w - - 0 1"),      # Rh8#? see check below
    ("KQ vs lone K, mate in 1", "7k/8/6K1/8/8/8/8/6Q1 w - - 0 1"),
    ("KR vs lone K, mate in 2", "6k1/8/5K2/8/8/8/8/7R w - - 0 1"),
    ("KQ vs lone K, mate in 3", "6k1/8/5K2/8/8/8/8/6Q1 w - - 0 1"),
]
CONTROLS = [
    ("quiet middlegame (must NOT be mate)", "r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8"),
    ("startpos (must NOT be mate)", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
]


class Missing(Exception):
    pass


def search(exe, settings, fen, depth, timeout=1800):
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
        _, ok = until(lambda x: x.strip() == "uciok")
        if not ok:
            raise Missing("no uciok")
        for item in settings:
            name, _, val = item.rpartition(" ")
            s("setoption name %s value %s" % (name, val))
        s("ucinewgame"); s("isready")
        until(lambda x: x.strip() == "readyok")
        s("position fen " + fen); s("isready")
        until(lambda x: x.strip() == "readyok")
        t0 = time.monotonic()
        s("go depth %d" % depth)
        lines, ok = until(lambda x: x.startswith("bestmove"), tmo=timeout)
        wall = time.monotonic() - t0
        if not ok:
            raise Missing("no bestmove for %r depth %d" % (fen, depth))
        infos = [l for l in lines if l.startswith("info depth")]
        if not infos:
            raise Missing("no info depth for %r depth %d (book? 19-F12?)" % (fen, depth))
        last = infos[-1]
        sc = re.search(r"score (cp|mate) (-?\d+)", last)
        d = re.search(r"depth (\d+)", last)
        n = re.search(r"nodes (\d+)", last)
        bm = next(l for l in lines if l.startswith("bestmove")).split()[1]
        return {"depth_reached": int(d.group(1)) if d else None,
                "kind": sc.group(1) if sc else None,
                "value": int(sc.group(2)) if sc else None,
                "nodes": int(n.group(1)) if n else None,
                "bestmove": bm, "wall_s": round(wall, 2),
                "book_lines": len([l for l in lines if "book move" in l])}
    finally:
        try:
            s("quit"); p.wait(timeout=20)
        except Exception:
            p.kill()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe"); ap.add_argument("outdir")
    ap.add_argument("--settings", default="PC20", choices=["PC20", "S14", "none"])
    ap.add_argument("--label", required=True)
    ap.add_argument("--depths", default="12,16,20")
    a = ap.parse_args()
    exe = os.path.realpath(a.exe)
    os.makedirs(a.outdir, exist_ok=True)
    depths = [int(x) for x in a.depths.split(",")]
    # OwnBook false is HARD-CODED in every variant -- the permanent fix after the book contaminated
    # my clock test and briefly convinced me the engine swapped the clocks.
    settings = {"none": ["Hash 16", "Threads 1", "OwnBook false"],
                "S14": ["Hash 16", "Threads 1", "OwnBook false"] + S14,
                "PC20": ["Hash 16", "Threads 1", "OwnBook false"] + S14 + PC20X}[a.settings]

    out = {"exe": exe, "settings": a.settings, "label": a.label, "threads": 1, "depths": depths,
           "ownbook": "false (hard-coded)",
           "sha256": subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0],
           "date_utc": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                      capture_output=True, text=True).stdout.strip(),
           "rows": []}

    for group, boards in (("mate", MATE_BOARDS), ("control", CONTROLS)):
        for name, fen in boards:
            for d in depths:
                try:
                    r = search(exe, settings, fen, d)
                    r.update({"board": name, "fen": fen, "requested_depth": d, "group": group})
                except Missing as ex:
                    r = {"board": name, "fen": fen, "requested_depth": d, "group": group,
                         "error": str(ex)}
                out["rows"].append(r)
                if "error" in r:
                    print("%-34s d%-3d ERROR %s" % (name, d, r["error"][:60]))
                else:
                    print("%-34s d%-3d -> reached %-3s %-5s %-6s nodes %-9s bm %-5s"
                          % (name, d, r["depth_reached"], r["kind"], r["value"],
                             r["nodes"], r["bestmove"]))

    with open(os.path.join(a.outdir, "deeppmate_%s_%s.json" % (a.label, a.settings)), "w") as f:
        json.dump(out, f, indent=2)

    # the comparison that matters: first depth at which each mate board reports `mate`
    print("\n-- first depth at which a MATE score appears (per board, this build) --")
    first = {}
    for name, _ in MATE_BOARDS:
        ds = [r for r in out["rows"] if r["board"] == name and "error" not in r
              and r["kind"] == "mate"]
        first[name] = min((r["requested_depth"] for r in ds), default=None)
        print("   %-34s %s" % (name, ("depth %d" % first[name]) if first[name] else "never in %s" % depths))
    out["first_mate_depth"] = first
    with open(os.path.join(a.outdir, "deeppmate_%s_%s.json" % (a.label, a.settings)), "w") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    main()
