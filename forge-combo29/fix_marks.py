#!/usr/bin/env python3
"""fix_marks.py -- repair git conflict markers in committed evidence files.

Usage: fix_marks.py [--check] FILE [FILE...]

For every conflicted file it keeps EVERY line of both sides, drops only the marker
lines (`<<<<<<<`, `=======`, `>>>>>>>`), and sorts the result by the timestamp or
number the line carries, so the same set of lines comes out in a stable order. Lines
with no recognisable time keep their relative order at the end.

--check prints nothing and exits 1 if any marker remains; that is the grep Opus asked
for, run over the job folder before every commit.
"""
import re
import sys

MARK = re.compile(r"^(<<<<<<<|=======|>>>>>>>)")
# 2026-11-16T17:44:40Z   or   Mon Nov 16 05:46:24 PM UTC 2026
ISO = re.compile(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})Z")
US = re.compile(r"[A-Z][a-z]{2} ([A-Z][a-z]{2}) +(\d{1,2}) (\d{2}):(\d{2}):(\d{2}) (AM|PM) UTC (\d{4})")
MONTHS = {m: i + 1 for i, m in enumerate(
    "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split())}
NODES = re.compile(r"nodes (\d+)")


def sort_key(line):
    m = ISO.search(line)
    if m:
        return (0, tuple(int(x) for x in m.groups()), line)
    m = US.search(line)
    if m:
        mon = MONTHS.get(m.group(1), 0)
        hour = int(m.group(3)) % 12 + (12 if m.group(6) == "PM" else 0)
        return (0, (int(m.group(7)), mon, int(m.group(2)), hour,
                    int(m.group(4)), int(m.group(5))), line)
    m = NODES.search(line)
    if m:
        return (1, (int(m.group(1)),), line)
    return (2, (), line)


def main():
    check = "--check" in sys.argv
    files = [a for a in sys.argv[1:] if a != "--check"]
    bad = 0
    for path in files:
        try:
            with open(path, encoding="utf-8") as fh:
                lines = fh.read().splitlines()
        except OSError as exc:
            print("%s: %s" % (path, exc), file=sys.stderr)
            continue
        marks = [l for l in lines if MARK.match(l)]
        if not marks:
            continue
        if check:
            bad += 1
            print("%s: %d marker line(s)" % (path, len(marks)))
            continue
        kept = [l for l in lines if l.strip() and not MARK.match(l)]
        # de-duplicate while preserving the set of distinct evidence lines
        seen, uniq = set(), []
        for l in kept:
            if l not in seen:
                seen.add(l)
                uniq.append(l)
        uniq.sort(key=sort_key)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(uniq) + "\n")
        print("%s: repaired, %d distinct line(s), %d marker line(s) removed"
              % (path, len(uniq), len(marks)))
    if check:
        return 1 if bad else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
