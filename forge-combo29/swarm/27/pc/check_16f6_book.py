#!/usr/bin/env python3
"""check_16f6_book.py <exe> <outdir> [--label base|pc]

Seat 16's S-F6: the built-in book can only affect searches where `game_search` holds, i.e.
`go wtime/btime/...` or `go movetime` -- NOT `go depth`, `go nodes` or `go infinite`
(src/uci.cpp: the probe is guarded by `game_search && own_book && !book.empty() && game_ply(...) < book_depth`).

A claim about which door the book can come through has an exact prediction, so I test BOTH sides:
  (a) analysis limits (depth, nodes, infinite+stop) must be IDENTICAL with OwnBook true and false -- and
      must never print `info string book move`;
  (b) clock/movetime limits MAY print `info string book move` with OwnBook true, and must not with false.
Without (b), "no book line in (a)" could just mean the book is unavailable on this build.

The book is only probed at a small `game_ply`, so the position must be an OPENING and `Book Depth` must be
set high enough to allow it. That is the condition under which (b) can fire at all -- if it cannot fire here
I say so instead of claiming a pass.

Threads 1 throughout.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

OPENING = "rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4"
START = "position startpos"


class Missing(Exception):
    pass


def run(exe, ownbook, cmd, pos, book_depth=None, wait=25.0):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def s(x):
        p.stdin.write(x + "\n"); p.stdin.flush()

    def until(pred, tmo=300, timeout=None):
        if timeout is not None:
            tmo = timeout
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
        s("uci"); _, ok = until(lambda x: x.strip() == "uciok")
        if not ok:
            raise Missing("no uciok")
        s("setoption name Hash value 16")
        s("setoption name Threads value 1")
        if book_depth is not None:
            s("setoption name Book Depth value %d" % book_depth)
        s("setoption name OwnBook value %s" % ("true" if ownbook else "false"))
        s("ucinewgame"); s("isready")
        until(lambda x: x.strip() == "readyok")
        s(pos); s("isready")
        until(lambda x: x.strip() == "readyok")
        s(cmd)
        if cmd.startswith("go infinite"):
            time.sleep(wait)
            s("stop")
        lines, ok = until(lambda x: x.startswith("bestmove"), timeout=600)
        if not ok:
            raise Missing("no bestmove for %r" % cmd)
        book = [l for l in lines if "info string book move" in l]
        infos = [l for l in lines if l.startswith("info depth")]
        last = infos[-1] if infos else ""
        n = re.search(r"nodes (\d+)", last)
        sc = re.search(r"score (cp|mate) (-?\d+)", last)
        bm = next(l for l in lines if l.startswith("bestmove")).split()[1]
        return {"cmd": cmd, "ownbook": ownbook, "book_lines": book,
                "n_info": len(infos), "bestmove": bm,
                "nodes": int(n.group(1)) if n else None,
                "score": (sc.group(1), int(sc.group(2))) if sc else None}
    finally:
        try:
            s("quit"); p.wait(timeout=20)
        except Exception:
            p.kill()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe"); ap.add_argument("outdir")
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    exe = os.path.realpath(a.exe)
    os.makedirs(a.outdir, exist_ok=True)

    ANALYSIS = [("go depth 10", START), ("go nodes 20000", START), ("go infinite + stop 3 s", START)]
    CLOCKED = [("go movetime 300", START), ("go wtime 10000 btime 10000", START)]

    R = {"exe": exe, "label": a.label,
         "sha256": subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0],
         "threads": 1, "a_analysis": [], "b_clocked": []}

    # (a) analysis limits: book on vs off must be identical, and no book line
    for cmd, pos in ANALYSIS:
        on = run(exe, True, cmd, pos, book_depth=100)
        off = run(exe, False, cmd, pos, book_depth=100)
        same = (on["bestmove"] == off["bestmove"] and on["score"] == off["score"]
                and on["nodes"] == off["nodes"])
        R["a_analysis"].append({"cmd": cmd, "on": on, "off": off, "identical": same})
        print("(a) %-24s identical=%-5s booklines on/off=%d/%d  bm %s/%s  nodes %s/%s"
              % (cmd, same, len(on["book_lines"]), len(off["book_lines"]),
                 on["bestmove"], off["bestmove"], on["nodes"], off["nodes"]))

    # (b) clocked limits: the book CAN fire here; if it never does, say so
    for cmd, pos in CLOCKED:
        on = run(exe, True, cmd, pos, book_depth=100)
        off = run(exe, False, cmd, pos, book_depth=100)
        R["b_clocked"].append({"cmd": cmd, "on": on, "off": off})
        print("(b) %-24s booklines on/off=%d/%d  bm %s/%s"
              % (cmd, len(on["book_lines"]), len(off["book_lines"]),
                 on["bestmove"], off["bestmove"]))

    fired = sum(len(x["on"]["book_lines"]) for x in R["b_clocked"])
    R["book_reachable_at_all"] = fired > 0
    all_same = all(x["identical"] for x in R["a_analysis"])
    no_book_a = all(len(x["on"]["book_lines"]) == 0 for x in R["a_analysis"])

    with open(os.path.join(a.outdir, "check_16f6_%s.json" % a.label), "w") as f:
        json.dump(R, f, indent=2)

    print()
    print("book reachable through a clocked search on this build: %s (%d book lines)"
          % (R["book_reachable_at_all"], fired))
    if all_same and no_book_a and R["book_reachable_at_all"]:
        print("verdict: CONFIRMS 16-F6 -- analysis limits identical with the book on and off, no book line "
              "from any analysis limit, and the book demonstrably CAN fire through a clocked limit")
    elif all_same and no_book_a and not R["book_reachable_at_all"]:
        print("verdict: analysis limits are unaffected, BUT the book could not be made to fire at all on this "
              "build, so the 'only a clocked search' half is NOT shown here")
    else:
        print("verdict: NOT confirmed -- see the rows above")


if __name__ == "__main__":
    main()
