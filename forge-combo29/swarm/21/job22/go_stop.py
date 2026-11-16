#!/usr/bin/env python3
"""go_stop.py OUTDIR

30-F1 done properly: send a `go` line, wait a short fixed time, send `stop`, and count the
bestmoves. A bare `go` never ends by itself (a legal infinite search), so any test that waits
for bestmove without a `stop` measures the wrong thing — that was my job21 mistake.

For each go line, on the PC build and the base build, Threads 1:
  - send `position startpos` then `isready`/`readyok`
  - send the go line
  - wait WAIT seconds
  - send `stop`
  - read until the FIRST bestmove; keep reading for a further GRACE to catch a SECOND one
  - assert the bestmove is legal on startpos (python-chess)
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, Timeout  # noqa: E402

import chess

GOS = ["go banana", "go depth -3", "go", "go depth 0", "go nodes 0", "go movetime 0", "go depth 5"]
WAIT = 0.35
GRACE = 1.2


def run_one(exe, outdir, tag, go_line):
    e = SafeEngine(exe, os.path.join(outdir, tag + "_raw.txt"), hash_mb=16, threads=1)
    e.position("position startpos")
    # send raw through the driver, but do NOT wait for bestmove: this go may search for ever
    e.send(go_line)
    time.sleep(WAIT)
    e.send("stop")
    bestmoves = []
    t_stop = time.monotonic()
    first_at = None
    deadline = t_stop + GRACE
    while time.monotonic() < deadline:
        try:
            ln = e.read_line(0.2)
        except Timeout:
            continue
        except EOFError:
            break
        if ln.startswith("bestmove"):
            if first_at is None:
                first_at = time.monotonic()
            bestmoves.append(ln.split()[1] if len(ln.split()) > 1 else "")
    latency = round((first_at - t_stop) * 1000.0, 1) if first_at else None
    e.close()
    legal = {m.uci() for m in chess.Board().legal_moves}
    ok = len(bestmoves) == 1 and bestmoves[0] in legal
    return dict(go=go_line, bestmoves=bestmoves, count=len(bestmoves),
                latency_ms=latency, legal=(bestmoves[0] in legal if bestmoves else None),
                ok=ok)


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    builds = [("pc", os.path.expanduser("~/b/pc_asan/forge")),
              ("base", os.path.expanduser("~/b/asan/forge"))]
    R = {}
    rows = ["| build | go line | bestmoves | count | stop→bestmove ms | legal |",
            "|---|---|---|---|---|---|"]
    for bname, exe in builds:
        for g in GOS:
            tag = "%s_%s" % (bname, g.replace(" ", "_"))
            r = run_one(exe, outdir, tag, g)
            R["%s|%s" % (bname, g)] = r
            rows.append("| %s | `%s` | %s | %d | %s | %s |" % (
                bname, g, r["bestmoves"], r["count"], r["latency_ms"], r["legal"]))
    pc_ok = all(v["ok"] for k, v in R.items() if k.startswith("pc|"))
    base_ok = all(v["ok"] for k, v in R.items() if k.startswith("base|"))
    text = "\n".join(rows)
    text += ("\n\nEvery go line yields exactly one legal bestmove after stop:\n")
    text += "PC build: %s\nbase build: %s\n" % (pc_ok, base_ok)
    text += "\n=> %s\n" % ("CONFIRMS 30-F1 on both builds" if (pc_ok and base_ok)
                           else "REFUTES or INCONCLUSIVE — see the rows that are not one legal bestmove")
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text)
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(R, fh, indent=1)
    print(text)


if __name__ == "__main__":
    main()