#!/usr/bin/env python3
"""swarm seat 01: published ARITHMETIC IDENTITIES must close (S-F157).

The divides-rule (S-F126) checks one form: `A -> B = Rx`, i.e. a ratio derived from two listed values. That rule caught a
real defect, and the coordinator's instruction to "check cells rather than point estimates" makes the gap visible: the
decomposition that now carries the per-node result is published in TWO OTHER forms that nothing checks.

    product form      `A x B = C`        e.g. 0.9090 x 1.0693 = 0.9720   (node x per-node = wall)
    quotient form     `A / B = C`        e.g. 0.9715 / 0.9131 = 1.0640   (time / node = per-node)

Both are load-bearing: the product is the decomposition's claim that the arithmetic CLOSES, and the quotient is the cell
the coordinator asked to be verified. If either is mistyped, the figure is wrong in the same silent way a ratio is.

What this checks:
  * scans .md and .txt result files for the two forms;
  * recomputes and requires agreement to within a stated tolerance (0.002 absolute, which is 0.2 percentage points on a
    ratio near 1 — tighter than the rounding the pages use, loose enough not to fire on 4-decimal presentation);
  * reports the count examined, and ZERO is a failure (Trap 12).

What it does NOT check, stated so the silence is not read as coverage:
  * whether the two inputs are the RIGHT inputs for the identity (a correctly-computed product of wrong numbers passes);
  * values quoted to fewer decimals than the tolerance requires;
  * identities written in prose without the operator symbols.

Usage: check_identities.py [dir ...]
"""
import re
import sys
from pathlib import Path

TOL = 0.002

# A x B = C   |   A / B = C   -> capture (A, op, B, C)
IDENT = re.compile(
    r"([0-9]+\.[0-9]+)\s*([x\u00d7/])\s*([0-9]+\.[0-9]+)\s*=\s*\*{0,2}([0-9]+\.[0-9]+)")


def scan(paths):
    checked, bad = 0, []
    for root in paths:
        rp = Path(root)
        # dedupe: scanning "." with *.md plus */*.md can reach the same file by two patterns, which double-counts
        files = sorted(set(list(rp.glob("*.md")) + list(rp.glob("*.txt")) +
                           list(rp.glob("*/*.md")) + list(rp.glob("*/*.txt"))))
        for f in files:
            try:
                lines = f.read_text(errors="replace").splitlines()
            except OSError:
                continue
            for n, line in enumerate(lines, 1):
                for m in IDENT.finditer(line):
                    a, op, b, c = m.group(1), m.group(2), m.group(3), m.group(4)
                    av, bv, cv = float(a), float(b), float(c)
                    if op in ("x", "\u00d7"):
                        expect = av * bv
                        what = "%s x %s" % (a, b)
                    else:
                        if bv == 0:
                            continue
                        expect = av / bv
                        what = "%s / %s" % (a, b)
                    checked += 1
                    if abs(expect - cv) > TOL:
                        bad.append("%s:%d: %s claims %s, but it is %.4f" % (f, n, what, c, expect))
    return checked, bad


def main():
    # ONE root, because "." already reaches subdirectories via */*.md. My first version listed "." plus each
    # subdirectory, so every identity in those directories was examined twice and a single defect printed twice.
    # A doubled count is a small case of the same failure as a zero count: the number does not mean what it says.
    paths = [p for p in sys.argv[1:] if not p.startswith("-")] or ["."]
    checked, bad = scan(paths)
    print("arithmetic identities examined: %d" % checked)
    # Trap 12: zero examined is a failure, not a pass.
    if checked == 0:
        print("\nFAIL: examined 0 identities. Either none are published in this form, or the selector is wrong - and")
        print("those are indistinguishable from here. Trap 12.")
        return 1
    if bad:
        print("FAILURES (%d):" % len(bad))
        for b in bad[:8]:
            print("  " + b)
        print("\nVERDICT: a published identity does not close. The reader can do that arithmetic too.")
        print("LIMIT: this checks the arithmetic, not whether the inputs are the right quantities.")
        return 1
    print("\nVERDICT: every published product and quotient closes to within %g." % TOL)
    print("LIMIT: a correct product of WRONG inputs passes - this checks that the arithmetic closes, not that the")
    print("terms are the right terms. Attribution is still the writer's job.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
