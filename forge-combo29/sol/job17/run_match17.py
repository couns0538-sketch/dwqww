#!/usr/bin/env python3
"""Run one of the eight Job 17 matches with the pinned Job 16 harness."""

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
    equal = swing(3, 400)
    dose6 = swing(6, 200)
    dose3 = swing(3, 200)
    matches = {
        # games, seed, workers, nodes A, nodes B, extra options A and B
        "K6": (100, 7171, 4, 2000, 2000, equal, equal),
        "C6": (200, 7172, 4, 10000, 20000, (), ()),
        "X400r": (2000, 7173, 2, 2000, 2000, swing(6, 400), dose6),
        "E24kr": (2000, 7174, 2, 2000, 2000, swing(24), swing(0)),
        "X400m3": (2000, 7175, 2, 2000, 2000, swing(3, 400), dose3),
        "X100m3": (2000, 7176, 2, 2000, 2000, swing(3, 100), dose3),
        "E48k": (2000, 7177, 2, 2000, 2000, swing(48), swing(0)),
        "X400w": (1600, 7178, 2, 20000, 20000, swing(6, 400), dose6),
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
