#!/usr/bin/env python3
"""Catch the two document defects that no content check reaches, mechanically where it can.

The record is explicit that most prose defects need cold reading, but TWO of them have
a mechanical shadow and every instance in this run had it:

  1. A CORRECTION THAT ADDS WITHOUT REMOVING leaves the old sentence standing beside the
     new one. Its shadow is a line -- or a line-fragment -- that appears twice in a
     neighbourhood where a re-edit happened.
  2. A STALE FIGURE survives the sentence that quoted it. Its shadow is the same figure
     written in two forms (the record's case: a range hyphenated and en-dashed).

This checker does the mechanical parts only and SAYS SO: a pass here is not a clean
bill. It reports:
  - repeated non-trivial lines within a window (the add-without-remove shadow),
  - near-duplicate consecutive sentence openings (the fragment case),
  - a number written with both a hyphen and an en-dash range,
  - every figure of 4+ digits, for human review against its source.

The last item is the important one and it is deliberately NOT a verdict: printing the
population is stronger than claiming completeness (the record's own rule).

Usage: python3 check_doc.py <findings.md>
Exit 0 = no mechanical defect found. Exit 1 = one of the three checks fired.
Exit 2 = the file could not be read (never silently a pass).
"""
import re
import sys


def normalise(line):
    return re.sub(r"[^a-z0-9 ]", "", line.lower()).strip()


def is_table_row(line):
    return line.lstrip().startswith("|")


def main():
    path = sys.argv[1]
    try:
        lines = open(path, errors="replace").read().split("\n")
    except OSError as exc:
        print(f"cannot read {path}: {exc}")
        return 2

    defects = []

    # 1. repeated non-trivial lines inside a window of 40 lines
    seen = {}
    for i, line in enumerate(lines):
        n = normalise(line)
        if len(n) < 45:
            continue
        if n.startswith(("cursor subagentid", "---")):
            continue
        if n in seen and i - seen[n] < 40:
            defects.append(f"repeat: line {i+1} duplicates line {seen[n]+1}: {line.strip()[:80]}")
        seen[n] = i

    # 2. a duplicated 5-WORD SEQUENCE inside a local window (the fragment left by an edit
    #    that added without removing).
    #
    #    The first two shapes I tried were both wrong and both were caught by running them
    #    on fixtures with known answers:
    #    (a) comparing the first five CHARACTERS of adjacent lines fired on ordinary prose
    #        wrapping ('worker_limits...' vs '`workers_.front()`...' share "worke");
    #    (b) comparing the first five WORDS of adjacent lines MISSED the real defect,
    #        because the duplicated text ('not just from the source line') sat in the
    #        MIDDLE of the new sentence and only at the START of the leftover.
    #    A shingle check catches both without knowing where in the sentence the copy sits.
    #    Table rows are excluded: two rows of one table legitimately share short phrases.
    W = 5
    window = 30
    grams = {}
    body_lines = [(i, l) for i, l in enumerate(lines) if not is_table_row(l)]
    for pos, (i, line) in enumerate(body_lines):
        if line.lstrip().startswith("#"):
            grams = {}          # a heading legitimately restates its section's subject;
            continue            # reset so the opening sentence is not scored against it
        words = normalise(line).split()
        for j in range(len(words) - W + 1):
            g = " ".join(words[j:j + W])
            if g in grams and pos - grams[g][0] <= window:
                pi = grams[g][1]
                defects.append(f"repeat: 5-gram {g!r} appears at lines {pi+1} and {i+1}")
            grams[g] = (pos, i)

    # 3. the same range written with a hyphen in one place and an en-dash in another
    body = "\n".join(l for l in lines if not is_table_row(l))
    hy = set(re.findall(r"\b(\d[\d,]*)-(\d[\d,]*)\b", body))
    en = set(re.findall(r"\b(\d[\d,]*)\u2013(\d[\d,]*)\b", body))
    for h in {h for h in hy if h in en}:
        defects.append(f"figure: range {h[0]}-{h[1]} appears with both hyphen and en-dash")

    print(f"lines examined: {len(lines)}  (table rows excluded from checks 2 and 3)")
    for d in defects:
        print(f"  {d}")

    # 4. the population of large figures, printed for human review (not a verdict).
    #    `file:line` citations are stripped first: their line numbers are not figures
    #    about the engine and would bury the ones that are.
    stripped = re.sub(r"[\w./]+\.(?:cpp|hpp|md|py|json|jsonl|txt):\d+(?:-\d+)?", "", "\n".join(lines))
    stripped = re.sub(r"sha256 `[0-9a-f]+", "", stripped)
    figures = sorted({f for f in re.findall(r"\b\d{1,3}(?:,\d{3})+\b|\b\d{4,}\b", stripped)})
    print(f"\nfigures of 4+ digits / thousands-grouped, citations stripped: {len(figures)}")
    print("  " + "  ".join(figures))

    print(f"\nVERDICT: {'PASS (mechanical checks only)' if not defects else 'FAIL'}")
    return 0 if not defects else 1


if __name__ == "__main__":
    sys.exit(main())
