#!/usr/bin/env python3
"""drive.py — seat 20, area 10. Interactive UCI driver: writes lines, WAITS for the engine's answer,
so a command sent "later" really is sent later.

usage: drive.py <exe> <case-name> <script>
script lines are either  "send: <uci line>"  or  "wait: <seconds>"
prints the raw transcript and, for each `go`, a verdict line.
"""
import subprocess
import sys
import threading
import time

EXE = sys.argv[1]


def transcript(exe, lines):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    out = []

    def rdo():
        for line in p.stdout:
            out.append(line.rstrip("\n"))

    t = threading.Thread(target=rdo, daemon=True)
    t.start()
    for item in lines:
        kind, _, val = item.partition(":")
        val = val.strip()
        if kind == "send":
            p.stdin.write(val + "\n")
            p.stdin.flush()
            out.append(f"--> {val}")
        elif kind == "wait":
            time.sleep(float(val))
        elif kind == "waitspin":  # wait until a bestmove appears, max val seconds
            t0 = time.monotonic()
            while time.monotonic() - t0 < float(val):
                if any(x.startswith("bestmove") for x in out):
                    break
                time.sleep(0.005)
        elif kind == "quit":
            p.stdin.write("quit\n")
            p.stdin.flush()
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
        out.append("<killed after 20 s>")
    t.join(timeout=2)
    return out


def one(exe, name, lines):
    print(f"===== {name}")
    for line in lines:
        print(f"  script: {line}")
    out = transcript(exe, lines)
    for line in out:
        print("  | " + line)
    depth_lines = [x for x in out if x.startswith("info depth")]
    best = [x for x in out if x.startswith("bestmove")]
    if not depth_lines and best:
        print(f"  >>> VERDICT: bestmove {best[-1].split()[1]} with ZERO info depth lines "
              f"(unsearched first-legal-move fallback)")
    elif best:
        print(f"  >>> VERDICT: normal ({len(depth_lines)} info depth lines, {best[-1].strip()})")
    else:
        print("  >>> VERDICT: no bestmove printed")
    print()
    return out


FEN = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1"
PRE = ["send: uci", "send: isready", "send: ucinewgame", "send: isready"]

if __name__ == "__main__":
    # A: quit arriving while the search runs (the engine answers with the fallback move)
    one(EXE, "A1 go depth 8 then quit at once",
        PRE + [f"send: position fen {FEN}", "send: go depth 8", "send: quit"])
    # B: the same, but the search is allowed to finish first (control)
    one(EXE, "B1 go depth 8, wait for bestmove, then quit",
        PRE + [f"send: position fen {FEN}", "send: go depth 8", "waitspin: 10", "quit"])
    # C: stop after 0 ms — the realistic "GUI stops the search" path
    one(EXE, "C1 go infinite then stop at once",
        PRE + [f"send: position fen {FEN}", "send: go infinite", "send: stop", "waitspin: 10", "quit"])
    # D: stop after a very short time
    for ms in (1, 2, 5, 10, 25):
        one(EXE, f"D{ms} go infinite, stop after {ms} ms",
            PRE + [f"send: position fen {FEN}", "send: go infinite", f"wait: {ms/1000}", "send: stop",
                   "waitspin: 10", "quit"])
