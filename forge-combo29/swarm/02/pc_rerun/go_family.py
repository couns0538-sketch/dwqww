#!/usr/bin/env python3
"""S02: map the whole eaten-keyword `go` family — every ordered pair of `go` parameters, base vs PC build.

S-F6 found that `go btime wtime 50` never ends on the base tree and ends at once on the PC build, because the
base parser takes `wtime` as btime's value. That is one cell of a family. This walks the family systematically
rather than by hand: for every ordered PAIR (X, Y) of parameter keywords, send `go X Y 50` and see whether the
search ends by itself.

The point is to answer the owner's question precisely: which keyword combinations were already broken on the
PC side (i.e. are repaired by FORGE_FIX_GO_PARSE) and which are still broken on the PC build.

A pair that hangs is only a DEFECT if a search was expected to end: `go depth wtime 50` names no depth value, so
whether it should end is arguable. I therefore report the mechanism (does the build end the search?) separately
for each build and let the DIFFERENCE between the builds carry the finding, rather than judging intent.

THREADS 1, OwnBook false, fresh process per case, interactive driver, COLD.

usage: go_family.py <pc_exe> <base_exe> <outdir>
"""
import itertools
import json
import os
import subprocess
import sys
import threading
import time

PC = sys.argv[1] if len(sys.argv) > 1 else "/agent/repos/pc/forge-combo29/build-pc/forge"
BASE = sys.argv[2] if len(sys.argv) > 2 else "/agent/repos/base/forge-combo29/build/forge"
OUT = sys.argv[3] if len(sys.argv) > 3 else "out_family"

FEN = "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9"
SETUP = ["setoption name Threads value 1", "setoption name Hash value 16",
         "setoption name OwnBook value false"]
KEYWORDS = ["wtime", "btime", "winc", "binc", "depth", "nodes", "movetime", "movestogo", "mate"]
GRACE = 1.0


def run(exe, go):
    env = {k: v for k, v in os.environ.items()
           if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS")}
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
    L = []
    threading.Thread(target=lambda: [L.append(l.rstrip("\n")) for l in p.stdout], daemon=True).start()

    def send(t):
        if p.poll() is None:
            try:
                p.stdin.write(t + "\n")
                p.stdin.flush()
            except Exception:
                pass

    def wait(pref, n0=0, to=5.0):
        dl = time.monotonic() + to
        while time.monotonic() < dl:
            if any(l.startswith(pref) for l in L[n0:]):
                return True
            if p.poll() is not None:
                return any(l.startswith(pref) for l in L[n0:])
            time.sleep(0.001)
        return False

    send("uci")
    wait("uciok")
    for s in SETUP:
        send(s)
    send("isready")
    if not wait("readyok"):
        return {"go": go, "error": "setup failed"}
    send("position fen " + FEN)
    send("isready")
    n = len(L)
    wait("readyok", n)
    n = len(L)
    t0 = time.monotonic()
    send(go)
    ended = wait("bestmove", n, GRACE)
    el = (time.monotonic() - t0) * 1000
    if not ended:
        send("stop")
        wait("bestmove", n, 5.0)
    send("quit")
    try:
        p.wait(timeout=5)
    except Exception:
        p.kill()
    return {"go": go, "ended": ended, "ms": round(el, 1)}


def main():
    os.makedirs(OUT, exist_ok=True)
    pairs = [(a, b) for a, b in itertools.permutations(KEYWORDS, 2)]
    rows = []
    print("%-24s %-8s %-8s %s" % ("go X Y 50", "base", "PC", "note"))
    for a, b in pairs:
        go = "go %s %s 50" % (a, b)
        rb = run(BASE, go)
        rp = run(PC, go)
        be, pe = rb.get("ended"), rp.get("ended")
        note = ""
        if be is False and pe is True:
            note = "REPAIRED ON PC"
        elif be is False and pe is False:
            note = "hangs on BOTH"
        elif be is True and pe is False:
            note = "REGRESSION on PC?"
        rows.append({"a": a, "b": b, "go": go, "base": rb, "pc": rp, "note": note})
        if note or be != pe:
            print("%-24s %-8s %-8s %s" % (go, be, pe, note))
    json.dump({"pc_exe": PC, "base_exe": BASE,
               "pc_sha256": subprocess.run(["sha256sum", PC], capture_output=True,
                                           text=True).stdout.split()[0],
               "base_sha256": subprocess.run(["sha256sum", BASE], capture_output=True,
                                             text=True).stdout.split()[0],
               "settings": "Threads 1, Hash 16, OwnBook false (PC20's thread/hash/book part; the S14 and "
                           "switch part does not affect `go` parsing)",
               "threads": 1, "grace_s": GRACE, "rows": rows,
               "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(os.path.join(OUT, "results.json"), "w"), indent=1)

    rep = [r for r in rows if r["note"] == "REPAIRED ON PC"]
    both = [r for r in rows if r["note"] == "hangs on BOTH"]
    reg = [r for r in rows if r["note"] == "REGRESSION on PC?"]
    print()
    print("pairs tested: %d" % len(rows))
    print("REPAIRED ON PC (base hangs, PC ends): %d" % len(rep))
    for r in rep:
        print("   %-24s base %.0f ms -> PC %.1f ms" % (r["go"], r["base"]["ms"], r["pc"]["ms"]))
    print("hangs on BOTH: %d" % len(both))
    for r in both:
        print("   %-24s base %.0f ms, PC %.0f ms" % (r["go"], r["base"]["ms"], r["pc"]["ms"]))
    print("possible REGRESSIONS: %d" % len(reg))
    for r in reg:
        print("   %-24s base ended, PC did NOT" % r["go"])


if __name__ == "__main__":
    main()
