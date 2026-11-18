#!/usr/bin/env python3
"""Run one of the nine Job 22 matches with the pinned dual-preflight harness."""

from pathlib import Path
import sys

PCA_SHA256 = "49b56941b2acc0c2b9272c4e14992f2561c9ef71dbaf3da74a8a684ae8bc416a"
COUNTING_MATCHES = ("E64wr",)


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
    fhb = [(*swing(0), ("FailHighBlend", str(bitmask))) for bitmask in range(7)]
    matches = {
        # games, seed, workers, nodes A, nodes B, extra options A and B
        "K11": (100, 7221, 4, 2000, 2000, fhb[6], fhb[6]),
        "C11": (200, 7222, 4, 10000, 20000, fhb[0], fhb[0]),
        "F1kr": (2000, 7223, 2, 2000, 2000, fhb[1], fhb[0]),
        "F3kr": (2000, 7224, 2, 2000, 2000, fhb[3], fhb[0]),
        "F2k": (2000, 7225, 2, 2000, 2000, fhb[2], fhb[0]),
        "F4k": (2000, 7226, 2, 2000, 2000, fhb[4], fhb[0]),
        "F5k": (2000, 7227, 2, 2000, 2000, fhb[5], fhb[0]),
        "F6k": (2000, 7228, 2, 2000, 2000, fhb[6], fhb[0]),
        "E64wr": (2000, 7229, 2, 20000, 20000, swing(64), swing(0)),
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
