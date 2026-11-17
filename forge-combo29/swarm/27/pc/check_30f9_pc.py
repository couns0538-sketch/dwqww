#!/usr/bin/env python3
"""check_30f9_pc.py <exe> <outdir> [--settings PC20|S14]

Seat 30's 30-F9: the node cost of a `go depth 10` spikes at halfmove 91 and collapses at 99, because the
engine spends nodes proving a draw the fifty-move rule awards anyway. Measured on the BASE tree:
  halfmove 90 -> 946,042 nodes; 91 -> 13,791,896; 99 -> 200.

The PC build REPAIRS the drawn root (FORGE_FIX_ROOT_DRAWN: a drawn root is now searched like any other),
so the question worth answering is: does the same counter sweep still spike on the PC build, and if so by
how much? A spike that survives means the fix changed WHICH moves are considered without changing how the
horizon is searched -- useful for Opus either way.

One position, one counter changed at a time. Fresh process per row, Threads 1, one `go` per process.
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
# a quiet position where the fifty-move counter can be set freely (no captures/pawns needed to reach it)
# A QUIET position with no forced mate and enough pieces that depth 10 is real work. My first template
# ("6k1/5ppp/.../R5K1") had Ra8# available, so every clock found mate 1 in 210 nodes and the sweep tested
# nothing about the horizon -- caught by reading the output rather than trusting that it had run.
TEMPLATE = "r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - %d 8"
CLOCKS = [88, 89, 90, 91, 92, 95, 98, 99, 100]


class Missing(Exception):
    pass


def run(exe, settings, clock, depth=10):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def s(x):
        p.stdin.write(x + "\n"); p.stdin.flush()

    def until(pred, tmo=600):
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
        _, ok = until(lambda x: x.strip() == "readyok")
        if not ok:
            raise Missing("no readyok")
        s("position fen " + (TEMPLATE % clock)); s("isready")
        until(lambda x: x.strip() == "readyok")
        t0 = time.monotonic()
        s("go depth %d" % depth)
        lines, ok = until(lambda x: x.startswith("bestmove"))
        wall = time.monotonic() - t0
        if not ok:
            raise Missing("no bestmove at clock %d" % clock)
        infos = [l for l in lines if l.startswith("info depth %d " % depth)]
        if not infos:
            raise Missing("no 'info depth %d' line at clock %d (19-F12 signature)" % (depth, clock))
        last = infos[-1]
        n = re.search(r"nodes (\d+)", last)
        sc = re.search(r"score (cp|mate) (-?\d+)", last)
        if not n or not sc:
            raise Missing("info line lacks nodes/score at clock %d: %r" % (clock, last))
        bm = next(l for l in lines if l.startswith("bestmove")).split()[1]
        return {"clock": clock, "nodes": int(n.group(1)), "score": (sc.group(1), int(sc.group(2))),
                "bestmove": bm, "wall_ms": round(wall * 1000, 1),
                "n_info": len([l for l in lines if l.startswith("info depth")])}
    finally:
        try:
            s("quit"); p.wait(timeout=20)
        except Exception:
            p.kill()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe"); ap.add_argument("outdir")
    ap.add_argument("--settings", default="PC20", choices=["PC20", "S14", "none"])
    ap.add_argument("--label", default="")
    a = ap.parse_args()
    exe = os.path.realpath(a.exe)
    os.makedirs(a.outdir, exist_ok=True)
    settings = {"none": ["Hash 16", "Threads 1"],
                "S14": ["Hash 16", "Threads 1"] + S14,
                "PC20": ["Hash 16", "Threads 1"] + S14 + PC20X}[a.settings]

    rows = [run(exe, settings, c) for c in CLOCKS]
    out = {"exe": exe, "settings": a.settings, "threads": 1, "label": a.label,
           "sha256": subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0],
           "date_utc": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                      capture_output=True, text=True).stdout.strip(),
           "template": TEMPLATE, "rows": rows}
    tag = a.label or a.settings
    with open(os.path.join(a.outdir, "check_30f9_%s.json" % tag), "w") as f:
        json.dump(out, f, indent=2)
    print("%-5s %-12s %-9s %-8s %-8s" % ("clock", "nodes", "score", "move", "ms"))
    for r in rows:
        print("%-5d %-12d %-9s %-8s %-8s" % (r["clock"], r["nodes"],
                                             "%s %d" % r["score"], r["bestmove"], r["wall_ms"]))
    ns = {r["clock"]: r["nodes"] for r in rows}
    peak = max(rows, key=lambda r: r["nodes"])
    print("\npeak at halfmove %d: %d nodes (%.1f ms)" % (peak["clock"], peak["nodes"], peak["wall_ms"]))
    if 90 in ns and ns[90]:
        print("ratio peak / halfmove-90: %.1fx" % (peak["nodes"] / ns[90]))


if __name__ == "__main__":
    main()
