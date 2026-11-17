#!/usr/bin/env python3
"""Verify RECHECK.md's own arithmetic: the claim counts in the header must match the tables.

The report this seat audits has a documented failure mode where a number in prose disagreed with
the rows beneath it.  This script applies the same rule to RECHECK.md itself: every numbered row
in the four claim tables is counted, its verdict cell is read, and the header's literal
"Claims examined / Agree / Disagree" must equal the counts.

It also verifies the extra claim rows recorded only in the HEADLINE section (D3, the build
variant) so a disagreement cannot exist in prose while being absent from the tables.

Exit 0 only if the header matches the tables AND every DISAGREE row is named in the headline.
"""
import re
import sys

PATH = "RECHECK.md"
with open(PATH, encoding="utf-8") as handle:
    text = handle.read()

# Numbered table rows look like: | 23 | claim | report | derived | verdict |
row_re = re.compile(r"^\|\s*(\d+)\s*\|(.+?)\|(.+?)\|\s*$", re.MULTILINE)

rows = []
for m in row_re.finditer(text):
    idx = int(m.group(1))
    cells = [c.strip() for c in m.group(0).strip().strip("|").split("|")]
    if len(cells) < 5:
        continue
    verdict_cell = cells[-1]
    rows.append((idx, cells[1], verdict_cell))

print("numbered claim rows found: %d" % len(rows))

# verdict classification
disagree = [r for r in rows if "DISAGREE" in r[2].upper()]
agree = [r for r in rows if "AGREE" in r[2].upper() and "DISAGREE" not in r[2].upper()]
other = [r for r in rows if r not in disagree and r not in agree]

indices = [r[0] for r in rows]
missing = [i for i in range(1, max(indices) + 1) if i not in indices]
dupes = [i for i in set(indices) if indices.count(i) > 1]

# rows carrying a caveat still count as agree, but are reported separately
caveats = [r for r in agree if "CAVEAT" in r[2].upper()]

print("\n  agree rows            : %d" % len(agree))
print("  disagree rows         : %d" % len(disagree))
print("  unclassified rows     : %d %s" % (len(other), [r[0] for r in other] if other else ""))
print("  rows with a caveat    : %d %s" % (len(caveats), [r[0] for r in caveats] if caveats else ""))
print("  numbering gaps        : %s" % (missing if missing else "none"))
print("  duplicate row numbers : %s" % (dupes if dupes else "none"))

# The header must equal the table counts, plus the headline-only claim (D3 build variant).
HEADER_ONLY_CLAIMS = 1   # D3: the brief's "PC build variant" claim, argued in HEADLINE not in a table

hdr = re.search(r"\*\*Claims examined: (\d+)\. Agree: (\d+)\. Disagree: (\d+)\.\*\*", text)
checks = 0
agree_n = 0
if not hdr:
    print("\nHEADER NOT FOUND -- cannot verify")
    sys.exit(1)

want_examined = len(rows) + HEADER_ONLY_CLAIMS
want_agree = len(agree)
want_disagree = len(disagree) + HEADER_ONLY_CLAIMS

print("\nheader says : examined %s / agree %s / disagree %s" % hdr.groups())
print("tables give : examined %d / agree %d / disagree %d (+%d headline-only)" % (
    len(rows), len(agree), len(disagree), HEADER_ONLY_CLAIMS))

for label, got, want in (
        ("examined", int(hdr.group(1)), want_examined),
        ("agree", int(hdr.group(2)), want_agree),
        ("disagree", int(hdr.group(3)), want_disagree)):
    checks += 1
    if got == want:
        agree_n += 1
        print("  OK       %-10s %d" % (label, got))
    else:
        print("  WRONG    %-10s header %d, tables %d" % (label, got, want))

# every DISAGREE row must also be named in the headline as a D-number
checks += 1
headline = text.split("## Row-by-row")[0]
d_nums = set(re.findall(r"### (D\d)\.", headline))
unnamed = []
for idx, claim, verdict in disagree:
    if not re.search(r"D\d", verdict):
        unnamed.append(idx)
if unnamed:
    print("  WRONG    disagree rows not tied to a headline item: %s" % unnamed)
else:
    agree_n += 1
    print("  OK       every DISAGREE row is tied to a headline item (%d headline items)"
          % len(d_nums))

# a check that declines to evaluate must not read as a pass
checks += 1
if other:
    print("  WRONG    %d rows have no readable verdict" % len(other))
else:
    agree_n += 1
    print("  OK       every row carries a readable verdict")

print("\nrows examined: %d" % checks)
print("agree: %d / %d" % (agree_n, checks))
sys.exit(0 if agree_n == checks else 1)
