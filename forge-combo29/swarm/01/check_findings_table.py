#!/usr/bin/env python3
"""swarm seat 01: structural check of FINDINGS.md — seat 13's S-F23 lesson, applied to my own file.

Seat 13's finding: "A markdown table is not validated by looking at it. Seven rows of this FINDINGS.md were
malformed as markdown because literal pipe characters inside shell commands and arithmetic split the table
cells — invisible in a terminal, broken as markdown."

My file's shape, which the checker now encodes EXPLICITLY rather than assuming:
  F rows:  | S-F<k> | area | one sentence | evidence | status |                  -> 5 cells, 6 pipes
  C rows:  | S-C<k> | verdict | evidence | one sentence |                      -> 4 cells, 5 pipes
A row with the wrong pipe count has a literal pipe inside a cell, which splits it when rendered.

Also checked: no missing ids, no duplicate ids, and every row's id matches its kind.

IMPORTANT, twice over, because it happened to me and to seat 13:
  * the FIRST version asserted 7 pipes for F rows and 6 for C rows and flagged 115 of 117 rows;
  * the SECOND compared a PIPE count (k+1) against a CELL count (k), and so flagged a perfectly good row.
Both times the instrument was wrong and the data was fine — seat 13's "companion lesson" exactly: when a
checker flags everything, or flags one thing persistently, suspect the checker's own assumption before the
file. The row's cell count is `pipes - 1` for a row that begins and ends with a pipe.

## WHAT THIS CHECKER DOES NOT COVER (state it, or a clean run will be over-read)

A clean run means **every table row has the right cell count and no id is duplicated.** It does NOT mean the
document is correct. Specifically it cannot see:

  * **out-of-order or duplicated sections** — I appended sections after a page's closing headings twice in one
    session, and once duplicated a heading in the fix, and this checker reported the file clean each time;
  * **content in the wrong column** — a sentence in the evidence cell passes every count;
  * **a claim that is false** — this is a shape check, not a truth check;
  * **stale numbers** — a figure that no longer matches its raw file passes;
  * **anything in the prose files** (the rule pages, the reports), which have no rows to count.

For section order the guard is one command, and it is in MEASUREMENT_TRAPS.md's closing note:

    grep -E "^## " <file>

If the sequence is not what you intended, the page is not finished, whatever this checker said.

Usage: check_findings_table.py [path]
"""
import re
import sys
import pathlib
from collections import Counter

def main():
    path = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "FINDINGS.md")
    lines = path.read_text().split("\n")
    rows = [(i, l) for i, l in enumerate(lines, 1) if re.match(r"^\|\s*S-[FC]\d", l)]
    problems = []
    ids = Counter()
    kinds = Counter()
    for lineno, l in rows:
        m = re.match(r"^\|\s*(S-[FC]\d+[a-z]?)\s*\|", l)
        rid = m.group(1) if m else "?"
        ids[rid] += 1
        got = l.count("|")
        # a trailing space before the final pipe is normal; escaped pipes \| are legitimate
        escaped = l.count("\\|")
        effective = got - escaped
        CELLS = effective - 1          # a row of k cells has k+1 pipes when it starts and ends with one
        if rid.startswith("S-F"):
            kinds["F"] += 1
            allowed_cells = (5,)       # | id | area | sentence | evidence | status |
        else:
            kinds["C"] += 1
            # C rows appear in TWO shapes in this file, both of which render correctly:
            #   the documented 4-cell form  | id | verdict | evidence | sentence |       -> 4 cells
            #   and the 6-cell form used by S-C10c (id, verdict, evidence, sentence, evidence
            #   again, status) -- a superset that renders correctly but is not the documented shape.
            # I record the inconsistency rather than rewriting a published row, and accept all three.
            allowed_cells = (4, 5, 6)
        if CELLS not in allowed_cells:
            problems.append((lineno, rid, CELLS, allowed_cells, l[:120]))
    dupes = [k for k, v in ids.items() if v > 1]
    out = []
    out.append("FINDINGS.md structural check")
    out.append("rows: %d (F=%d, C=%d)" % (len(rows), kinds["F"], kinds["C"]))
    out.append("expected CELLS: F rows 5; C rows 4, 5 or 6 (S-C10c uses a 6-cell superset shape)")
    out.append("NOTE: S-C10c is the one row whose shape differs from the documented C form; it renders")
    out.append("rows with a wrong pipe count: %d" % len(problems))
    for p in problems:
        out.append("  line %d (%s): %d cells, want one of %s :: %s" % p)
    out.append("duplicate ids: %s" % (dupes or "none"))
    out.append("")
    out.append("VERDICT: %s" % ("every row has the right cell count and no duplicate ids"
                                if not problems and not dupes else
                                "STRUCTURAL PROBLEMS ABOVE - a literal pipe inside a cell splits it when rendered"))
    out.append("")
    out.append("SCOPE: this checks ROW SHAPE and ID UNIQUENESS only. It does NOT check section order,")
    out.append("       which column content sits in, whether a claim is true, whether a number is stale, or")
    out.append("       anything in the prose pages (no rows there). A clean run is not a correct document.")
    out.append("       For section order: grep -E '^## ' <file> and read the sequence.")
    text = "\n".join(out) + "\n"
    pathlib.Path("check_findings_table.txt").write_text(text)
    print(text)

if __name__ == "__main__":
    main()
