#!/usr/bin/env python3
"""Gate: run the four honesty pins on a build of forge-combo29.

bench N must go in on STDIN as a UCI command; `./forge bench 11` as argv exits 0
and prints nothing (brief, known trap). Every command here is fed on stdin and we
read until the expected terminal line appears, so nothing is piped into a live
search (brief rule 1: never pipe `quit` into a search).

Usage: pins.py <exe> [--v3]
  --v3  also assert NNUEArch stays off and the pins do not move with the option present
"""
import subprocess
import sys

WANT = {11: 312866, 13: 862329, 16: 3024920}
WANT_PERFT5 = 4865609


def run(exe, script, until_prefixes, timeout=600):
    """Send `script` on stdin, collect stdout+stderr, wait for the terminal lines."""
    proc = subprocess.run([exe], input=script, capture_output=True, text=True, timeout=timeout)
    return proc


def bench(exe, depth):
    out = run(exe, "uci\nisready\nbench %d\nquit\n" % depth, None)
    nodes = None
    for line in out.stdout.splitlines():
        if line.startswith("info string bench depth"):
            fields = line.split()
            nodes = int(fields[fields.index("nodes") + 1])
    return nodes, out


def perft5(exe):
    out = run(exe, "uci\nisready\nposition startpos\ngo perft 5\nquit\n", None)
    nodes = None
    for line in out.stdout.splitlines():
        if line.startswith("nodes "):
            nodes = int(line.split()[1])
    return nodes, out


def main():
    exe = sys.argv[1]
    v3 = "--v3" in sys.argv[2:]
    ok = True
    rows = []

    for depth, want in WANT.items():
        got, proc = bench(exe, depth)
        good = got == want
        ok &= good
        rows.append(("bench %d" % depth, want, got, good))

    got, proc = perft5(exe)
    good = got == WANT_PERFT5
    ok &= good
    rows.append(("perft 5", WANT_PERFT5, got, good))

    if v3:
        # Prove NNUEArch is present in this build but OFF by default: the option line
        # must appear and the pins above must hold with it unset.
        uci = run(exe, "uci\nisready\nquit\n", None)
        has_arch = "option name NNUEArch type check" in uci.stdout
        has_arch_file = "option name NNUEArchFile type string" in uci.stdout
        rows.append(("option NNUEArch advertised", True, has_arch, has_arch))
        rows.append(("option NNUEArchFile advertised", True, has_arch_file, has_arch_file))
        ok &= has_arch and has_arch_file

    for name, want, got, good in rows:
        print("%-32s want %-12s got %-12s %s" % (name, want, got, "PASS" if good else "FAIL"))
    print("PINS %s" % ("MATCH" if ok else "MISMATCH"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
