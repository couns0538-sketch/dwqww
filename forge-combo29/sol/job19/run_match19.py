#!/usr/bin/env python3
"""Run one of the six Job 19 matches with the pinned Job 16 harness."""

from pathlib import Path
import sys


def main():
    work = Path(__file__).resolve().parent.parent
    for job16 in (work / "job16", work / "sol-job16"):
        if (job16 / "run_match16.py").is_file():
            sys.path.insert(0, str(job16))
            break
    else:
        raise SystemExit("Job 16 run_match16.py is missing from the adjacent job16 or sol-job16 directory")

    import run_match16

    swing = run_match16.swing
    zero = swing(0)
    dose48 = swing(48)
    dose64 = swing(64)
    matches = {
        # games, seed, workers, nodes A, nodes B, extra options A and B
        "K8": (100, 7191, 4, 2000, 2000, dose64, dose64),
        "C8": (200, 7192, 4, 10000, 20000, zero, zero),
        "E64kr": (2000, 7193, 2, 2000, 2000, dose64, zero),
        "E48tr": (2000, 7194, 2, 10000, 10000, dose48, zero),
        "E64t": (2000, 7195, 2, 10000, 10000, dose64, zero),
        "E48w": (2000, 7196, 2, 20000, 20000, dose48, zero),
    }
    previous, description = run_match16.MATCHES, run_match16.__doc__
    run_match16.MATCHES = matches
    run_match16.__doc__ = __doc__
    try:
        return run_match16.main()
    finally:
        run_match16.MATCHES = previous
        run_match16.__doc__ = description


if __name__ == "__main__":
    raise SystemExit(main())
