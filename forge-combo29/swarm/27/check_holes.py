#!/usr/bin/env python3
"""check_holes.py [dir]

Catches the class of damage that has hit this seat five times: a backtick (or shell metacharacter) inside an
`echo`/`printf` argument executes or is swallowed, leaving the sentence with a HOLE where content should be.
The text still reads as a sentence, which is why it survives proofreading.

DAMAGE SIGNATURE: in PROSE (not tables, not code fences, not headings), a doubled space between two words.
That is what a swallowed inline code span looks like: "every position already reports  at depth 10".

Deliberately narrow: my first version flagged 40 hits, all of them column alignment inside output tables.
Tables, code fences, headings and list markers are now excluded, and lines under 40 characters are skipped.
Still a heuristic — it reports candidates, and each one has to be read.
"""
import os
import re
import sys

MIN_LEN = 40


def prose_lines(path):
    """Yield (lineno, text) for prose lines only, tracking code fences."""
    in_fence = False
    try:
        lines = open(path, errors="replace").read().split("\n")
    except Exception:
        return
    for i, line in enumerate(lines, 1):
        t = line.strip()
        if t.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not t or t.startswith("|") or t.startswith("#"):
            continue
        if t.startswith("-") or t.startswith("*") or re.match(r"^\d+\.", t):
            continue
        if len(t) < MIN_LEN:
            continue
        yield i, line


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    hits = []
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if not fn.endswith((".md", ".txt")):
                continue
            path = os.path.join(dirpath, fn)
            for lineno, line in prose_lines(path):
                # a doubled space between two letters is the swallowed-code-span signature
                if re.search(r"[A-Za-z]  +[A-Za-z]", line):
                    hits.append((path, lineno, line.strip()[:140]))

    print("scanning %s for hole-shaped prose..." % root)
    print()
    for path, lineno, text in hits:
        print("%s:%d" % (path, lineno))
        print("   %s" % text)
    print()
    if not hits:
        print("no hole-shaped prose found (no doubled spaces between words outside tables/code)")
        return 0
    print("%d candidate(s). Read each: a doubled space in prose is usually a swallowed code span,"
          % len(hits))
    print("but a deliberate two-space spacing would look the same, so this is a screen, not a verdict.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
