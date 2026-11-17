#!/usr/bin/env python3
"""swarm seat 01: FORM 4, rebuilt narrowly — a ratio with its percentage in the SAME parenthetical (S-F163).

`METHOD_NOTES.md` records that a broad prose-ratio checker was built and abandoned: 16 findings, almost all its own
fault. **That conclusion was too strong, and this file corrects it.** The instrument that caught a real error in my
headline (`0.9090` with `12.4 % fewer`, where 1 − 0.9090 = 9.10 %) was the broad checker — so abandoning the class
would have discarded the one thing that worked.

What separates the true positive from the false ones is not magnitude or tolerance but **grammatical form**. A ratio and
its percentage stated inside ONE parenthetical is an identity claim:

    0.9090 (12.4 % fewer nodes)          <- ratio, then paren, then percentage, then direction  => CHECKABLE
    0.530 us -> 0.578 us = 1.09x (9 %)   <- first decimal on the line is not the ratio            => NOT THIS FORM
    1.079-1.092x - 7.9-9.2 % dearer      <- a range has no single percentage                     => NOT THIS FORM

The three false-positive mechanisms the broad version hit are all excluded by requiring the ratio to be immediately
followed by the parenthetical. No adjacency guessing, no magnitude heuristic needed for correctness (it is kept only to
skip non-ratios).

Quoted regions (backticks, double quotes, fenced blocks) are stripped first: this page's own examples, and the
annotations that preserve the 0.9090 error as evidence, are quoted and must not be reported as violations.

What this does NOT check, so its silence is not coverage:
  * a percentage with no ratio in the same parenthetical - the commonest form on these pages;
  * whether the label ("nodes", "wall", "per node") names the right quantity.

Usage: check_ratio_percent.py [file ...]
"""
import re
import sys
from pathlib import Path

TOL_PP = 0.11  # set by one-decimal presentation and whole-number rounding, not by taste

# ratio, optional bold close, then a parenthetical opening, a percentage, and a direction word
CLAIM = re.compile(
    r"([0-9]+\.[0-9]+)\**\s*\(\**\s*([0-9]+\.?[0-9]*)\s*%\s*"
    r"(fewer|less|more|dearer|cheaper|faster|slower|higher|lower)", re.I)
DECREASING = {"fewer", "less", "cheaper", "faster", "lower"}


def strip_quoted(text):
    out, fenced = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            out.append("")
            continue
        if fenced:
            out.append("")
            continue
        s = re.sub(r"`[^`]*`", "", line)
        s = re.sub(r'"[^"]*"', "", s)
        out.append(s)
    return out


def main():
    files = sys.argv[1:] or [str(p) for p in sorted(
        set(list(Path(".").glob("*.md")) + list(Path(".").glob("*/*.md")) + list(Path(".").glob("*/*.txt"))))]
    examined, bad, skipped_range = 0, [], 0
    for fn in files:
        p = Path(fn)
        if not p.exists():
            continue
        for n, line in enumerate(strip_quoted(p.read_text(errors="replace")), 1):
            for m in CLAIM.finditer(line):
                ratio, pct, word = float(m.group(1)), float(m.group(2)), m.group(3).lower()
                if not (0.5 <= ratio <= 1.5):
                    # Counted, not silently dropped (23-F200's rule): a matched pattern whose number is not a ratio
                    # is a case I COULD NOT EVALUATE, and that must be visible rather than absent. It is not a
                    # failure - a non-ratio is legitimately outside this check's claim - but the count shows the
                    # boundary of the vocabulary instead of hiding it.
                    skipped_range += 1
                    continue
                examined += 1
                expect = (1 - ratio) * 100 if word in DECREASING else (ratio - 1) * 100
                if abs(expect - pct) > TOL_PP:
                    bad.append("%s:%d: ratio %.4f with '%s' implies %.2f %%, but the line says %.2f %%"
                               % (fn, n, ratio, word, expect, pct))

    print("ratio-with-percentage claims examined: %d" % examined)
    if skipped_range:
        print("matched but not evaluable (number outside the ratio range 0.5-1.5): %d" % skipped_range)
        print("  -> these are the VOCABULARY BOUNDARY of this check: reported so a reader sees what it could not")
        print("     evaluate, per 23-F200 (\"I could not evaluate this\" must never be reported as \"this is fine\").")
    if examined == 0:
        print("\nFAIL: examined 0 claims (Trap 12) - either none are written in this form or the selector is wrong.")
        return 1
    if bad:
        print("FAILURES (%d):" % len(bad))
        for b in bad[:8]:
            print("  " + b)
        print("\nVERDICT: a ratio and the percentage beside it disagree beyond rounding (%.2f pp)." % TOL_PP)
        return 1
    print("\nVERDICT: every ratio/percentage pair written in one parenthetical agrees to within %.2f pp." % TOL_PP)
    print("LIMIT: same-parenthetical form only. A percentage whose ratio is elsewhere on the line or page is")
    print("       unchecked - deciding which number is the ratio is how a checker invents an identity.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
