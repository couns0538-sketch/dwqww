#!/usr/bin/env python3
"""Run one of the six Job 25 matches with the pinned dual-preflight harness."""

from pathlib import Path
import sys

JITTER_0 = (("DrawJitter", "0"),)
JITTER_8 = (("DrawJitter", "8"),)
MATCHES = {
    # games, seed, workers, nodes A, nodes B, extra options A and B
    "K14": (100, 7251, 4, 2000, 2000, (), ()),
    "C14": (200, 7252, 4, 10000, 20000, (), ()),
    "D2r": (4000, 7253, 2, 2000, 2000, JITTER_8, JITTER_0),
    "D2q": (2000, 7254, 2, 2000, 2000, (("DrawJitter", "4"),), JITTER_0),
    "D2o": (2000, 7256, 2, 2000, 2000, (("DrawJitter", "1"),), JITTER_0),
    "D20": (1600, 7255, 2, 20000, 20000, JITTER_8, JITTER_0),
}


def main():
    here = Path(__file__).resolve().parent
    for job16 in (here.parent / "job16", here.parent / "sol-job16"):
        if (job16 / "run_match16.py").is_file():
            sys.path.insert(0, str(job16))
            break
    else:
        raise SystemExit("Job 16 run_match16.py is missing from the adjacent job16 or sol-job16 directory")

    import run_match16

    previous, description = run_match16.MATCHES, run_match16.__doc__
    run_match16.MATCHES = MATCHES
    run_match16.__doc__ = __doc__
    try:
        return run_match16.main()
    finally:
        run_match16.MATCHES = previous
        run_match16.__doc__ = description


if __name__ == "__main__":
    raise SystemExit(main())
