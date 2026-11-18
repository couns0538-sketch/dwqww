#!/usr/bin/env python3
"""Run one of the seven Job 21 matches with the pinned dual-preflight harness."""

from pathlib import Path
import sys

PCA_SHA256 = "49b56941b2acc0c2b9272c4e14992f2561c9ef71dbaf3da74a8a684ae8bc416a"
COUNTING_MATCHES = ("E64tr2", "E64w")


def main():
    here = Path(__file__).resolve().parent
    for job16 in (here.parent / "job16", here.parent / "sol-job16"):
        if (job16 / "run_match16.py").is_file():
            sys.path.insert(0, str(job16))
            break
    else:
        raise SystemExit("Job 16 run_match16.py is missing from the adjacent job16 or sol-job16 directory")

    import run_match16

    swing = run_match16.swing
    fhb0 = (*swing(0), ("FailHighBlend", "0"))
    fhb1 = (*swing(0), ("FailHighBlend", "1"))
    fhb3 = (*swing(0), ("FailHighBlend", "3"))
    fhb7 = (*swing(0), ("FailHighBlend", "7"))
    matches = {
        # games, seed, workers, nodes A, nodes B, extra options A and B
        "K10": (100, 7211, 4, 2000, 2000, fhb3, fhb3),
        "C10": (200, 7212, 4, 10000, 20000, fhb0, fhb0),
        "E64tr2": (2000, 7213, 2, 10000, 10000, swing(64), swing(0)),
        "F7kr": (2000, 7214, 2, 2000, 2000, fhb7, fhb0),
        "F3k": (2000, 7215, 2, 2000, 2000, fhb3, fhb0),
        "F1k": (2000, 7216, 2, 2000, 2000, fhb1, fhb0),
        "E64w": (2000, 7217, 2, 20000, 20000, swing(64), swing(0)),
    }
    previous, description = run_match16.MATCHES, run_match16.__doc__
    original_digest, original_run = run_match16.ENGINE_SHA256, run_match16.run

    def run_with_engine_pin(args):
        if args.match not in COUNTING_MATCHES:
            run_match16.ENGINE_SHA256 = PCA_SHA256
        try:
            return original_run(args)
        finally:
            run_match16.ENGINE_SHA256 = original_digest

    run_match16.MATCHES = matches
    run_match16.__doc__ = __doc__
    run_match16.run = run_with_engine_pin
    try:
        return run_match16.main()
    finally:
        run_match16.MATCHES = previous
        run_match16.__doc__ = description
        run_match16.run = original_run


if __name__ == "__main__":
    raise SystemExit(main())
