#!/usr/bin/env python3
"""Run one of the seven Job 15 matches with the pinned Job 13 harness."""

from pathlib import Path
import sys

MATCHES = {
    # games, seed, concurrency, nodes A, nodes B, EvalSwingMult for A
    "K4": (100, 7151, 4, 5000, 5000, None),
    "C4": (200, 7152, 4, 10000, 20000, None),
    "E6k2": (2000, 7154, 2, 2000, 2000, "6"),
    "E12k2": (2000, 7155, 2, 2000, 2000, "12"),
    "D12v3": (2000, 7156, 2, 2000, 2000, "12"),
    "E6m": (2000, 7157, 2, 5000, 5000, "6"),
    "E6t": (2000, 7158, 2, 10000, 10000, "6"),
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

    base, run = run_match13.BASE, run_match13.run

    def run_match(args):
        if args.match == "D12v3":
            # Job 13 appends A's override after BASE. B keeps the dose of 3.
            run_match13.BASE = (*base, ("EvalSwingMult", "3"))
        try:
            return run(args)
        finally:
            run_match13.BASE = base

    matches, description = run_match13.MATCHES, run_match13.__doc__
    run_match13.MATCHES = MATCHES
    run_match13.__doc__ = __doc__
    run_match13.run = run_match
    try:
        return run_match13.main()
    finally:
        run_match13.MATCHES = matches
        run_match13.__doc__ = description
        run_match13.run = run


if __name__ == "__main__":
    raise SystemExit(main())
