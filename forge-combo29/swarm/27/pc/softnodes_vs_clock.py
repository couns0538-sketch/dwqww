#!/usr/bin/env python3
"""softnodes_vs_clock.py <exe> <outdir> [--settings PC20]

The PC's self-play uses `go softnodes 2000`; its matches use a 6 s + 0.06 clock. Nobody has crossed them:
what happens when a `softnodes` budget is sent TOGETHER with a clock, which is what a self-play loop that
also keeps time would do? Three questions with exact answers:

  1. When both are present, WHICH limit stops the search? (the smaller of the two, or one overrides the other)
  2. Is the result deterministic run to run at Threads 1? (it must be, or self-play labels are not reproducible)
  3. Does the engine's own `info string softnodes` line report a node count that matches the last info line?

Method: for each of three positions, run four commands on fresh processes:
    go softnodes 2000                      (budget alone)
    go wtime 6000 btime 6000 winc 60 binc 60        (clock alone)
    go softnodes 2000 wtime 6000 btime 6000 winc 60 binc 60   (both)
    go softnodes 400000 wtime 10 btime 10 winc 0 binc 0       (budget huge, clock nearly empty)
and compare reported nodes, depth, bestmove. That last case is the discriminator: if the clock is honoured at
all, a 10 ms clock must cut the huge budget short.

OwnBook false hard-coded, Threads 1, Hash 16, fresh process per row.
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
         "MateAlphaGuard true", "OwnBook value false" ]

POSITIONS = [
    ("O-mid1", "rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4"),
    ("G-mid", "r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8"),
    ("kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"),
]
COMMANDS = [
    ("budget only", "go softnodes 2000"),
    ("clock only", "go wtime 6000 btime 6000 winc 60 binc 60"),
    ("both", "go softnodes 2000 wtime 6000 btime 6000 winc 60 binc 60"),
    ("huge budget + empty clock", "go softnodes 400000 wtime 10 btime 10 winc 0 binc 0"),
]


class Missing(Exception):
    pass


def run(exe, settings, fen, cmd, timeout=300):
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
            raise Missing("no bestmove for %r" % cmd)
        infos = [l for l in lines if l.startswith("info depth")]
        if not infos:
            raise Missing("no info depth (%r)" % cmd)
        last = infos[-1]
        n = re.search(r"nodes (\d+)", last)
        d = re.search(r"depth (\d+)", last)
        sc = re.search(r"score (cp|mate) (-?\d+)", last)
        soft = [l for l in lines if "info string softnodes" in l]
        softn = None
        if soft:
            m = re.search(r"softnodes nodes (\d+)", soft[-1])
            if m:
                softn = int(m.group(1))
        bm = next(l for l in lines if l.startswith("bestmove")).split()[1]
        return {"cmd": cmd, "depth": int(d.group(1)) if d else None,
                "nodes": int(n.group(1)) if n else None, "softnodes_reported": softn,
                "score": (sc.group(1), int(sc.group(2))) if sc else None,
                "bestmove": bm, "n_info": len(infos), "wall_ms": round(wall, 1),
                "softnodes_line_present": bool(soft)}
    finally:
        try:
            s("quit"); p.wait(timeout=20)
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
                "PC20": ["Hash 16", "Threads 1", "OwnBook false"] + S14 + PC20X}[a.settings]

    out = {"exe": exe, "settings": a.settings, "threads": 1, "ownbook": "false",
           "sha256": subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0],
           "date_utc": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                      capture_output=True, text=True).stdout.strip(),
           "rows": []}
    for name, fen in POSITIONS:
        print("\n== %s" % name)
        for label, cmd in COMMANDS:
            r1 = run(exe, settings, fen, cmd)
            r2 = run(exe, settings, fen, cmd)
            det = (r1["nodes"] == r2["nodes"] and r1["depth"] == r2["depth"]
                   and r1["bestmove"] == r2["bestmove"] and r1["score"] == r2["score"])
            r1.update({"position": name, "fen": fen, "label": label,
                       "deterministic": det, "repeat": r2})
            out["rows"].append(r1)
            print("   %-26s depth %-3s nodes %-8s bm %-5s wall %7.1f ms  softline %-5s det=%s"
                  % (label, r1["depth"], f"{r1['nodes']:,}" if r1['nodes'] else "-",
                     r1["bestmove"], r1["wall_ms"], r1["softnodes_line_present"], det))

    with open(os.path.join(a.outdir, "softnodes_vs_clock.json"), "w") as f:
        json.dump(out, f, indent=2)

    # the discriminator, printed plainly
    print("\n-- which limit wins when both are present? --")
    for name, _ in POSITIONS:
        rows = {r["label"]: r for r in out["rows"] if r["position"] == name}
        b, c, both = rows["budget only"], rows["clock only"], rows["both"]
        h = rows["huge budget + empty clock"]
        print("%-10s budget-only nodes %-8s | both nodes %-8s | clock-only nodes %-8s -> %s"
              % (name, b["nodes"], both["nodes"], c["nodes"],
                 "both == budget" if both["nodes"] == b["nodes"] else
                 ("both == clock" if both["nodes"] == c["nodes"] else "both differs from each")))
        print("%-10s huge budget + 10ms clock: nodes %-8s depth %-3s wall %7.1f ms -> clock %s"
              % ("", h["nodes"], h["depth"], h["wall_ms"],
                 "HONOURED" if h["wall_ms"] < 500 else "IGNORED (searched as if time were ample)"))


if __name__ == "__main__":
    main()
