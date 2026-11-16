#!/usr/bin/env python3
"""halfmove_control.py — the control for job 7: does seat 01's patch actually fix the HALFMOVE door?

This is the control that makes the repetition result meaningful: if the patch fixes the halfmove door and not
the repetition door, the repetition door is a separate door. An interactive driver is required — piping `go` and
`quit` together lets `quit` cancel the search and produces a bogus "unsearched" answer.

usage: halfmove_control.py <base-exe> <patched-exe>
"""
import re
import subprocess
import sys
import threading
import time

FEN = "6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - {hm} 60"


def ask(exe, fen, go="go depth 6"):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    out = []
    threading.Thread(target=lambda: [out.append(l.rstrip("\n")) for l in p.stdout], daemon=True).start()
    for c in ("uci", "setoption name OwnBook value false", "isready", "ucinewgame", "isready",
              f"position fen {fen}", "isready", go):
        p.stdin.write(c + "\n")
        p.stdin.flush()
    t0 = time.monotonic()
    while time.monotonic() - t0 < 40:
        if any(x.startswith("bestmove") for x in out):
            break
        time.sleep(0.002)
    p.stdin.write("quit\n")
    p.stdin.flush()
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    d = [x for x in out if x.startswith("info depth")]
    b = [x for x in out if x.startswith("bestmove")]
    nodes = max([int(m.group(1)) for x in d for m in [re.search(r"nodes (\d+)", x)] if m], default=0)
    sc = re.search(r"score (\S+(?: \S+)?)", d[-1]).group(1) if d else "-"
    return (b[-1].split()[1] if b else "<none>"), sc, nodes


if __name__ == "__main__":
    base, patched = sys.argv[1], sys.argv[2]
    print(f"{'build':10s} {'halfmove':8s} {'bestmove':9s} {'score':8s} nodes")
    for lab, exe in (("base", base), ("patched", patched)):
        for hm in (0, 99, 100, 101, 150):
            bm, sc, n = ask(exe, FEN.format(hm=hm))
            print(f"{lab:10s} {hm:8d} {bm:9s} {sc:8s} {n}")
