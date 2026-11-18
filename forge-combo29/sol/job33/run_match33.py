#!/usr/bin/env python3
"""Run Job 33's pinned HG null-move mate guard matches."""

from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
for candidate in (HERE.parent / "job28", HERE.parent / "sol-job28"):
    if (candidate / "run_match28.py").is_file():
        sys.path.insert(0, str(candidate))
        break
else:
    raise SystemExit("Job 28's match harness is missing")

import run_match28

GUARD0 = (("HistoryAgeKeep", "1024"), ("NullMateGuard", "0"))
GUARD2 = (("HistoryAgeKeep", "1024"), ("NullMateGuard", "2"))
MATCHES = {
    "K23": (50, 7331, 4, 20000, 20000, GUARD0, GUARD0),
    "C23": (100, 7332, 4, 40000, 80000, GUARD0, GUARD0),
    "M7": (2000, 7333, 4, 20000, 20000, GUARD2, GUARD0),
    "M8": (500, 7334, 4, 80000, 80000, GUARD2, GUARD0),
}


def main():
    previous = run_match28.MATCHES, run_match28.HERE, run_match28.__doc__
    run_match28.MATCHES, run_match28.HERE, run_match28.__doc__ = MATCHES, HERE, __doc__
    try:
        return run_match28.main()
    finally:
        run_match28.MATCHES, run_match28.HERE, run_match28.__doc__ = previous


if __name__ == "__main__":
    raise SystemExit(main())
