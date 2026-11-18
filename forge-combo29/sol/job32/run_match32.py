#!/usr/bin/env python3
"""Run Job 32's pinned HG null-move mate guard matches."""

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
    "K22": (100, 7321, 4, 2000, 2000, GUARD0, GUARD0),
    "C22": (200, 7322, 4, 1000, 2000, GUARD0, GUARD0),
    "M5": (8000, 7323, 4, 2000, 2000, GUARD2, GUARD0),
    "M6": (2000, 7324, 4, 20000, 20000, GUARD2, GUARD0),
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
