#!/usr/bin/env python3
"""Run one of the seven Job 24 matches with the pinned dual-preflight harness."""

from pathlib import Path
import sys

HISTORY_OFF = (("HistoryPruneDepth", "0"), ("HistoryPruneMultiplier", "2220"))
HISTORY_DEFAULT = (("HistoryPruneDepth", "3"), ("HistoryPruneMultiplier", "2220"))
HISTORY_HIGH_MULTIPLIER = (("HistoryPruneDepth", "3"), ("HistoryPruneMultiplier", "20000"))
NULL_BASE = (("NullMoveBase", "6"), ("NullMoveDepthDivisor", "3"))
NULL_DIVISOR = (("NullMoveBase", "5"), ("NullMoveDepthDivisor", "1"))
MATCHES = {
    # games, seed, workers, nodes A, nodes B, extra options A and B
    "K13": (100, 7241, 4, 2000, 2000, (), ()),
    "C13": (200, 7242, 4, 10000, 20000, (), ()),
    "L1": (1000, 7243, 2, 2000, 2000, HISTORY_OFF, HISTORY_HIGH_MULTIPLIER),
    "L2": (1000, 7244, 2, 2000, 2000, NULL_BASE, NULL_DIVISOR),
    "D2": (2000, 7245, 2, 2000, 2000, (("DrawJitter", "8"),), (("DrawJitter", "0"),)),
    "H2k": (2000, 7246, 2, 2000, 2000, HISTORY_OFF, HISTORY_DEFAULT),
    "H20": (1600, 7247, 2, 20000, 20000, HISTORY_OFF, HISTORY_DEFAULT),
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
