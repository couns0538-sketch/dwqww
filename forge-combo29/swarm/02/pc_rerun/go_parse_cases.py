#!/usr/bin/env python3
"""S02: does FORGE_FIX_GO_PARSE repair anything my S-F4 reproduces? Test the cases its own comment names.

The patch's comment for the switch says: "in a `go` line a keyword is never taken as the value of the keyword
before it, and a token that is not a complete integer leaves that ONE parameter out ... r9 let
`go wtime btime 50` lose the clock."

So the test is a `go` line where a keyword follows a keyword with no number between them. On the base build the
number that belongs to the SECOND keyword can be eaten by the FIRST. I measure, per build, whether the search
ends by itself and with what warning, for the cases the comment names plus the near neighbours.

THREADS 1, OwnBook false, fresh process per case, interactive driver, COLD per seat 10's rule.

usage: go_parse_cases.py <pc_exe> <base_exe> <outdir>
"""
import json
import os
import subprocess
import sys
import threading
import time

PC = sys.argv[1] if len(sys.argv) > 1 else "/agent/repos/pc/forge-combo29/build-pc/forge"
BASE = sys.argv[2] if len(sys.argv) > 2 else "/agent/repos/base/forge-combo29/build/forge"
OUT = sys.argv[3] if len(sys.argv) > 3 else "out_go_parse"

FEN = "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9"
SETUP_PC = ["setoption name Threads value 1", "setoption name Hash value 16",
            "setoption name OwnBook value false"]
CASES = [
    "go wtime btime 50",       # the exact case the patch comment names
    "go btime wtime 50",       # mirrored
    "go wtime 50 btime",       # second keyword with no number at the end
    "go depth wtime 50",       # a depth keyword with no number before a clock
    "go wtime depth 3",        # a clock with no number before a depth
    "go movetime wtime 50",
    "go wtime 50 depth",       # trailing bare keyword
]


def run(exe, setup, go, grace=2.0):
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
    for s in setup:
        send(s)
    send("isready")
    if not wait("readyok"):
        return {"go": go, "error": "no readyok at setup", "lines": L[:20]}
    send("position fen " + FEN)
    send("isready")
    n = len(L)
    wait("readyok", n)
    n = len(L)
    t0 = time.monotonic()
    send(go)
    ended = wait("bestmove", n, grace)
    elapsed = (time.monotonic() - t0) * 1000
    seg = L[n:]
    if not ended:
        send("stop")
        wait("bestmove", n, 5.0)
        seg = L[n:]
    send("quit")
    try:
        p.wait(timeout=5)
    except Exception:
        p.kill()
    bm = [l for l in seg if l.startswith("bestmove")]
    warn = [l for l in seg if l.startswith("info string")]
    depth = [l for l in seg if l.startswith("info depth")]
    return {"go": go, "ended_by_itself": ended, "elapsed_ms": round(elapsed, 1),
            "bestmove": bm[-1].split()[1] if bm else None,
            "warnings": warn, "info_depth_lines": len(depth)}


def main():
    os.makedirs(OUT, exist_ok=True)
    print("| go line | base+S14: ended | base bestmove | base warn | PC+PC20: ended | PC bestmove | PC warn |")
    print("|---|---|---|---|---|---|---|")
    rows = []
    for go in CASES:
        b = run(BASE, SETUP_PC, go)
        p = run(PC, SETUP_PC, go)
        rows.append({"go": go, "base": b, "pc": p})
        print("| `%s` | %s %5.1f ms | %s | %s | %s %5.1f ms | %s | %s |"
              % (go, b["ended_by_itself"], b["elapsed_ms"], b["bestmove"],
                 (b["warnings"][0][11:] if b["warnings"] else "-"),
                 p["ended_by_itself"], p["elapsed_ms"], p["bestmove"],
                 (p["warnings"][0][11:] if p["warnings"] else "-")))
    json.dump({"pc_exe": PC, "base_exe": BASE,
               "pc_sha256": subprocess.run(["sha256sum", PC], capture_output=True,
                                           text=True).stdout.split()[0],
               "base_sha256": subprocess.run(["sha256sum", BASE], capture_output=True,
                                             text=True).stdout.split()[0],
               "settings": {"pc": "PC20-lite: Threads 1, Hash 16, OwnBook false",
                            "base": "same, because the base build has no PC20 switches"},
               "threads": 1, "rows": rows,
               "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(os.path.join(OUT, "results.json"), "w"), indent=1)

    diffs = [r for r in rows if r["base"]["ended_by_itself"] != r["pc"]["ended_by_itself"]]
    print()
    print("cases where the two builds differ in whether the search ends by itself: %d of %d"
          % (len(diffs), len(rows)))
    for d in diffs:
        print("  %-22s base ended=%s  PC ended=%s" % (d["go"], d["base"]["ended_by_itself"],
                                                     d["pc"]["ended_by_itself"]))


if __name__ == "__main__":
    main()
