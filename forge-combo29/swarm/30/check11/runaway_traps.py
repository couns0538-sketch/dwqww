#!/usr/bin/env python3
"""runaway_traps.py -- the two SILENT RUNAWAYS, measured side by side in one run, and saved.

Trap 1 (node budget): a `go nodes` line whose value is not a positive integer (`-1`, `xyz`, or the
word `depth` because the formatter put a keyword where the number belongs) is accepted as NO NODE
LIMIT: the search runs until something else stops it.

Trap 2 (one-sided clock): a `go` line carrying only ONE side's clock (`go wtime N` with no `btime`)
makes the clock value irrelevant: `wtime 0` and `wtime 1000` produce the SAME tree, unbounded.

Both are HARNESS traps, not engine defects in the sense of "wrong chess" — the engine computes
correctly, it simply does not stop. Both are silent: a driver that waits for `bestmove` without a
wall-clock guard waits forever, and a driver that closes stdin gets 19-F12's fabricated move instead.

Every row: fresh process, Threads 1, Hash 16, OwnBook false, confirmed setoptions, explicit window.
A row that produces no bestmove inside the window is reported as RUNAWAY with the nodes reached.

usage: runaway_traps.py OUTDIR [WINDOW_S]
"""
import json
import os
import subprocess
import sys
import threading
import time

BUILDS = {"pc_r15": "/home/ubuntu/b/pc/forge", "base": "/home/ubuntu/b/rel/forge"}
ENV = {k: v for k, v in os.environ.items()
       if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS", "LSAN_OPTIONS")}
S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5),
       ("LmpBase", 8), ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24),
       ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212), ("SingularDepth", 6),
       ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
TRAPS = [
    ("trap1_node_budget", "position startpos", "go nodes -1"),
    ("trap1_node_budget", "position startpos", "go nodes xyz"),
    ("trap1_node_budget", "position startpos", "go nodes depth 5"),
    ("trap1_CONTROL", "position startpos", "go nodes 200000"),
    ("trap2_one_sided_clock", "position fen 2N3k1/3pn1p1/8/2R1P1KP/7P/8/8/5r2 b - - 18 55",
     "go wtime 0"),
    ("trap2_one_sided_clock", "position fen 2N3k1/3pn1p1/8/2R1P1KP/7P/8/8/5r2 b - - 18 55",
     "go wtime 1000"),
    ("trap2_CONTROL", "position fen 2N3k1/3pn1p1/8/2R1P1KP/7P/8/8/5r2 b - - 18 55",
     "go wtime 0 btime 0"),
    ("trap2_CONTROL", "position fen 2N3k1/3pn1p1/8/2R1P1KP/7P/8/8/5r2 b - - 18 55",
     "go wtime 1000 btime 1000"),
]


def run(exe, settings, pos, go, window):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1, env=ENV)
    out = []
    lock = threading.Lock()

    def pump():
        try:
            for l in p.stdout:
                with lock:
                    out.append(l.rstrip("\n"))
        except Exception:
            pass

    threading.Thread(target=pump, daemon=True).start()

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def ready(t=120.0):
        with lock:
            k = len(out)
        send("isready")
        t0 = time.monotonic()
        while time.monotonic() - t0 < t:
            with lock:
                if any(x.strip() == "readyok" for x in out[k:]):
                    return
            if p.poll() is not None:
                return
            time.sleep(0.003)

    send("uci")
    time.sleep(0.1)
    send("setoption name Threads value 1")
    ready()
    send("setoption name Hash value 16")
    ready()
    for n, v in settings:
        send("setoption name %s value %s" % (n, v))
        ready()
    send("ucinewgame")
    ready()
    send(pos)
    ready()
    with lock:
        mark = len(out)
    t0 = time.monotonic()
    send(go)
    got = None
    while time.monotonic() - t0 < window:
        with lock:
            hit = [x for x in out[mark:] if x.startswith("bestmove")]
        if hit:
            parts = hit[0].split()
            got = parts[1] if len(parts) > 1 else None
            break
        time.sleep(0.004)
    el = time.monotonic() - t0
    with lock:
        blk = out[mark:]
    try:
        send("quit")
    except Exception:
        pass
    try:
        p.wait(timeout=15)
    except Exception:
        p.kill()
    infos = [x for x in blk if x.startswith("info depth") and " pv" in x]
    depth = nodes = None
    if infos:
        t = infos[-1].split()
        if "depth" in t:
            depth = int(t[t.index("depth") + 1])
        if "nodes" in t:
            nodes = int(t[t.index("nodes") + 1])
    return {"bestmove": got, "answered": got is not None, "seconds": round(el, 2),
            "depth": depth, "nodes": nodes, "info_lines": len(infos)}


def main():
    outdir = sys.argv[1]
    window = float(sys.argv[2]) if len(sys.argv) > 2 else 20.0
    os.makedirs(outdir, exist_ok=True)
    report = {"window_s": window, "rows": []}
    print("window = %.0f s per row; Threads 1, Hash 16, OwnBook false" % window)
    print("%-22s %-6s %-22s %-9s %-8s %s" % ("trap", "build", "go line", "answered", "secs", "nodes"))
    for tname, pos, go in TRAPS:
        for bname, exe in BUILDS.items():
            settings = PC20 if bname == "pc_r15" else S14
            r = run(exe, settings, pos, go, window)
            r.update({"trap": tname, "build": bname, "go": go, "position": pos})
            report["rows"].append(r)
            print("%-22s %-6s %-22s %-9s %-8s %s" % (
                tname, bname, go, r["answered"], r["seconds"], r["nodes"]))
    runaways = [r for r in report["rows"] if not r["answered"]]
    report["summary"] = {
        "rows": len(report["rows"]),
        "runaways": len(runaways),
        "runaways_detail": [{"trap": r["trap"], "build": r["build"], "go": r["go"],
                             "nodes": r["nodes"], "seconds": r["seconds"]} for r in runaways],
        "controls_all_answered": all(r["answered"] for r in report["rows"]
                                     if "CONTROL" in r["trap"])}
    with open(os.path.join(outdir, "runaway_traps.json"), "w") as f:
        json.dump(report, f, indent=1)
    print()
    print(json.dumps(report["summary"], indent=1))


if __name__ == "__main__":
    main()
