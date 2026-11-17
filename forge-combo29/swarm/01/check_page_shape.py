#!/usr/bin/env python3
"""swarm seat 01: page-SHAPE check for the prose files — the guard for the gap the row checker cannot cover.

Why this exists: I appended sections after a page's closing content THREE times in one session (Trap 3,
Trap 5, and the `readyok` section), and once duplicated a heading while fixing it. `check_findings_table.py`
reported every one of those files "clean", because it only counts table cells. The coordinator's suggestion
was to make the heading listing part of a script's output rather than a step to remember — this is that.

What it checks, per file:
  * the heading sequence, printed so a human can read the ORDER at a glance;
  * duplicate headings (a section appended twice, or a merge that left both copies);
  * a "closing" heading followed by more top-level sections — the specific reflex that bit me, since a page
    whose last two sections are a summary/checklist/guard and then a new topic reads as broken;
  * empty sections (a heading immediately followed by another heading).

It does NOT check content, correctness, or whether the order is the RIGHT order — only that it is a deliberate
sequence with no duplicates and nothing stranded after the closing material.

Usage: check_page_shape.py [files...]   (defaults to the rule pages in this folder)

SCOPE / EXCLUSIONS (S-F142, Trap 13):
  scans:      the *.md files named on the command line, or the DEFAULT list
  does NOT scan: *.txt, *.json (no headings to check) and STATUS.md BY DESIGN - it is an
                 append-only log where a block legitimately follows closing material
  does NOT check: intent, whether a section belongs where it is, or prose quality
"""
import pathlib
import re
import sys
from collections import Counter

# DEFAULT derives from a glob rather than being a hand-maintained list. It WAS a hand-written list of 11 pages,
# which meant a page added later was invisible to a manual run - the generated-list omission of Trap 14 in its
# mildest form. The gate passes explicit paths so it was never affected; this fixes the manual-invocation default.
DEFAULT = sorted(str(p) for p in pathlib.Path(__file__).parent.glob("*.md")
                 if p.name != "STATUS.md")  # STATUS.md is an append-only log; the page rule does not apply
# headings that read as closing material: nothing new should follow them
CLOSING = re.compile(r"(the guard|one-minute version|checklist|the rule for a harness|consequence in one line|"
                     r"why this is worth a page|what it costs a harness)", re.I)


def main():
    here = pathlib.Path(__file__).parent
    files = sys.argv[1:] or DEFAULT
    problems = []
    lines_out = []
    for name in files:
        p = here / name
        if not p.exists():
            problems.append("%s: MISSING" % name)
            continue
        heads = [(i, l.rstrip()) for i, l in enumerate(p.read_text().split("\n"), 1)
                 if re.match(r"^#{2,3} ", l)]
        lines_out.append("== %s  (%d headings)" % (name, len(heads)))
        for _, h in heads:
            lines_out.append("   " + h)
        counts = Counter(h for _, h in heads)
        for h, n in counts.items():
            if n > 1:
                problems.append("%s: DUPLICATE heading x%d -> %s" % (name, n, h))
        # empty section: a heading immediately followed by another heading
        for (ln, h), (ln2, h2) in zip(heads, heads[1:]):
            if ln2 - ln == 1:
                problems.append("%s: EMPTY section (line %d) -> %s" % (name, ln, h))
        # closing material followed by a new topic
        for idx, (ln, h) in enumerate(heads):
            if CLOSING.search(h) and idx + 1 < len(heads):
                nxt = heads[idx + 1][1]
                if not CLOSING.search(nxt):
                    problems.append("%s: section appended AFTER closing material -> '%s' follows '%s'"
                                    % (name, nxt, h))
    lines_out.append("")
    lines_out.append("heading order is printed above - READ THE SEQUENCE; this tool cannot judge intent")
    if problems:
        lines_out.append("")
        lines_out.append("PROBLEMS (%d):" % len(problems))
        for x in problems:
            lines_out.append("  " + x)
    else:
        lines_out.append("")
        lines_out.append("no duplicate headings, no empty sections, nothing stranded after closing material")
    # TRAP 12 (S-F139): report how many files were examined, and treat zero as a failure. A checker that looked at
    # nothing is indistinguishable from one whose subject is clean, and only the count tells them apart.
    lines_out.append("files examined: %d" % len(files))
    text = "\n".join(lines_out) + "\n"
    (here / "check_page_shape.txt").write_text(text)
    print(text)
    if not files:
        print("FAIL: examined 0 files (Trap 12).")
        return 1
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
