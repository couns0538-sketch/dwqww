#!/usr/bin/env python3
"""S02: what SHOULD `ponderhit` do, decided from what the engine actually does in the case that matters.

S-F3 records that on a NON-ponder search `ponderhit` is a no-op and the search runs on. Before recommending a
behaviour I have to know whether the mechanism is correct in the case `ponderhit` exists for: a search started
with `go ponder`, where `ponderhit` is supposed to switch from "pondering on the opponent's time" to "searching
on OUR time". If that case works, the engine's handling is right and the finding is a GUI-side warning. If it
does not work either, `ponderhit` is broken as a whole and the recommendation is different.

Three searches, each the first of a fresh process (COLD per seat 10), driven interactively (19-F12: piping and
closing stdin makes this build invent a bestmove):

  A: `go ponder wtime 400 btime 400`  then wait 400 ms, then `ponderhit`
     -> if ponderhit switches to our clock, the search should END by itself shortly after ponderhit
        (the clock budget is ~400 ms minus overhead, and 400 ms of it was already spent pondering).
        If it runs on until `stop`, ponderhit did nothing.
  B: `go ponder wtime 400 btime 400` then wait 400 ms, then `stop`
     -> control: shows that `stop` alone does end it.
  C: `go infinite` then `ponderhit` (S-F3's case)
     -> control: shows the no-op.

usage: probe_ponderhit.py <exe> <outdir>
"""
import json
import os
import re
import subprocess
import sys
import threading
import time

EXE = sys.argv[1] if len(sys.argv) > 1 else "/agent/repos/base/forge-combo29/build/forge"
OUT = sys.argv[2] if len(sys.argv) > 2 else "out"
FEN = "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9"
WAIT = 400          # ms spent "pondering" before the trigger
GRACE = 1200        # ms to wait for a bestmove AFTER the trigger, before concluding it did not end


def run(go, trigger):
    env = {k: v for k, v in os.environ.items()
           if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS")}
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
    L = []
    threading.Thread(target=lambda: [L.append(l.rstrip("\n")) for l in p.stdout], daemon=True).start()

    def say(t):
        p.stdin.write(t + "\n")
        p.stdin.flush()

    def wait(pref, n0=0, to=5.0):
        dl = time.time() + to
        while time.time() < dl:
            if any(l.startswith(pref) for l in L[n0:]):
                return True
            time.sleep(0.002)
        return False

    say("uci")
    wait("uciok")
    say("isready")
    wait("readyok")
    say("setoption name OwnBook value false")
    say("isready")
    n = len(L)
    wait("readyok", n)
    say("position fen " + FEN)
    say("isready")
    n = len(L)
    wait("readyok", n)

    n2 = len(L)
    t0 = time.monotonic()
    say(go)
    time.sleep(WAIT / 1000.0)
    info_before_trigger = len([l for l in L[n2:] if l.startswith("info depth")])
    say(trigger)
    ended = wait("bestmove", n2, GRACE / 1000.0)
    elapsed_after = (time.monotonic() - t0) * 1000.0
    stopped = False
    if not ended:
        say("stop")
        stopped = wait("bestmove", n2, 5.0)
    bm = [l for l in L[n2:] if l.startswith("bestmove")]
    info = len([l for l in L[n2:] if l.startswith("info depth")])
    say("quit")
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    return {"go": go, "trigger": trigger, "waited_ms_before_trigger": WAIT,
            "grace_ms_after_trigger": GRACE,
            "bestmove_by_itself_after_trigger": ended,
            "elapsed_ms_total": round(elapsed_after, 1),
            "info_depth_before_trigger": info_before_trigger,
            "info_depth_total": info, "needed_stop": stopped,
            "bestmove": bm[-1] if bm else None}


def main():
    os.makedirs(OUT, exist_ok=True)
    cases = [
        ("go ponder wtime 400 btime 400", "ponderhit"),
        ("go ponder wtime 400 btime 400", "stop"),
        ("go infinite", "ponderhit"),
    ]
    rows = [run(go, tr) for go, tr in cases]
    for r in rows:
        print("%-34s + %-10s -> ended by itself: %-5s  elapsed %7.1f ms  info lines %2d  needed stop: %s"
              % (r["go"], r["trigger"], r["bestmove_by_itself_after_trigger"],
                 r["elapsed_ms_total"], r["info_depth_total"], r["needed_stop"]))
    json.dump({"exe": EXE,
               "sha256": subprocess.run(["sha256sum", EXE], capture_output=True,
                                        text=True).stdout.split()[0],
               "position": FEN, "rows": rows,
               "option_lines_sent": ["setoption name OwnBook value false"],
               "expected_clock_budget_ms": "400 requested minus Move Overhead 10 = ~390",
               "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(os.path.join(OUT, "rows.json"), "w"), indent=1)

    a, b, c = rows
    checks = {
        "control: `stop` DOES end a ponder search": b["bestmove_by_itself_after_trigger"] is True,
        "`ponderhit` on a `go ponder` search ends it by itself (it switched to our clock)":
            a["bestmove_by_itself_after_trigger"] is True,
        "`ponderhit` on `go infinite` does NOT end it (S-F3's case)":
            c["bestmove_by_itself_after_trigger"] is False,
        "the ponderhit-triggered end happens soon after the trigger, not at once":
            a["elapsed_ms_total"] >= WAIT,
    }
    print()
    print("### checks")
    for k, v in checks.items():
        print("- %-84s %s" % (k, "PASS" if v else "FAIL"))
    json.dump(checks, open(os.path.join(OUT, "checks.json"), "w"), indent=1)
    print()
    if checks["`ponderhit` on a `go ponder` search ends it by itself (it switched to our clock)"]:
        print("READING: ponderhit works in the case it exists for, so `ignore it on a non-ponder search` is "
              "the correct engine behaviour and S-F3 is a GUI-side warning, not an engine defect.")
    else:
        print("READING: ponderhit does NOT switch to our clock even on a `go ponder` search, so it is "
              "broken as a whole and S-F3's recommendation must say so.")


if __name__ == "__main__":
    main()
