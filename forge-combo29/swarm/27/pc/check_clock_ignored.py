#!/usr/bin/env python3
"""check_clock_ignored.py <exe> <outdir> [--settings PC20]

WHAT I FOUND BY ACCIDENT, then chased: on one long-game position, `go wtime 0` (and 1, 3, 10, 50, 200, 1000,
3000) all search to the same 20 plies / 286,156 nodes / ~124 ms, while `go movetime 5` on the same position
correctly stops at depth 1 and `go wtime 0` on startpos correctly fires the emergency path (0 info lines,
instant move). So the clock is being IGNORED on some positions.

This script measures the scope: for a list of positions, at `go wtime 0 btime 5000`, does the engine
  (a) answer with 0 info lines instantly (the documented emergency path), or
  (b) search normally, i.e. IGNORE the empty clock?
and how many nodes it spends. A position where (b) happens is the defect.

I also run the same set at wtime 3000 so I can report whether the ignoring position searches for the SAME
node count at both clocks (clock fully ignored) or only overspends at zero.

Every case: fresh process, Threads 1, PC20, PC build.
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
         "MateAlphaGuard true", "OwnBook false"]

# The position that exposed it, the position it came from, and a set of ordinary middlegames for scope.
POSITIONS = [
    ("found: long game endgame", "2N3k1/3pn1p1/8/2R1P1KP/7P/8/8/5r2 b - - 18 55"),
    ("startpos", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    ("O-mid1", "rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4"),
    ("O-mid2", "rnbqkbnr/pp2pppp/2p5/8/2pP4/4P3/PP3PPP/RNBQKBNR w KQkq - 0 4"),
    ("G-mid", "r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8"),
    ("kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"),
    ("K+R vs K", "1K6/8/8/3R4/8/8/8/k7 w - - 0 1"),
    ("bare kings", "4k3/8/8/8/8/8/8/4K3 w - - 0 1"),
]


class Missing(Exception):
    pass


def go(exe, settings, fen, cmd, timeout=180):
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
        s(cmd)
        lines, ok = until(lambda x: x.startswith("bestmove"), tmo=timeout)
        wall = (time.monotonic() - t0) * 1000.0
        if not ok:
            raise Missing("no bestmove for %r %r" % (fen, cmd))
        infos = [l for l in lines if l.startswith("info depth")]
        # GUARD (S-W1): a search that published NO info line has no score, no node count and no nps.
        # Zero info lines is the end-of-input / early-close signature and has produced fabricated
        # "plausible" numbers for two seats. Abort the row instead of recording a None-laden result.
        if not infos:
            raise Missing("no 'info depth' line for this search (zero-info-line signature; row aborted)")
        last = infos[-1]
        n = re.search(r"nodes (\d+)", last)
        d = re.search(r"depth (\d+)", last)
        bm = next(l for l in lines if l.startswith("bestmove")).split()[1]
        return {"cmd": cmd, "n_info": len(infos), "depth": int(d.group(1)) if d else None,
                "nodes": int(n.group(1)) if n else None, "bestmove": bm,
                "wall_ms": round(wall, 1)}
    finally:
        try:
            s("quit"); p.wait(timeout=15)
        except Exception:
            p.kill()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe"); ap.add_argument("outdir")
    ap.add_argument("--settings", default="PC20", choices=["PC20", "S14", "none"])
    a = ap.parse_args()
    exe = os.path.realpath(a.exe)
    os.makedirs(a.outdir, exist_ok=True)
    settings = {"none": ["Hash 16", "Threads 1", "OwnBook false"],
                "S14": ["Hash 16", "Threads 1", "OwnBook false"] + S14,
                "PC20": ["Hash 16", "Threads 1"] + S14 + PC20X}[a.settings]

    out = {"exe": exe, "settings": a.settings, "threads": 1,
           "sha256": subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0],
           "date_utc": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                      capture_output=True, text=True).stdout.strip(),
           "rows": []}
    ignored = []
    for name, fen in POSITIONS:
        zero = go(exe, settings, fen, "go wtime 0 btime 5000")
        healthy = go(exe, settings, fen, "go wtime 3000 btime 5000")
        mv = go(exe, settings, fen, "go movetime 5")
        # the emergency path is "0 info lines": anything searched at wtime 0 is the clock being ignored
        # CORRECTED CRITERION. My first version used `n_info > 0`, which flagged every position --
        # including the ones behaving correctly. The documented emergency path at an empty clock is
        # "answer at once with at most a depth-1 search" (26 nodes at startpos), so ONE info line at
        # depth 1 is CORRECT. What is wrong is searching DEEPER than the emergency allowance, i.e. a
        # depth of 2 or more at wtime 0, or a node count far above a depth-1 search.
        ign = (zero["depth"] is not None and zero["depth"] > 1)
        same_as_healthy = (zero["nodes"] == healthy["nodes"] and zero["depth"] == healthy["depth"])
        row = {"position": name, "fen": fen, "wtime0": zero, "wtime3000": healthy,
               "movetime5": mv, "clock_ignored_at_zero": ign,
               "same_nodes_as_healthy": same_as_healthy}
        out["rows"].append(row)
        if ign:
            ignored.append(name)
        print("%-26s wtime0: info %-2s depth %-3s nodes %-7s | wtime3000: depth %-3s nodes %-7s | "
              "same=%-5s | movetime5: info %-2s depth %-3s  %s"
              % (name, zero["n_info"], zero["depth"], zero["nodes"], healthy["depth"],
                 healthy["nodes"], same_as_healthy, mv["n_info"], mv["depth"],
                 "CLOCK IGNORED" if ign else "ok (emergency path: depth<=1)"))

    out["summary"] = {"positions": len(POSITIONS), "clock_ignored_at_zero": ignored,
                      "n_ignored": len(ignored)}
    with open(os.path.join(a.outdir, "check_clock_ignored.json"), "w") as f:
        json.dump(out, f, indent=2)
    print("\nclock ignored at wtime 0 on %d of %d positions: %s"
          % (len(ignored), len(POSITIONS), ignored if ignored else "none"))


if __name__ == "__main__":
    main()
