#!/usr/bin/env python3
"""swarm seat 01: FORM 5, narrow half — verify a table row LABELLED "product" (S-F159).

`METHOD_NOTES.md` names five forms a claim can take and records that two have no check. This closes one of them: **the
table row**, which is how my single most load-bearing result was presented (node ratio, per-node ratio, product, observed
wall) and which `check_identities.py` cannot see because the operands and the result sit on different lines.

The table is tractable precisely because the rows are LABELLED. A row whose label contains "product" and two rows whose
labels contain a ratio-like word give the identity: product = ratio_1 x ratio_2. Similarly a "quotient"/"implied" row with
two inputs gives product = a / b.

What this checks:
  * finds markdown tables whose rows match `| label | **value** ... |`;
  * when a table contains a row labelled exactly "product" and at least two factor-like rows, verifies
    product = a x b to TOL;
  * reports how many such tables it examined, and ZERO is a failure (Trap 12).

What it does NOT check, stated so its silence is not read as coverage:
  * WHICH two rows are the factors when a table has more than two ratio-like rows - it takes the first two in order and
    says so, so a table where the factors are not adjacent could pass on the wrong pair;
  * prose claims, inline identities (`check_identities.py` owns those), or arithmetic inside a fenced code block;
  * whether the labels mean what the words say;
  * **any QUOTIENT claim in table form** — see the note in the code: a quotient row's label vocabulary is ambiguous
    ("implied", "derived", "per-node" all occur), and treating them as identity claims produced a false positive on my
    own three-route table. The quotient form is checked only when written inline, by `check_identities.py`.

Usage: check_table_identities.py [file ...]
"""
import re
import sys
from pathlib import Path

TOL = 0.002

ROW = re.compile(r"^\|\s*(.+?)\s*\|\s*\**([0-9]+\.[0-9]+)\**")
# ONLY the "product" label is treated as an identity claim. My first version also matched "implied"/"derived" as a
# quotient row, and it fired on my own PER_NODE_CELL table - which lists three ROUTES to the same quantity, not an
# identity. That was a false positive, and the honest fix is to narrow the claim rather than tune the pattern until my
# page passes: a row labelled "product" unambiguously asserts a product; a row labelled "implied" asserts nothing about
# the other rows. So the quotient form in tables is NOT checked, and the docstring says so.
PRODUCT_LABEL = re.compile(r"^\s*\**\s*product\s*\**\s*$", re.I)
# a row whose label reads like one of the factors
FACTOR_LABEL = re.compile(r"ratio|rate|per-node|per node|saving|cost|time|node|wall", re.I)


def parse_tables(lines):
    """Yield (start_line, rows) for each markdown table. A table is consecutive lines starting with '|'."""
    block, start = [], None
    for n, line in enumerate(lines, 1):
        if line.lstrip().startswith("|"):
            if start is None:
                start = n
            block.append((n, line))
        else:
            if block:
                yield start, block
            block, start = [], None
    if block:
        yield start, block


def classify(rows):
    """Split a table's rows into (factors, product_row, quotient_row)."""
    factors, prod, quot = [], None, None
    for n, line in rows:
        m = ROW.match(line.strip())
        if not m:
            continue
        label, value = m.group(1), float(m.group(2))
        if PRODUCT_LABEL.search(label):
            prod = (n, label, value)
        elif FACTOR_LABEL.search(label):
            factors.append((n, label, value))
    return factors, prod, quot


def main():
    files = sys.argv[1:] or [str(p) for p in sorted(Path(".").glob("*/*.md")) + sorted(Path(".").glob("*.md"))]
    examined, bad = 0, []
    for fn in files:
        p = Path(fn)
        if not p.exists():
            continue
        lines = p.read_text(errors="replace").splitlines()
        for start, rows in parse_tables(lines):
            factors, prod, quot = classify(rows)
            if prod and len(factors) >= 2:
                examined += 1
                a, b = factors[0][2], factors[1][2]
                expect = a * b
                if abs(expect - prod[2]) > TOL:
                    bad.append("%s:%d (table at %d): product row says %.4f, but %s x %s = %.4f"
                               % (fn, prod[0], start, prod[2], factors[0][1][:22], factors[1][1][:22], expect))

    print("labelled-table identities examined: %d" % examined)
    if examined == 0:
        print("\nFAIL: examined 0 tables carrying a product row beside factors (Trap 12).")
        return 1
    if bad:
        print("FAILURES (%d):" % len(bad))
        for b in bad[:8]:
            print("  " + b)
        print("\nVERDICT: a table row's arithmetic does not close.")
        print("LIMIT: takes the FIRST TWO factor-labelled rows; a table whose factors are not adjacent could")
        print("       pass on the wrong pair.")
        return 1
    print("\nVERDICT: every labelled-table PRODUCT closes to within %g." % TOL)
    print("LIMIT: it assumes the first two factor-labelled rows are the operands. A table with three or more")
    print("       such rows could be verified against the wrong pair - stated here rather than discovered later.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
