#!/usr/bin/env python3
"""check_04f14.py EXE OUT.json — seat 12's check of seat 04's 04-F14 / 04-F16.

Claim: `go nodes N` finishes the iteration it is in and STOPS at an iteration boundary, so
  * the work actually done is quantised to the `nodes` values the `info depth k` lines report;
  * N equal to a boundary uses ~100% of the budget, N = boundary - 1 falls back a whole iteration;
  * therefore two different N can do the same work (30,000 and 20,000 both stop after depth 11).

Design:
  1. Read the position's own boundary list first: run `go depth 20` unbounded and record the
     `nodes` field of every `info depth k` line. Those numbers are the boundaries, per position.
  2. For each boundary b and for b-1, send `go nodes <b>` / `go nodes <b-1>` and record the work
     actually reported. The claim predicts ~1.00x at b and a fall-back at b-1.
  3. Also send a value well above the last boundary to see whether the engine keeps going beyond it
     (my own S-F25 measured 1,000,000 -> 920,173, which is NOT a boundary stop if the deepest
     boundary is far below that).

Every run: fresh process, Threads 1, Hash 16, MultiPV 1, OwnBook false; read to `bestmove` before
anything else.
"""
import json
import queue
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def run(exe, go, bound=300.0):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    q = queue.Queue()
    out = []
    threading.Thread(target=lambda: ([q.put(l.rstrip("\n")) for l in p.stdout], q.put(None)),
                     daemon=True).start()

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def wait(pred, limit):
        end = time.monotonic() + limit
        while time.monotonic() < end:
            try:
                ln = q.get(timeout=0.2)
            except queue.Empty:
                if p.poll() is not None:
                    return None
                continue
            if ln is None:
                return None
            out.append(ln)
            if pred(ln):
                return ln
        return None

    send("uci")
    wait(lambda l: l == "uciok", 30)
    for name, value in (("Hash", 16), ("MultiPV", 1), ("Threads", 1), ("OwnBook", "false")):
        send(f"setoption name {name} value {value}")
        send("isready")
        wait(lambda l: l == "readyok", 30)
    send(f"position fen {START}")
    send("isready")
    wait(lambda l: l == "readyok", 30)
    send(go)
    bm = wait(lambda l: l.startswith("bestmove"), bound)
    send("quit")
    try:
        p.stdin.close()
    except (OSError, ValueError):
        pass
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()

    per_depth = []
    for l in out:
        m = re.match(r"^info depth (\d+).* nodes (\d+)", l)
        if m:
            per_depth.append((int(m.group(1)), int(m.group(2))))
    return {"answered": isinstance(bm, str) and bm.startswith("bestmove"),
            "per_depth": per_depth,
            "last_depth": per_depth[-1][0] if per_depth else None,
            "last_nodes": per_depth[-1][1] if per_depth else None}


def main():
    exe, outfile = sys.argv[1], sys.argv[2]
    print(f"exe {exe}   Threads 1, Hash 16, MultiPV 1, startpos\n")

    # 1. the position's own boundaries, from an unbounded depth search
    ref = run(exe, "go depth 24")
    if not ref["answered"]:
        print("the engine did not answer `go depth 24`")
        return 1
    bounds = [n for _, n in ref["per_depth"]]
    print("2. boundaries this position reports (nodes field of each info depth line):")
    print("   " + " / ".join(f"d{d}:{n:,}" for d, n in ref["per_depth"]))
    print(f"   deepest: depth {ref['last_depth']} = {ref['last_nodes']:,} nodes\n")

    out = {"exe": exe, "boundaries": ref["per_depth"], "tests": []}
    print("3. `go nodes <boundary>` vs `<boundary - 1>` — the quantisation claim")
    print(f"{'budget':>10} {'work done':>12} {'ratio':>7} {'stopped at':>11}  verdict")
    checks = []
    # take a few representative boundaries from the middle and top of the list
    idx = [4, 8, 12] if len(bounds) > 12 else list(range(len(bounds)))[-3:]
    for i in idx:
        b = bounds[i]
        for budget in (b, b - 1):
            r = run(exe, f"go nodes {budget}")
            if not r["answered"] or not r["last_nodes"]:
                print(f"{budget:>10} -- no completed search --")
                continue
            ratio = r["last_nodes"] / budget
            verdict = ("FULL BUDGET USED" if ratio > 0.98 else
                       f"stopped short ({ratio:.2f}x)")
            print(f"{budget:>10} {r['last_nodes']:>12,} {ratio:>7.2f} "
                  f"{'depth ' + str(r['last_depth']):>11}  {verdict}")
            checks.append({"budget": budget, "work": r["last_nodes"], "ratio": round(ratio, 3),
                           "depth": r["last_depth"], "boundary": b})
            out["tests"].append(checks[-1])

    # 4. does the engine stop at the LAST boundary, or keep going past it?
    print("\n4. budgets above the deepest boundary — does it stop at the boundary or keep working?")
    print(f"{'budget':>10} {'work done':>12} {'ratio':>7} {'stopped at':>11}")
    for mult in (2, 4, 8):
        budget = ref["last_nodes"] * mult
        r = run(exe, f"go nodes {budget}")
        if not r["answered"] or not r["last_nodes"]:
            print(f"{budget:>10} -- no completed search --")
            continue
        ratio = r["last_nodes"] / budget
        print(f"{budget:>10} {r['last_nodes']:>12,} {ratio:>7.2f} "
              f"{'depth ' + str(r['last_depth']):>11}")
        out["tests"].append({"budget": budget, "work": r["last_nodes"],
                             "ratio": round(ratio, 3), "depth": r["last_depth"],
                             "above_last_boundary": True})

    Path(outfile).write_text(json.dumps(out, indent=1) + "\n")
    print(f"\nraw -> {outfile}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
