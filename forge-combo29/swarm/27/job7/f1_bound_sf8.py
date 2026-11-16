#!/usr/bin/env python3
"""f1_bound_sf8.py <exe> <outdir>

BOUNDS S-F8 (a `searchmoves`-restricted root reports a different score than the unrestricted search of
the same position) without chasing the cause. The engine advertises `IirDepth` min 1 max 20
(include/forge/search.hpp / the uci answer), and IIR only fires when `depth >= tune::IirDepth`
(src/search.cpp:1784). At depth 12 that means:

    IirDepth 4  (default) -> IIR CAN fire at the restricted root
    IirDepth 20           -> IIR CANNOT fire at depth 12

So running the same three go-lines at both settings, on the UNMODIFIED build, answers:
  - does the score difference exist with IIR inactive? (if it vanishes, IIR is the whole cause)
  - how much of the difference does IIR account for? (the gap that remains is the unidentified part)

Each case is a fresh process, paced (waits for bestmove), and every parse asserts its line.
"""
import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import time

S14 = [l for l in """setoption name LmrQuietBase value 93
setoption name LmrQuietDivisor value 205
setoption name LmrNoisyBase value 13
setoption name LmrNoisyDivisor value 333
setoption name LmrHistoryDivisor value 5643
setoption name NullMoveBase value 5
setoption name LmpBase value 8
setoption name HistoryPruneMultiplier value 2220
setoption name HistoryBonusQuadratic value 24
setoption name HistoryBonusLinear value 54
setoption name HistoryBonusMax value 2212
setoption name SingularDepth value 6
setoption name IirDepth value 2
setoption name NonPawnCorrection value true""".splitlines() if l.strip()]
# IirDepth is overridden per case below, so drop it from the fixed block.
S14 = [l for l in S14 if "IirDepth" not in l]


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

    def boot(self):
        self.send("uci")
        lines, ok = self.until(lambda s: s.strip() == "uciok")
        if not ok:
            raise Missing("no uciok")

    def setopt(self, name, value):
        self.send("setoption name %s value %s" % (name, value))
        self.ready()

    def go(self, depth, searchmoves):
        self.send("position startpos")
        self.ready()
        line = "go depth %d" % depth
        if searchmoves:
            line += " searchmoves " + " ".join(searchmoves)
        self.send(line)
        lines, ok = self.until(lambda s: s.startswith("bestmove"))
        if not ok:
            raise Missing("no bestmove for %r" % line)
        infos = [l for l in lines if l.startswith("info depth %d " % depth)]
        if not infos:
            raise Missing("no 'info depth %d' line for %r -- refusing to guess (19-F12 signature)"
                          % (depth, line))
        last = infos[-1]
        n = re.search(r"nodes (\d+)", last)
        sc = re.search(r"score (cp|mate) (-?\d+)", last)
        if not n or not sc:
            raise Missing("info line lacks nodes or score: %r" % last)
        bm = next(l for l in lines if l.startswith("bestmove")).split()[1]
        return {"go": line, "score": (sc.group(1), int(sc.group(2))),
                "nodes": int(n.group(1)), "bestmove": bm}

    def close(self):
        try:
            self.send("quit"); self.p.wait(timeout=20)
        except Exception:
            self.p.kill()


CASES = [([], "plain"), (["e2e4"], "e2e4"), (["e2e4", "d2d4"], "e2e4 d2d4")]
IIR_SETTINGS = [2, 4, 20]       # 2 = the S14 value; 4 = default; 20 = IIR cannot fire at depth 12
DEPTH = 12


def run_once(exe, iir, searchmoves):
    e = Engine(exe)
    try:
        e.boot()
        e.setopt("Hash", 16)
        e.setopt("Threads", 1)
        for line in S14:
            e.send(line)
        e.ready()
        e.setopt("IirDepth", iir)
        e.setopt("Clear Hash", "") if False else None   # (button, not needed: fresh process)
        e.send("ucinewgame"); e.ready()
        return e.go(DEPTH, searchmoves)
    finally:
        e.close()


def main():
    exe = os.path.realpath(sys.argv[1]); outdir = sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    table = {}
    for iir in IIR_SETTINGS:
        for sm, label in CASES:
            reps = [run_once(exe, iir, sm) for _ in range(3)]
            scores = {r["score"][1] for r in reps}
            nodes = {r["nodes"] for r in reps}
            table["iir%d/%s" % (iir, label)] = {
                "iir_depth": iir, "case": label, "reps": reps,
                "score_set": sorted(scores), "node_set": sorted(nodes),
                "deterministic": len(scores) == 1 and len(nodes) == 1,
                "score": reps[-1]["score"], "nodes": reps[-1]["nodes"],
                "bestmove": reps[-1]["bestmove"]}

    out = {"exe": exe,
           "sha256": subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0],
           "date_utc": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                      capture_output=True, text=True).stdout.strip(),
           "depth": DEPTH, "iir_settings": IIR_SETTINGS, "table": table}

    # the gaps that answer the question
    def get(iir, label):
        return table["iir%d/%s" % (iir, label)]
    plain4, e4_4, e4d4_4 = get(4, "plain"), get(4, "e2e4"), get(4, "e2e4 d2d4")
    plain20, e4_20 = get(20, "plain"), get(20, "e2e4")
    plain2, e4_2 = get(2, "plain"), get(2, "e2e4")
    out["gaps"] = {
        "iir2_plain_minus_e2e4": plain2["score"][1] - e4_2["score"][1],
        "iir2_plain_nodes": plain2["nodes"],
        "iir2_e2e4_nodes": e4_2["nodes"],
        "iir4_plain_minus_e2e4": plain4["score"][1] - e4_4["score"][1],
        "iir20_plain_minus_e2e4": plain20["score"][1] - e4_20["score"][1],
        "iir4_plain_nodes": plain4["nodes"],
        "iir20_plain_nodes": plain20["nodes"],
        "iir4_e2e4_nodes": e4_4["nodes"],
        "iir20_e2e4_nodes": e4_20["nodes"],
    }
    with open(os.path.join(outdir, "result.json"), "w") as f:
        json.dump(out, f, indent=2)

    with open(os.path.join(outdir, "SUMMARY.txt"), "w") as f:
        f.write("exe %s\nsha %s\ndepth %d, startpos, S14, Threads 1, Hash 16, 3 reps per cell\ndate %s\n\n"
                % (exe, out["sha256"], DEPTH, out["date_utc"]))
        f.write("| IirDepth | go line | score | nodes | bestmove | 3 reps identical |\n")
        f.write("|---|---|---|---|---|---|\n")
        for iir in IIR_SETTINGS:
            for _, label in CASES:
                r = table["iir%d/%s" % (iir, label)]
                f.write("| %d | `%s` | %s %s | %s | %s | %s |\n" % (
                    iir, r["reps"][0]["go"], r["score"][0], r["score"][1], r["nodes"],
                    r["bestmove"], r["deterministic"]))
        g = out["gaps"]
        f.write("\nscore gap plain - searchmoves(e2e4):\n")
        f.write("  IirDepth 2  (S14, IIR active):          %+d cp   (%s vs %s nodes)\n"
                % (g["iir2_plain_minus_e2e4"], g["iir2_plain_nodes"], g["iir2_e2e4_nodes"]))
        f.write("  IirDepth 4  (IIR active at depth %d): %+d cp   (%s vs %s nodes)\n"
                % (DEPTH, g["iir4_plain_minus_e2e4"], g["iir4_plain_nodes"], g["iir4_e2e4_nodes"]))
        f.write("  IirDepth 20 (IIR inactive at depth %d): %+d cp   (%s vs %s nodes)\n"
                % (DEPTH, g["iir20_plain_minus_e2e4"], g["iir20_plain_nodes"], g["iir20_e2e4_nodes"]))
        f.write("\nverdict:\n")
        if g["iir20_plain_minus_e2e4"] == 0:
            f.write("  the score difference VANISHES with IIR inactive -> IIR is the whole cause\n")
        else:
            f.write("  the score difference SURVIVES with IIR inactive (%+d cp) -> IIR is not the whole\n"
                    "  cause; there is at least one more, unidentified, and it is bounded by this number\n"
                    % g["iir20_plain_minus_e2e4"])
    print(open(os.path.join(outdir, "SUMMARY.txt")).read())


if __name__ == "__main__":
    main()
