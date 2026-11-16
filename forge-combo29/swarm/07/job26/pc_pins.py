#!/usr/bin/env python3
"""pc_pins.py EXE OUTDIR [--s14] [--pc20]

Checks the PC r15 build against the numbers FABLE_TO_swarm_5.md publishes, in the three regimes it
distinguishes (file 4 also warns that mixing regimes produces false mismatches):

  none : a fresh engine, NO setoption at all  -> bench 11 = 312866, bench 13 = 862329,
                                                 bench 16 = 3024920, go perft 5 = 4865609
  S14  : the 14 file-1 settings, then the bench -> bench 11 = 242796, bench 13 = 656517
  PC20 : S14 + the six settings below           -> bench 11 = 278024, bench 13 = 587276

PC20 = S14, then CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true,
       MateAlphaGuard true, OwnBook false.  Threads 1 and Hash 16 everywhere.

Every figure is parsed and asserted present; a missing bench line fails loudly. Any `unknown option`,
`invalid value` or `ERROR` line is a hard failure (file 5 says to stop on them).
"""
import json
import os
import queue
import re
import subprocess
import sys
import threading

S14 = [
    "LmrQuietBase value 93", "LmrQuietDivisor value 205", "LmrNoisyBase value 13",
    "LmrNoisyDivisor value 333", "LmrHistoryDivisor value 5643", "NullMoveBase value 5",
    "LmpBase value 8", "HistoryPruneMultiplier value 2220",
    "HistoryBonusQuadratic value 24", "HistoryBonusLinear value 54",
    "HistoryBonusMax value 2212", "SingularDepth value 6", "IirDepth value 2",
    "NonPawnCorrection value true",
]
PC20_EXTRA = [
    "CuckooRep value true", "HistRework value 2", "TtPruneV2 value true",
    "CorrHistV2 value true", "MateAlphaGuard value true", "OwnBook value false",
]
EXPECTED = {
    "none": {"bench11": 312866, "bench13": 862329, "bench16": 3024920, "perft5": 4865609},
    "S14": {"bench11": 242796, "bench13": 656517},
    "PC20": {"bench11": 278024, "bench13": 587276},
}


class Reader:
    def __init__(s, st):
        s.q = queue.Queue()
        threading.Thread(target=s._pump, args=(st,), daemon=True).start()

    def _pump(s, st):
        for l in st:
            s.q.put(l)
        s.q.put(None)

    def get(s, t=300):
        try:
            return s.q.get(timeout=t)
        except queue.Empty:
            return None


def one_run(exe, options, commands):
    """One fresh process. Returns (list of output lines, list of bad lines)."""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    r = Reader(p.stdout)
    bad = []

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def drain():
        while True:
            l = r.get()
            if l is None:
                raise RuntimeError("no readyok")
            low = l.lower()
            if "unknown option" in low or "invalid value" in low or "error" in low:
                bad.append(l.strip())
            if l.strip() == "readyok":
                return

    send("uci")
    while True:
        l = r.get(60)
        if l is None or l.strip() == "uciok":
            break
    for opt in options:
        send("setoption name " + opt)
        send("isready")
        drain()
    if options:
        send("ucinewgame")
        send("isready")
        drain()
    out = []
    for cmd in commands:
        send(cmd)
        # bench and perft both answer with lines we must read; perft ends with "nodes N",
        # bench with "info string bench ...".
        deadline_after = None
        while True:
            l = r.get(600)
            if l is None:
                raise RuntimeError(f"no answer to {cmd}")
            out.append(l.rstrip("\n"))
            low = l.lower()
            if "unknown option" in low or "invalid value" in low or "error" in low:
                bad.append(l.strip())
            if l.startswith("info string bench"):
                break
            if l.startswith("nodes "):
                break
        send("isready")
        drain()
    send("quit")
    try:
        p.wait(timeout=30)
    except subprocess.TimeoutExpired:
        p.kill()
    return out, bad


def parse(out, kind):
    if kind == "bench":
        for l in out:
            m = re.match(r"info string bench depth (\d+) nodes (\d+)", l)
            if m:
                return int(m.group(2))
    else:
        for l in reversed(out):
            m = re.match(r"^nodes (\d+)$", l)
            if m:
                return int(m.group(1))
    raise SystemExit(f"FAIL could not parse a {kind} node count from: {out[-3:]}")


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    want_s14 = "--s14" in sys.argv or "--pc20" in sys.argv
    want_pc20 = "--pc20" in sys.argv
    os.makedirs(outdir, exist_ok=True)
    results, failures = {}, []

    regimes = ["none"]
    if want_s14:
        regimes.append("S14")
    if want_pc20:
        regimes.append("PC20")

    for regime in regimes:
        opts = [] if regime == "none" else (S14 if regime == "S14" else S14 + PC20_EXTRA)
        got = {}
        # benches and perft, each its own fresh process (the brief's rule)
        for depth in (11, 13, 16):
            out, bad = one_run(exe, opts, [f"bench {depth}"])
            got[f"bench{depth}"] = parse(out, "bench")
            if bad:
                failures.append(f"{regime} bench {depth}: {bad[:3]}")
        out, bad = one_run(exe, opts, ["go perft 5"])
        got["perft5"] = parse(out, "perft")
        if bad:
            failures.append(f"{regime} perft 5: {bad[:3]}")
        results[regime] = got

        for key, want in EXPECTED[regime].items():
            have = got.get(key)
            status = "OK" if have == want else "MISMATCH"
            print(f"{regime:5s} {key:8s} got {have:>9} want {want:>9}  {status}", flush=True)
            if have != want:
                failures.append(f"{regime} {key}: got {have} want {want}")

    json.dump(results, open(os.path.join(outdir, "pc_pins.json"), "w"), indent=1)
    print()
    if failures:
        for f in failures:
            print("  FAIL " + str(f))
        print(f"RESULT: {len(failures)} mismatch(es) or bad option line(s)")
        sys.exit(1)
    print("RESULT: every published PC r15 number matched in every regime checked")


if __name__ == "__main__":
    main()
