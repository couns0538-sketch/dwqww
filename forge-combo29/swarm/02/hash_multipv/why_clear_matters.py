#!/usr/bin/env python3
"""S02 — WHY does the clear matter? Compare hashfull and TT hit behaviour, MultiPV 4, with vs without the clear.

The question the fixer needs answered before building a cluster-local clear:
  if the no-clear build shows a MUCH HIGHER hit rate, surviving entries are being REUSED, the score changes are
  explained by reuse, and a cluster-local clear (which removes exactly that reuse) is not equivalent either.
  if the hit rate barely moves, something subtler is happening.

How hits are measured without instrumenting the engine: the engine prints `hashfull` in every info line, and
`nodes` per line. Those are the only TT observables it exposes. So this records, per final-depth line:
  * the `hashfull` value (occupied entries in the sampled 1000 clusters, per 1000),
  * the `nodes` for that line,
  * the line's emitted `score` and `pv`.
and compares the whole sequence BETWEEN the two builds. A reuse story predicts the no-clear build's hashfull is
higher (more entries occupied, kept from the previous line) at the same multipv index.

Honest limit, stated up front: hashfull is a SAMPLE of 1000 clusters (src/search.cpp:562-573), not a probe
counter, and the engine exposes no hit counter. So this measures OCCUPANCY, which is the closest available proxy
for "entries survived and could be reused". It cannot distinguish "survived and were hit" from "survived and were
missed". I say what the number supports and what it does not.

usage: why_clear_matters.py <with_clear_exe> <no_clear_exe> <outdir> [runs]
"""
import json
import os
import re
import subprocess
import sys
import threading
import time

A = sys.argv[1]
B = sys.argv[2]
OUT = sys.argv[3] if len(sys.argv) > 3 else "out_why"
RUNS = int(sys.argv[4]) if len(sys.argv) > 4 else 3

FEN = "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9"
DEPTH = 8
MULTIPV = 4
SETUP = ["setoption name Threads value 1", "setoption name Hash value 16",
         "setoption name OwnBook value false",
         "setoption name MultiPV value %d" % MULTIPV]

LINE_RE = re.compile(
    r"^info depth (\d+) multipv (\d+) score (\S+) (\S+) seldepth (\d+) nodes (\d+) "
    r"nps (\d+) hashfull (\d+) time (\d+)(?: pv (.*))?$")


def run(exe):
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

    def wait(pref, n0=0, to=180.0):
        dl = time.monotonic() + to
        while time.monotonic() < dl:
            if any(l.startswith(pref) for l in L[n0:]):
                return True
            if p.poll() is not None:
                return any(l.startswith(pref) for l in L[n0:])
            time.sleep(0.001)
        return False

    send("uci")
    if not wait("uciok"):
        raise SystemExit("FAIL: no uciok from %s" % exe)
    for s in SETUP:
        send(s)
    send("isready")
    if not wait("readyok"):
        raise SystemExit("FAIL: no readyok from %s" % exe)
    for line in L:
        if "unknown option" in line or "invalid value" in line:
            raise SystemExit("FAIL: option refused: %r" % line)
    send("position fen " + FEN)
    send("isready")
    n = len(L)
    wait("readyok", n)
    n = len(L)
    t0 = time.monotonic()
    send("go depth %d" % DEPTH)
    if not wait("bestmove", n, 300):
        raise SystemExit("FAIL: no bestmove from %s" % exe)
    ms = (time.monotonic() - t0) * 1000.0
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()

    # every info line of the FINAL depth, in emission order
    rows = []
    for line in L[n:]:
        m = LINE_RE.match(line)
        if not m:
            continue
        if int(m.group(1)) != DEPTH:
            continue
        rows.append({"multipv": int(m.group(2)), "score_kind": m.group(3),
                     "score": int(m.group(4)), "seldepth": int(m.group(5)),
                     "nodes": int(m.group(6)), "hashfull": int(m.group(8)),
                     "pv": (m.group(10) or "").split()})
    # also count how many info lines were emitted in total (a proxy for iteration activity)
    total_infos = sum(1 for line in L[n:] if line.startswith("info depth"))
    return {"ms": round(ms, 0), "final": rows, "total_info_lines": total_infos}


def main():
    os.makedirs(OUT, exist_ok=True)
    res = {}
    for label, exe in (("with_clear", A), ("no_clear", B)):
        runs = [run(exe) for _ in range(RUNS)]
        res[label] = {"exe": exe, "runs": runs,
                      "sha256": subprocess.run(["sha256sum", exe], capture_output=True,
                                               text=True).stdout.split()[0]}
        print("== %s: %d runs" % (label, RUNS))
        for r in runs:
            print("   %5.0f ms  %s" % (r["ms"], " | ".join(
                "mpv%d %s%d nodes=%d hashfull=%d" % (x["multipv"], x["score_kind"],
                                                     x["score"], x["nodes"], x["hashfull"])
                for x in r["final"])))
        print()

    a, b = res["with_clear"]["runs"][0], res["no_clear"]["runs"][0]
    print("### per-line comparison at depth %d, MultiPV %d" % (DEPTH, MULTIPV))
    print()
    print("| line | with clear: score | nodes | hashfull | without clear: score | nodes | hashfull | hashfull delta |")
    print("|---|---|---|---|---|---|---|---|")
    for i in range(max(len(a["final"]), len(b["final"]))):
        x = a["final"][i] if i < len(a["final"]) else None
        y = b["final"][i] if i < len(b["final"]) else None
        if not x or not y:
            continue
        print("| multipv %d | %s %d | %d | %d | %s %d | %d | %d | %+d |"
              % (x["multipv"], x["score_kind"], x["score"], x["nodes"], x["hashfull"],
                 y["score_kind"], y["score"], y["nodes"], y["hashfull"],
                 y["hashfull"] - x["hashfull"]))

    # stability check: are hashfull values stable across runs of the same build?
    def stable(label):
        first = res[label]["runs"][0]["final"]
        return all([(r["multipv"], r["hashfull"], r["nodes"], r["score"]) for r in run["final"]]
                   == [(r["multipv"], r["hashfull"], r["nodes"], r["score"]) for r in first]
                   for run in res[label]["runs"])

    stable_a, stable_b = stable("with_clear"), stable("no_clear")
    print()
    print("with-clear stable across runs (multipv, hashfull, nodes, score all equal): %s" % stable_a)
    print("no-clear   stable across runs: %s" % stable_b)

    hf_a = [x["hashfull"] for x in a["final"]]
    hf_b = [x["hashfull"] for x in b["final"]]
    print()
    print("hashfull series with clear   : %s" % hf_a)
    print("hashfull series without clear: %s" % hf_b)
    delta = sum(hf_b) - sum(hf_a)
    print("sum of hashfull over the %d lines: with=%d without=%d  delta=%+d" % (len(hf_a), sum(hf_a), sum(hf_b), delta))

    json.dump({"position": FEN, "depth": DEPTH, "multipv": MULTIPV, "runs": RUNS,
               "setup": SETUP, "results": res,
               "stable_with_clear": stable_a, "stable_no_clear": stable_b,
               "hashfull_sum_with": sum(hf_a), "hashfull_sum_without": sum(hf_b),
               "note": "hashfull is the engine's own 1000-cluster sample occupancy, not a probe/hit counter; "
                       "the engine exposes no hit counter, so this measures OCCUPANCY as the closest proxy"},
              open(os.path.join(OUT, "why.json"), "w"), indent=1)
    print()
    print("raw: why.json")


if __name__ == "__main__":
    main()
