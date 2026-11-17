#!/usr/bin/env python3
"""process_policy.py <exe> <outdir> [--settings PC20] [--games N] [--maxplies P] [--fens FILE]

THE PROCESS-POLICY EXCHANGE the coordinator asked for: my WARM policy (one engine process per game, table
carried move to move) against seat 15's COLD policy (a fresh process per move), on the same positions, same
clock, same settings. Reports median nodes per move and median wall for each, which separates table warmth
from position mix.

Design notes that matter for honesty:
  - ONE engine per move (cold) means `ucinewgame` cannot be relied on to clear the table (seat 10 measured
    that Clear Hash does not restore cold either), so the cold arm starts a NEW PROCESS for every move.
  - Both arms get `OwnBook false` hard-coded, Threads 1, Hash 16, the same PC20 block, the same clock logic
    (decrement by measured wall time, increment after the move), the same start FENs, and the same ply cap.
  - WALL IS REPORTED RAW **and** with Move Overhead (10 ms) shown beside it, because that omission is exactly
    what made my earlier figures incomparable with seat 15's. Nobody should have to guess which convention a
    number uses.
  - Median nodes per move is the machine-independent comparator: my earlier figure was 145,432 against
    seat 15's 263,746.
"""
import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import time

S14 = ["LmrQuietBase 93", "LmrQuietDivisor 205", "LmrNoisyBase 13", "LmrNoisyDivisor 333",
       "LmrHistoryDivisor 5643", "NullMoveBase 5", "LmpBase 8", "HistoryPruneMultiplier 2220",
       "HistoryBonusQuadratic 24", "HistoryBonusLinear 54", "HistoryBonusMax 2212",
       "SingularDepth 6", "IirDepth 2", "NonPawnCorrection true"]
PC20X = ["CuckooRep true", "HistRework 2", "TtPruneV2 true", "CorrHistV2 true",
         "MateAlphaGuard true", "OwnBook false" ]
OVERHEAD = 10  # the default; I never set it, and I report both conventions


class Missing(Exception):
    pass


class Engine:
    def __init__(self, exe, settings):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.s("uci")
        lines, ok = self.until(lambda x: x.strip() == "uciok")
        if not ok:
            raise Missing("no uciok")
        adv = {m.group(1) for m in (re.match(r"option name (.+?) type ", l) for l in lines) if m}
        for item in settings:
            name, _, val = item.rpartition(" ")
            if name not in adv:
                raise Missing("option %r not advertised" % name)
            self.s("setoption name %s value %s" % (name, val))
        self.s("ucinewgame"); self.s("isready")
        self.until(lambda x: x.strip() == "readyok")

    def s(self, line):
        self.p.stdin.write(line + "\n"); self.p.stdin.flush()

    def until(self, pred, tmo=120):
        t0 = time.monotonic(); out = []
        while time.monotonic() - t0 < tmo:
            ln = self.p.stdout.readline()
            if not ln:
                break
            y = ln.rstrip("\n"); out.append(y)
            if pred(y):
                return out, True
        return out, False

    def move(self, start_fen, moves_uci, wtime, btime, winc, binc, timeout=30):
        pos = ("position fen " + start_fen) if start_fen else "position startpos"
        if moves_uci:
            pos += " moves " + " ".join(moves_uci)
        self.s(pos); self.s("isready")
        if not self.until(lambda x: x.strip() == "readyok")[1]:
            raise Missing("no readyok")
        cmd = "go wtime %d btime %d winc %d binc %d" % (wtime, btime, winc, binc)
        t0 = time.monotonic()
        self.s(cmd)
        lines, ok = self.until(lambda x: x.startswith("bestmove"), tmo=timeout)
        wall = (time.monotonic() - t0) * 1000.0
        if not ok:
            return {"timeout": True, "wall_ms": wall, "bestmove": None}
        bm = next(l for l in lines if l.startswith("bestmove")).split()[1]
        infos = [l for l in lines if l.startswith("info depth")]
        # GUARD (S-W1): a search that published NO info line has no score, no node count and no nps.
        # Zero info lines is the end-of-input / early-close signature and has produced fabricated
        # "plausible" numbers for two seats. Abort the row instead of recording a None-laden result.
        if not infos:
            raise Missing("no 'info depth' line for this search (zero-info-line signature; row aborted)")
        last = infos[-1]
        n = re.search(r"nodes (\d+)", last)
        d = re.search(r"depth (\d+)", last)
        return {"timeout": False, "wall_ms": wall, "bestmove": bm,
                "nodes": int(n.group(1)) if n else None,
                "depth": int(d.group(1)) if d else None}

    def close(self):
        try:
            self.s("quit"); self.p.wait(timeout=15)
        except Exception:
            self.p.kill()


def play(exe, settings, start_fen, policy, wtime0, btime0, winc, binc, maxplies):
    """One game. policy='warm' keeps one process; policy='cold' starts a new one for every move."""
    moves, log = [], []
    w, b = wtime0, btime0
    engine = Engine(exe, settings) if policy == "warm" else None
    try:
        for ply in range(maxplies):
            white = (ply % 2 == 0)
            if policy == "cold":
                engine = Engine(exe, settings)
            r = engine.move(start_fen, moves, max(1, int(w)), max(1, int(b)), winc, binc)
            if policy == "cold":
                engine.close(); engine = None
            if r["timeout"] or r["bestmove"] in (None, "0000"):
                return {"ended": "TIMEOUT_OR_NO_MOVE", "ply": ply, "log": log,
                        "white_left": w, "black_left": b}
            if white:
                w = w - r["wall_ms"] + winc
            else:
                b = b - r["wall_ms"] + binc
            log.append({"ply": ply, "side": "w" if white else "b",
                        "wall_ms": round(r["wall_ms"], 1), "nodes": r["nodes"],
                        "depth": r["depth"], "move": r["bestmove"],
                        "white_left": round(w, 1), "black_left": round(b, 1)})
            moves.append(r["bestmove"])
            if w <= 0 or b <= 0:
                return {"ended": "FORFEIT", "ply": ply, "log": log,
                        "white_left": w, "black_left": b}
        return {"ended": "PLY_CAP", "ply": maxplies, "log": log,
                "white_left": w, "black_left": b}
    finally:
        if engine is not None:
            engine.close()


def stats(games):
    nodes = [r["nodes"] for g in games for r in g["log"] if r.get("nodes")]
    walls = [r["wall_ms"] for g in games for r in g["log"]]
    if not nodes:
        return {}
    return {"moves": len(walls),
            "median_nodes": int(statistics.median(nodes)),
            "mean_nodes": int(statistics.mean(nodes)),
            "min_nodes": min(nodes), "max_nodes": max(nodes),
            "median_wall_ms": round(statistics.median(walls), 1),
            "median_wall_minus_overhead_ms": round(statistics.median(walls) - OVERHEAD, 1),
            "net_drain_ms": round(statistics.median(walls) - OVERHEAD - 60, 1),
            "median_depth": statistics.median([r["depth"] for g in games for r in g["log"]
                                               if r.get("depth")]),
            "forfeits": sum(1 for g in games if g["ended"] == "FORFEIT")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe"); ap.add_argument("outdir")
    ap.add_argument("--settings", default="PC20", choices=["PC20", "S14", "none"])
    ap.add_argument("--games", type=int, default=2)
    ap.add_argument("--maxplies", type=int, default=120)
    ap.add_argument("--fens", default="")
    ap.add_argument("--policies", default="warm,cold")
    a = ap.parse_args()
    exe = os.path.realpath(a.exe)
    os.makedirs(a.outdir, exist_ok=True)
    settings = {"none": ["Hash 16", "Threads 1", "OwnBook false"],
                "S14": ["Hash 16", "Threads 1", "OwnBook false"] + S14,
                "PC20": ["Hash 16", "Threads 1", "OwnBook false"] + S14 + PC20X}[a.settings]
    starts = [l.strip() for l in open(a.fens) if l.strip()] if a.fens else [None]
    policies = [p.strip() for p in a.policies.split(",")]

    out = {"exe": exe, "settings": a.settings, "threads": 1, "ownbook": "false (hard-coded)",
           "move_overhead": OVERHEAD, "maxplies": a.maxplies, "games_per_cell": a.games,
           "sha256": subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0],
           "date_utc": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                      capture_output=True, text=True).stdout.strip(),
           "cells": {}}

    for policy in policies:
        for i, sf in enumerate(starts):
            games = [play(exe, settings, sf, policy, 6000, 6000, 60, 60, a.maxplies)
                     for _ in range(a.games)]
            key = "%s|start%d" % (policy, i)
            s = stats(games)
            s["start_fen"] = sf or "startpos"
            s["ended"] = [g["ended"] for g in games]
            s["games"] = games
            out["cells"][key] = s
            print("%-6s start%-2d %s: median nodes %-9s median wall %-7s (minus overhead %-7s) "
                  "drain %-7s depth %-3s moves %-4s ended %s"
                  % (policy, i, (sf or "startpos")[:14], f"{s.get('median_nodes'):,}",
                     s.get("median_wall_ms"), s.get("median_wall_minus_overhead_ms"),
                     s.get("net_drain_ms"), s.get("median_depth"), s.get("moves"), s["ended"]))

    with open(os.path.join(a.outdir, "process_policy_%s.json" % a.settings), "w") as f:
        json.dump(out, f, indent=2)

    print("\n-- the comparison the exchange is for (same start, both policies) --")
    for i in range(len(starts)):
        w = out["cells"].get("warm|start%d" % i, {})
        c = out["cells"].get("cold|start%d" % i, {})
        if w and c:
            print("start%d: warm median nodes %s vs cold %s  -> warm is %+.0f %% of cold"
                  % (i, f"{w['median_nodes']:,}", f"{c['median_nodes']:,}",
                     100.0 * (w["median_nodes"] - c["median_nodes"]) / c["median_nodes"]))
            print("         warm median wall %s ms vs cold %s ms"
                  % (w["median_wall_ms"], c["median_wall_ms"]))


if __name__ == "__main__":
    main()
