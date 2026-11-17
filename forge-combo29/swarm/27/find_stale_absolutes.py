#!/usr/bin/env python3
"""find_stale_absolutes.py <findings.md>

Find rows that CONTAIN a correction pointing at another row, while still asserting the corrected thing.

THE PATTERN (named by the coordinator, fixed twice in this file as S-C87 and S-C100). A correction is appended to
a row without removing the sentence it corrects. The row then contains both the old absolute and the pointer to
its own refutation, four lines apart, and a reader skimming takes the first one because it is stated plainly and
the second one looks like a footnote.

That matters more than an ordinary stale sentence because the row is *about* being corrected: its presence makes
the finding look maintained, so nobody re-reads it.

WHAT IT DETECTS, per row:
  * a pointer to a later finding id (`S-Cxx` appearing inside the row's own text, where xx > the row's own)
    -> the row knows it is superseded
  * AND a phrase that asserts the pre-correction state without a qualifier nearby:
      "does NOT look", "always", "never", "no ... at all", "cannot", "is not a duplicate"
  * the qualifier test is crude on purpose: if the absolute phrase and the supersede-pointer are in the same
    row, the row is REPORTED so a human reads it. False positives are cheap here; a missed one is not.

CONTROLS:
  1. a row with a pointer AND a bare absolute IS reported
  2. a row with a pointer AND the absolute already qualified ("does not look ... in THIS cell") is NOT reported
  3. a row with no pointer is NOT reported even if it contains absolutes (those are S-C97's job, not this one's)
"""
import argparse
import re
import sys

ROW_RE = re.compile(r"^\|\s*(S-([A-Za-z])(\d+))\s*\|(.*)$")
ABS = [
    (r"\bdoes not look like a duplicate\b", "does not look like a duplicate"),
    (r"\bno duplicate signature\b", "no duplicate signature"),
    (r"\bcannot\b", "cannot"),
    (r"\bnever\b", "never"),
    (r"\balways\b", "always"),
    (r"\bno\b[^.|]{0,40}?\bat all\b", "no ... at all"),
]
# a qualifier that makes the absolute local rather than universal
QUAL = [
    r"\bTHIS cell\b", r"\bhere\b", r"\bin this (?:cell|row|case)\b",
    r"\babout \d+%", r"\bnot all\b", r"\bsuperseded\b", r"\bcorrected\b", r"\bwithdrawn\b",
    # a phrase that explicitly REJECTS the absolute is a qualification, not an instance of it.
    # Without these two, the fixed S-C87 tail read as a violation because it contains the words
    # "no duplicate signature" inside the sentence explaining why that phrase is wrong.
    r'\bnot[\s"]+none\b', r"\boften no\b", r"\bonly \d+ of \d+\b",
]


def rows(md):
    for ln in md.splitlines():
        m = ROW_RE.match(ln)
        if m:
            yield m.group(1), m.group(2), int(m.group(3)), m.group(4)


def scan(md):
    hits = []
    for rid, letter, num, body in rows(md):
        flat = " ".join(c.strip() for c in body.split("|") if c.strip())
        # pointers to OTHER findings of the same letter with a higher number
        ptrs = [p for p in re.findall(r"S-%s(\d+)" % letter, flat) if int(p) > num]
        if not ptrs:
            continue
        for pat, name in ABS:
            for m in re.finditer(pat, flat, re.I):
                window = flat[max(0, m.start() - 120):m.end() + 160]
                if any(re.search(q, window, re.I) for q in QUAL):
                    continue
                hits.append((rid, name, "superseded by S-%s%s" % (letter, max(ptrs)), window.strip()))
                break
            else:
                continue
            break
    return hits


def run_controls():
    ok = True

    def chk(n, c, d=""):
        nonlocal ok
        print("  %-58s %s %s" % (n, "PASS" if c else "FAIL", d))
        if not c:
            ok = False

    print("controls:")
    bad = "| S-C10 | a row that says the answer does NOT look like a duplicate. **SEE S-C20.** | x |"
    good = "| S-C10 | in THIS cell it does not look like a duplicate. **SEE S-C20.** | x |"
    noptr = "| S-C10 | the answer does NOT look like a duplicate, always. | x |"
    chk("1 pointer + bare absolute IS reported", len(scan(bad)) == 1)
    chk("2 pointer + qualified absolute is NOT reported", len(scan(good)) == 0)
    chk("3 no pointer is NOT reported (that is S-C97's job)", len(scan(noptr)) == 0)
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("findings")
    a = ap.parse_args()

    if not run_controls():
        print("\nCONTROLS FAILED - refusing to scan")
        sys.exit(2)

    md = open(a.findings, encoding="utf-8", errors="replace").read()
    hits = scan(md)
    if not hits:
        print("\nNo row both points at a later finding and asserts an unqualified absolute.")
        print("(0 findings - which is a result only because controls 1-3 passed.)")
        return
    for rid, name, ptr, window in hits:
        print("\n%s  [%s]  %s" % (rid, name, ptr))
        print("   ...%s..." % window[:280])
    print("\n%d candidate row(s) - read each and either qualify the absolute or remove it." % len(hits))


if __name__ == "__main__":
    main()
