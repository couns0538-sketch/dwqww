#!/usr/bin/env python3
"""S02 — does the secondary MultiPV search DEPEND on the per-line `tt.clear()`?

The experiment the coordinator asked for: one position, `go depth 8` at MultiPV 4, with and without the clear.

IMPORTANT about what is compared: this is a SCRATCH VARIANT BUILD of the PC r15 source kept outside the
repository (/agent/repos/pc-noclear). The engine source in the repository is untouched; per the rules a change
of the engine lives only as a text patch in my folder, and the patch is committed beside this file.

Measurement per run: for the FINAL depth, every `info depth N multipv K score ... pv ...` line, verbatim, and
the `bestmove`. The comparison is string equality of the full emitted line set, so a single score or a single
PV move differing is caught. Threads 1, OwnBook false, fresh process per run, interactive driver.

usage: remove_clear_probe.py <buildA_exe> <buildB_exe> <outdir> [runs]
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
OUT = sys.argv[3] if len(sys.argv) > 3 else "out_probe"
RUNS = int(sys.argv[4]) if len(sys.argv) > 4 else 3

FEN = "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9"
DEPTH = 8
MULTIPV = 4
SETUP = ["setoption name Threads value 1", "setoption name Hash value 16",
         "setoption name OwnBook value false",
         "setoption name MultiPV value %d" % MULTIPV]


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

    def wait(pref, n0=0, to=120.0):
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
            raise SystemExit("FAIL: option refused by %s: %r" % (exe, line))
    send("position fen " + FEN)
    send("isready")
    n = len(L)
    wait("readyok", n)
    n = len(L)
    t0 = time.monotonic()
    send("go depth %d" % DEPTH)
    if not wait("bestmove", n, 240):
        raise SystemExit("FAIL: no bestmove from %s" % exe)
    ms = (time.monotonic() - t0) * 1000.0
    seg = list(L[n:])
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    # the last emitted block at the final depth, one line per multipv, in emission order
    final = [l for l in seg if re.match(r"info depth %d multipv " % DEPTH, l)]
    bm = [l for l in seg if l.startswith("bestmove")]
    # normalise ONLY the timing fields, which are wall-clock and cannot match between builds by nature
    norm = []
    for l in final:
        l2 = re.sub(r" time \d+", " time <T>", l)
        l2 = re.sub(r" nps \d+", " nps <N>", l2)
        l2 = re.sub(r" nodes \d+", " nodes <X>", l2)
        norm.append(l2)
    return {"ms": round(ms, 0), "raw": final, "norm": norm,
            "bestmove": bm[-1] if bm else None,
            "scores": [re.search(r"score (\S+ \S+)", l).group(1) for l in final if "score" in l],
            "pvs": [l.split(" pv ")[1] if " pv " in l else "" for l in final],
            "nodes": [int(m.group(1)) for l in final for m in [re.search(r" nodes (\d+)", l)] if m]}


def main():
    os.makedirs(OUT, exist_ok=True)
    res = {}
    for label, exe in (("with_clear", A), ("no_clear", B)):
        runs = [run(exe) for _ in range(RUNS)]
        res[label] = {"exe": exe,
                      "sha256": subprocess.run(["sha256sum", exe], capture_output=True,
                                               text=True).stdout.split()[0],
                      "runs": runs}
        print("== %s (%s)" % (label, exe))
        for r in runs:
            print("   %5.0f ms  bestmove %s" % (r["ms"], (r["bestmove"] or "").split()[1]
                                                 if r["bestmove"] else "?"))
            for s, pv in zip(r["scores"], r["pvs"]):
                print("      score %-8s pv %s" % (s, pv[:70]))
        print()

    a, b = res["with_clear"]["runs"][0], res["no_clear"]["runs"][0]
    print("### the comparison (timing fields normalised; every other byte compared)")
    print()
    print("| | with clear | without clear | identical? |")
    print("|---|---|---|---|")
    print("| number of final-depth lines | %d | %d | %s |"
          % (len(a["norm"]), len(b["norm"]), "YES" if len(a["norm"]) == len(b["norm"]) else "NO"))
    for k in range(max(len(a["norm"]), len(b["norm"]))):
        la = a["norm"][k] if k < len(a["norm"]) else "(missing)"
        lb = b["norm"][k] if k < len(b["norm"]) else "(missing)"
        print("| line %d | `%s` | `%s` | %s |" % (k + 1, la[:60], lb[:60],
                                                  "YES" if la == lb else "**NO**"))
    print("| bestmove | %s | %s | %s |" % (a["bestmove"], b["bestmove"],
                                           "YES" if a["bestmove"] == b["bestmove"] else "**NO**"))
    identical = (a["norm"] == b["norm"] and a["bestmove"] == b["bestmove"])
    stable_a = all(r["norm"] == a["norm"] for r in res["with_clear"]["runs"])
    stable_b = all(r["norm"] == b["norm"] for r in res["no_clear"]["runs"])
    print()
    print("with-clear identical across its %d runs: %s" % (RUNS, stable_a))
    print("no-clear   identical across its %d runs: %s" % (RUNS, stable_b))
    print()
    if not (stable_a and stable_b):
        print("NOTE: one of the builds is not self-consistent across runs, so a difference between the two")
        print("      builds could be noise. Read the table above with that in mind.")
    if identical:
        print("CONCLUSION: BIT-IDENTICAL — the clear is NOT needed for correctness on this case.")
        print("            The cheap version (clear only the clusters the line touched, or nothing) is the")
        print("            right candidate; it needs no match to justify.")
    else:
        print("CONCLUSION: THE PVs DIFFER — the clear is LOAD-BEARING.")
        print("            Removing it changes output, so it needs a match, not a speed patch.")
    json.dump({"position": FEN, "depth": DEPTH, "multipv": MULTIPV, "runs": RUNS,
               "setup": SETUP, "identical": identical,
               "stable_with_clear": stable_a, "stable_no_clear": stable_b,
               "results": res}, open(os.path.join(OUT, "probe.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
