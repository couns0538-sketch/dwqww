#!/usr/bin/env python3
"""f2_depth_ablation.py <exe> <outdir>

Names the term behind seat 10's depth sign flip (10-F18): `searchmoves e2e4` vs unrestricted gives
cp +10/-7/-4/-4 at depths 8/10/12/14. A term that DEPENDS ON DEPTH and CANNOT SEE THE RESTRICTION.

Hypothesis under test: the ASPIRATION WINDOW. Each iteration >= 4 uses
    alpha = score - AspirationDelta, beta = score + AspirationDelta      (src/search.cpp:2400-2410)
where `score` is the PREVIOUS iteration's root score. A restricted root reaches a different previous
score, so it is handed a differently-centred window; whether that window clips the true value high or
low depends on the size and direction of the previous error -- which is exactly why the sign flips with
depth. The aspiration code itself reads `depth` and `score`, and never reads `root_restricted_`: it
cannot see the restriction, it only inherits a different number.

Test: run the same sweep with a WIDE window. `AspirationDelta` is advertised min 4 max 200, so
     AspirationDelta 18  (default) -> windows of +-18 cp around the previous score
     AspirationDelta 200           -> windows of +-200 cp, i.e. effectively never clipping
If the gap collapses at delta 200, the aspiration feedback is the causing term. If it survives, it is not.
Every cell is a fresh process, paced, and asserts its `info depth N` line.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

DEPTHS = [8, 10, 12, 14]
DELTAS = [18, 200]


class Missing(Exception):
    pass


class Engine:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(self, s):
        self.p.stdin.write(s + "\n"); self.p.stdin.flush()

    def until(self, pred, timeout=240):
        t0 = time.monotonic(); out = []
        while time.monotonic() - t0 < timeout:
            ln = self.p.stdout.readline()
            if not ln:
                break
            s = ln.rstrip("\n"); out.append(s)
            if pred(s):
                return out, True
        return out, False

    def ready(self):
        self.send("isready")
        _, ok = self.until(lambda s: s.strip() == "readyok")
        if not ok:
            raise Missing("no readyok")

    def boot(self, delta):
        self.send("uci")
        _, ok = self.until(lambda s: s.strip() == "uciok")
        if not ok:
            raise Missing("no uciok")
        self.send("setoption name Hash value 16"); self.ready()
        self.send("setoption name Threads value 1"); self.ready()
        self.send("setoption name AspirationDelta value %d" % delta); self.ready()
        self.send("ucinewgame"); self.ready()

    def go(self, depth, restricted):
        self.send("position startpos"); self.ready()
        line = "go depth %d" % depth + (" searchmoves e2e4" if restricted else "")
        self.send(line)
        lines, ok = self.until(lambda s: s.startswith("bestmove"))
        if not ok:
            raise Missing("no bestmove for %r" % line)
        infos = [l for l in lines if l.startswith("info depth %d " % depth)]
        if not infos:
            raise Missing("no 'info depth %d' line for %r (19-F12 signature)" % (depth, line))
        last = infos[-1]
        n = re.search(r"nodes (\d+)", last)
        sc = re.search(r"score (cp|mate) (-?\d+)", last)
        if not n or not sc:
            raise Missing("info line lacks nodes/score: %r" % last)
        bm = next(l for l in lines if l.startswith("bestmove")).split()[1]
        return {"score": int(sc.group(2)), "nodes": int(n.group(1)), "bestmove": bm,
                "last": last}

    def close(self):
        try:
            self.send("quit"); self.p.wait(timeout=20)
        except Exception:
            self.p.kill()


def cell(exe, delta, depth, restricted):
    e = Engine(exe)
    try:
        e.boot(delta)
        return e.go(depth, restricted)
    finally:
        e.close()


def main():
    exe = os.path.realpath(sys.argv[1]); outdir = sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    rows = []
    for delta in DELTAS:
        for depth in DEPTHS:
            u = cell(exe, delta, depth, False)
            r = cell(exe, delta, depth, True)
            rows.append({"delta": delta, "depth": depth,
                         "unrestricted": u, "restricted": r,
                         "gap": u["score"] - r["score"]})
    out = {"exe": exe,
           "sha256": subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0],
           "date_utc": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                      capture_output=True, text=True).stdout.strip(),
           "rows": rows}
    with open(os.path.join(outdir, "result.json"), "w") as f:
        json.dump(out, f, indent=2)
    with open(os.path.join(outdir, "SUMMARY.txt"), "w") as f:
        f.write("exe %s\nsha %s\ndate %s\nstartpos, Threads 1, Hash 16, default tuning, "
                "`searchmoves e2e4` vs unrestricted\n\n" % (exe, out["sha256"], out["date_utc"]))
        for delta in DELTAS:
            f.write("## AspirationDelta %d\n\n" % delta)
            f.write("| depth | unrestricted | restricted | gap (plain-restricted) | nodes plain / restr |\n")
            f.write("|---|---|---|---|---|\n")
            for r in rows:
                if r["delta"] != delta:
                    continue
                f.write("| %d | cp %d (%s) | cp %d (%s) | %+d | %d / %d |\n" % (
                    r["depth"], r["unrestricted"]["score"], r["unrestricted"]["bestmove"],
                    r["restricted"]["score"], r["restricted"]["bestmove"], r["gap"],
                    r["unrestricted"]["nodes"], r["restricted"]["nodes"]))
            gaps = [r["gap"] for r in rows if r["delta"] == delta]
            f.write("\n  gaps: %s   max |gap| = %d\n\n" % (gaps, max(abs(g) for g in gaps)))
        g18 = [r["gap"] for r in rows if r["delta"] == 18]
        g200 = [r["gap"] for r in rows if r["delta"] == 200]
        f.write("verdict:\n")
        if max(abs(g) for g in g200) == 0:
            f.write("  gaps VANISH at AspirationDelta 200 -> the aspiration feedback is the causing term\n")
        elif max(abs(g) for g in g200) < max(abs(g) for g in g18):
            f.write("  gaps SHRINK but do not vanish at delta 200 (%s vs %s) -> aspiration is ONE term,\n"
                    "  not the only one\n" % (g200, g18))
        else:
            f.write("  gaps do NOT shrink at delta 200 (%s vs %s) -> aspiration is NOT the term\n"
                    % (g200, g18))
    print(open(os.path.join(outdir, "SUMMARY.txt")).read())


if __name__ == "__main__":
    main()
