#!/usr/bin/env python3
"""Run one of the nine Job 18 matches with the pinned Job 16 harness."""

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
    dose48 = swing(48)
    dose48_cap200 = swing(48, 200)
    zero = swing(0)
    matches = {
        # games, seed, workers, nodes A, nodes B, extra options A and B
        "K7": (100, 7181, 4, 2000, 2000, dose48, dose48),
        "C7": (200, 7182, 4, 10000, 20000, (), ()),
        "E48kr": (2000, 7183, 2, 2000, 2000, dose48, zero),
        "D48v24": (2000, 7184, 2, 2000, 2000, dose48, swing(24)),
        "E64k": (2000, 7185, 2, 2000, 2000, swing(64), zero),
        "X400k48": (2000, 7186, 2, 2000, 2000, swing(48, 400), dose48_cap200),
        "X100k48": (2000, 7187, 2, 2000, 2000, swing(48, 100), dose48_cap200),
        "E48t": (2000, 7188, 2, 10000, 10000, dose48, zero),
        "E24t": (2000, 7189, 2, 10000, 10000, swing(24), zero),
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
