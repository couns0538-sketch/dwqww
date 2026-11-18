#!/usr/bin/env python3
"""Run one of the six Job 14 matches with the pinned Job 13 harness."""

from pathlib import Path
import sys

MATCHES = {
    # games, seed, concurrency, nodes A, nodes B, EvalSwingMult for A
    "K3": (100, 7121, 4, 20000, 20000, None),
    "C3": (200, 7122, 4, 10000, 20000, None),
    "E6b": (2000, 7124, 2, 20000, 20000, "6"),
    "E3k2": (2000, 7123, 2, 2000, 2000, "3"),
    "E6k": (2000, 7125, 2, 2000, 2000, "6"),
    "E12k": (2000, 7126, 2, 2000, 2000, "12"),
}


def main():
    work = Path(__file__).resolve().parent.parent
    for job13 in (work / "job13", work / "sol-job13"):
        if (job13 / "run_match13.py").is_file():
            sys.path.insert(0, str(job13))
            break
    else:
        raise SystemExit("Job 13 run_match13.py is missing from the adjacent job13 or sol-job13 directory")

    import run_match13

    run_match13.MATCHES = MATCHES
    run_match13.__doc__ = __doc__
    return run_match13.main()


if __name__ == "__main__":
    raise SystemExit(main())
