#!/usr/bin/env python3
"""Use the Job 6 replay driver with the Job 8 cold-hard arm."""

from pathlib import Path
import sys


def main():
    work = Path(__file__).resolve().parent.parent
    # Support both the local scratch layout and the committed sol/jobN layout.
    for job6 in (work / "job6", work / "sol-job6"):
        if (job6 / "run_sweep.py").is_file():
            sys.path.insert(0, str(job6))
            break
    else:
        raise SystemExit("Job 6 run_sweep.py is missing from the adjacent job6 or sol-job6 directory")

    import run_sweep

    run_sweep.PROTOCOLS["cold-hard"] = ("hard", False)
    return run_sweep.main()


if __name__ == "__main__":
    raise SystemExit(main())
