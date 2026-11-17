#!/usr/bin/env python3
"""swarm seat 01: check that every STATUS.md block stamp is a real clock reading.

I typed a future timestamp into STATUS.md twice in one session (00:52:10Z when the clock read 00:49Z, and
00:59:30Z when it read 00:56Z). Both were caught by hand. That is Trap 0 exactly: a hand-typed number and a
measured number look identical in the file, and "be careful" is not a mechanism — memory is what fails at the
moment of creation.

So this script checks two things a human reading the page would have to do by eye:

  1. **No stamp is in the future** relative to now (the error I actually made, twice).
  2. **Stamps are non-decreasing down the file**, since each block is appended.

It cannot check that a stamp is ACCURATE for when the block was written — only the writer can. But a future stamp
is proof of a fabrication, and out-of-order stamps mean a block was inserted rather than appended.

Usage: check_status_stamps.py STATUS.md [--now 2026-11-17T00:00:00Z]
Exit 1 on any problem, so it can gate a commit.
"""
import re
import sys
from datetime import datetime, timezone

STAMP = re.compile(r"^## (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)")


def main():
    path = sys.argv[1]
    now = datetime.now(timezone.utc)
    if "--now" in sys.argv:
        now = datetime.strptime(sys.argv[sys.argv.index("--now") + 1], "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc)

    stamps = []
    for i, line in enumerate(open(path, encoding="utf-8"), 1):
        m = STAMP.match(line)
        if m:
            stamps.append((i, m.group(1), datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc)))

    print("blocks with a stamp: %d" % len(stamps))
    problems = 0

    # 1. future stamps: a stamp later than the clock is not a rounding error, it is invented
    future = [(ln, s) for ln, s, d in stamps if d > now]
    if future:
        problems += len(future)
        print("FUTURE STAMPS (the clock reads %s):" % now.strftime("%Y-%m-%dT%H:%M:%SZ"))
        for ln, s in future:
            print("  line %-5d %s  -> %+d s ahead" % (ln, s, (datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
                                                             .replace(tzinfo=timezone.utc) - now).total_seconds()))

    # 2. order
    for (ln0, s0, d0), (ln1, s1, d1) in zip(stamps, stamps[1:]):
        if d1 < d0:
            problems += 1
            print("OUT OF ORDER: line %d (%s) then line %d (%s)" % (ln0, s0, ln1, s1))

    # 3. a stamp far in the past is not a failure, but flag a gap over 3 h as likely a stale paste
    for (ln0, s0, d0), (ln1, s1, d1) in zip(stamps, stamps[1:]):
        gap = (d1 - d0).total_seconds()
        if gap > 3 * 3600:
            print("NOTE: %.1f h between line %d (%s) and line %d (%s) - check it is not a stale paste"
                  % (gap / 3600.0, ln0, s0, ln1, s1))

    if problems:
        print("\nVERDICT: %d problem(s). A future stamp is a fabricated reading, not a rounding error." % problems)
        return 1
    print("\nVERDICT: every stamp is at or before the clock and stamps are in order."
          "\nLIMIT: this cannot tell whether a stamp is accurate for its block, only that it is possible.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
