#!/usr/bin/env python3
"""check_settings.py <exe> [--expect N]

THE CHECK that would have caught S-W7: a harness that *builds* a PC20 option list and then *applies* only part of
it, producing numbers that are real measurements of the wrong configuration.

It works by doing the honest thing — send every option, read back what the engine acknowledges, and count. Then it
asserts the count matches what the label promises:

    Hash, Threads, OwnBook, 14 S14 settings, 5 PC20 switches  =  22 options

If a harness sends fewer, its "PC20" label is false. Run this before trusting any settings label in a finding.

Also verifies that the engine ADVERTISES each option, so a typo'd name cannot silently do nothing.
"""
import argparse
import re
import subprocess
import sys
import time

S14 = ["LmrQuietBase value 93", "LmrQuietDivisor value 205", "LmrNoisyBase value 13",
       "LmrNoisyDivisor value 333", "LmrHistoryDivisor value 5643", "NullMoveBase value 5",
       "LmpBase value 8", "HistoryPruneMultiplier value 2220", "HistoryBonusQuadratic value 24",
       "HistoryBonusLinear value 54", "HistoryBonusMax value 2212", "SingularDepth value 6",
       "IirDepth value 2", "NonPawnCorrection value true"]
PC20X = ["CuckooRep value true", "HistRework value 2", "TtPruneV2 value true",
         "CorrHistV2 value true", "MateAlphaGuard value true", "OwnBook value false"]
BASE = ["Hash value 16", "Threads value 1"]
PC20 = BASE + S14 + PC20X


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--expect", type=int, default=len(PC20))
    a = ap.parse_args()

    p = subprocess.Popen([a.exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(x):
        p.stdin.write(x + "\n"); p.stdin.flush()

    def until(pred, tmo=30):
        t0 = time.monotonic(); out = []
        while time.monotonic() - t0 < tmo:
            ln = p.stdout.readline()
            if not ln:
                break
            out.append(ln.rstrip())
            if pred(out[-1]):
                return out
        return out

    send("uci")
    uci = until(lambda x: x.strip() == "uciok")
    advertised = set()
    for line in uci:
        m = re.match(r"option name (.+?) type ", line)
        if m:
            advertised.add(m.group(1))

    sent, refused, bad = [], [], []
    for item in PC20:
        name = item.rsplit(" value ", 1)[0]
        if name not in advertised:
            bad.append(name)
            continue
        send("setoption name " + item)
        sent.append(name)
        send("isready")
        lines = until(lambda x: x.strip() == "readyok")
        for l in lines:
            if "unknown option" in l or "invalid value" in l:
                refused.append((name, l.strip()))

    send("quit")
    print("advertised options: %d" % len(advertised))
    print("PC20 list length  : %d" % len(PC20))
    print("options SENT      : %d" % len(sent))
    if bad:
        print("NOT ADVERTISED (a typo would silently do nothing): %s" % bad)
    if refused:
        print("REFUSED:")
        for n, l in refused:
            print("   %s -> %s" % (n, l))
    print()
    ok = True
    if len(sent) != a.expect:
        print("FAIL: sent %d options, expected %d -- your 'PC20' label is FALSE" % (len(sent), a.expect))
        ok = False
    if bad or refused:
        print("FAIL: an option was not accepted, so the configuration is not what the label says")
        ok = False
    if ok:
        print("PASS: all %d PC20 options advertised and accepted -- the label matches what was sent" % len(sent))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
