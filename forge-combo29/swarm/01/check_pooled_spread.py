#!/usr/bin/env python3
"""swarm seat 01: a pooled ratio must come with a per-position spread (S-F139).

Seat 19's audit supplied the rule and the reason: `CorrHistV2`'s pooled node saving is a genuine 5.2 %, but it wins on
only **54.2 %** of positions with quartiles **0.767-1.180** — an IQR **28x the effect size**. Reporting "5.2 %" alone
would describe a real pooled property as though it were a per-position one.

**A pooled ratio without a spread is the same class of deficiency as an extremum without a trace**: the number is
correct and the reader cannot tell what it means. So this check looks for pooled-ratio claims in the result files and
fails them when no spread accompanies them on the same row or in the same file.

What it accepts as a spread, any of: quartiles/Q1/Q3, min and max, a standard deviation, an interquartile range, a
per-position win rate, or an explicit "spread"/"distribution" statement carrying numbers.

LIMIT, stated because a check that overclaims is worse than one that does not exist: this verifies PRESENCE of spread
markers near a pooled figure, not that the spread is correctly computed or that it belongs to that figure. It catches
the omission, which is the failure seat 19 documented. It cannot catch a spread quoted from the wrong run.

Usage: check_pooled_spread.py [dir]
Exit 1 if any file reports a pooled ratio with no spread marker.

SCOPE / EXCLUSIONS (S-F142, Trap 13):
  scans:      *.txt at one directory level (the given dir and its immediate children)
  does NOT scan: *.md (prose may legitimately state a pooled figure with the spread in the
                 same paragraph), *.json, deeper nesting
  does NOT check: that the spread belongs to the pooled figure, only that one is nearby
"""
import re
import sys
from pathlib import Path

# a pooled ratio claim: "pooled ... 0.955", "total ... x 5.2 %", "ratio 0.926", "median 0.926" alone is NOT pooled
# A pooled ratio claim also includes the shape my own files use: "median node ratio 0.926", "median paired ratio
# 0.983", "mean ... ratio". Those aggregate a set the same way "pooled" does, and my first pattern missed all of them -
# the check examined ZERO lines and passed, which is Trap 8 inside the new check.
POOLED = re.compile(
    r"((?:pooled|aggregate|total nodes|overall)[^.\n]{0,60}?[0-9]+\.[0-9]+)"
    r"|((?:median|mean|geometric mean)[^.\n]{0,40}?ratio[^.\n]{0,20}?[0-9]+\.[0-9]+)",
    re.I)
SPREAD = re.compile(r"(quartile|Q1|Q3|IQR|interquartile|sd\s*[0-9]|stdev|standard deviation|min\s*[0-9]|\bmin\b.*\bmax\b"
                    r"|range\s*[0-9]|win[s]? on|favou?r the|% of positions|percent of positions|per-position)", re.I)


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    files = sorted(list(root.glob("*.txt")) + list(root.glob("*/*.txt")))
    problems = []
    checked = 0
    for f in files:
        try:
            text = f.read_text(errors="replace")
        except OSError:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if not POOLED.search(line):
                continue
            checked += 1
            # the spread may be on the same line or within the surrounding block of the file
            window = "\n".join(text.splitlines()[max(0, n - 4):n + 6])
            if not SPREAD.search(window):
                problems.append("%s:%d: pooled ratio with no spread nearby -> %s" % (f, n, line.strip()[:100]))
    print("pooled-ratio lines examined: %d" % checked)
    # TRAP 12 (S-F139): THE COUNT IS THE CHEAPEST SELF-TEST, and this check is the one that needed it. Its first
    # version examined ZERO lines and printed "every pooled ratio examined is accompanied by a spread marker" -
    # a pass over an empty set. Zero is now a failure.
    if checked == 0:
        print("\nFAIL: examined 0 rows. The selector matched nothing, so this verdict means nothing (Trap 12).")
        return 1
    if problems:
        print("FAILURES (%d):" % len(problems))
        for p in problems[:8]:
            print("  " + p)
        print("\nVERDICT: a pooled ratio was reported without a per-position spread.")
        print("LIMIT: presence of a spread marker only; not that it is the right spread for that figure.")
        return 1
    print("\nVERDICT: every pooled ratio examined is accompanied by a spread marker.")
    print("LIMIT: presence only. It cannot catch a spread quoted from the wrong run.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
