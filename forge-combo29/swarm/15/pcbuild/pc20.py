#!/usr/bin/env python3
"""pc20.py EXE [--label X]

Checks FABLE_TO_swarm_5's three known-answer rows on one build, each in a fresh process:
  none (no setoption)                  bench 11 312866, bench 13 862329, bench 16 3024920, perft5 4865609
  S14                                  bench 11 242796, bench 13 656517
  PC20 = S14 + CuckooRep/HistRework 2/TtPruneV2/CorrHistV2/MateAlphaGuard/OwnBook false
                                       bench 11 278024, bench 13 587276

Every option name is taken from the exe's own `uci` list and STOPPED ON if absent, so a missing
option can never be silently ignored (that is how a harness measures the wrong build).
A number that cannot be parsed is reported PARSE_FAIL, never 0.
"""
import argparse
import queue
import re
import subprocess
import threading

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

KNOWN = {
    "none": {11: 312866, 13: 862329, 16: 3024920, "perft5": 4865609},
    "S14": {11: 242796, 13: 656517},
    "PC20": {11: 278024, 13: 587276},
}


def uci_options(exe):
    out = subprocess.run([exe], input="uci\nquit\n", capture_output=True, text=True).stdout
    names = set()
    for line in out.splitlines():
        m = re.match(r"option name (.+?) type ", line)
        if m:
            names.add(m.group(1))
    return names, out


def run(exe, opts, tail_cmd, terminator_re, limit=900):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    q = queue.Queue()
    log = []

    def reader():
        for line in p.stdout:
            q.put(line.rstrip("\n"))
        q.put(None)

    threading.Thread(target=reader, daemon=True).start()
    cmds = ["uci"] + ["setoption name %s value %s" % (k, v) for k, v in opts] + \
           ["isready"] + tail_cmd
    for c in cmds:
        p.stdin.write(c + "\n")
    p.stdin.flush()
    import time
    t0 = time.monotonic()
    while True:
        rem = limit - (time.monotonic() - t0)
        if rem <= 0:
            break
        try:
            line = q.get(timeout=rem)
        except queue.Empty:
            break
        if line is None:
            break
        log.append(line)
        if re.search(terminator_re, line):
            break
    try:
        p.stdin.write("quit\n"); p.stdin.flush(); p.wait(timeout=10)
    except Exception:
        p.kill()
    return log


def last_nodes(log):
    vals = []
    for line in log:
        m = re.search(r"\bnodes\s+(\d+)", line)
        if m:
            vals.append(int(m.group(1)))
    return vals[-1] if vals else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    a = ap.parse_args()
    E = a.exe
    names, uciout = uci_options(E)
    print("exe: %s" % E, flush=True)
    print("id name: %s" % next((l for l in uciout.splitlines() if l.startswith("id name")), "?"),
          flush=True)
    print("options listed: %d" % len(names), flush=True)

    regimes = {
        "none": [],
        "S14": S14,
        "PC20": S14 + PC20_EXTRA,
    }
    ok_all = True
    for regime, opts in regimes.items():
        missing = [k for k, _ in opts if k not in names]
        if missing:
            print("\n%s: STOP - option(s) not in the exe's uci list: %s" % (regime, missing),
                  flush=True)
            ok_all = False
            continue
        print("\n=== %s (%d setoptions) ===" % (regime, len(opts)), flush=True)
        for d in (11, 13, 16):
            want = KNOWN[regime].get(d)
            if want is None:
                continue
            log = run(E, opts, ["bench %d" % d], r"\bnodes\s+\d+")
            n = last_nodes(log)
            verdict = "PARSE_FAIL" if n is None else ("MATCH" if n == want else "DIFFERS")
            if n != want:
                ok_all = False
            print("  bench %-2d got %-10s want %-10d %s" % (d, n if n is not None else "PARSE_FAIL",
                                                            want, verdict), flush=True)
        if regime == "PC20":
            for rname in ("none", "PC20"):
                pass
        log = run(E, opts, ["position startpos", "isready", "go perft 5"], r"\bnodes\s+\d+")
        n = last_nodes(log)
        want = 4865609
        verdict = "PARSE_FAIL" if n is None else ("MATCH" if n == want else "DIFFERS")
        print("  perft 5 got %-10s want %-10d %s" % (n if n is not None else "PARSE_FAIL", want,
                                                     verdict), flush=True)
    print("\nOVERALL: %s" % ("ALL ROWS MATCH" if ok_all else "SOME ROWS DIFFER OR STOPPED"),
          flush=True)


if __name__ == "__main__":
    main()
