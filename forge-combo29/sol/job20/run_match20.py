#!/usr/bin/env python3
"""Run one of the six Job 20 matches with the pinned dual-preflight harness."""

from pathlib import Path
import re
import sys


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
    fhb7 = (*swing(0), ("FailHighBlend", "7"))
    fhb0 = (*swing(0), ("FailHighBlend", "0"))
    matches = {
        # games, seed, workers, nodes A, nodes B, extra options A and B
        "K9": (100, 7201, 4, 2000, 2000, fhb7, fhb7),
        "C9": (200, 7202, 4, 10000, 20000, fhb7, fhb7),
        "F7k": (2000, 7203, 2, 2000, 2000, fhb7, fhb0),
        "F7t": (2000, 7204, 2, 10000, 10000, fhb7, fhb0),
        "E64tr": (2000, 7205, 2, 10000, 10000, swing(64), swing(0)),
        "F7w": (2000, 7206, 2, 20000, 20000, fhb7, fhb0),
    }
    previous, description = run_match16.MATCHES, run_match16.__doc__
    original_digest, original_run = run_match16.ENGINE_SHA256, run_match16.run

    def run_with_engine_pin(args):
        if args.match != "E64tr":
            receipt = here / "pca.sha256"
            fields = receipt.read_text(encoding="utf-8").split()
            if not fields or not re.fullmatch(r"[a-f0-9]{64}", fields[0]):
                raise SystemExit(f"{receipt} must start with the validated PCA SHA-256")
            run_match16.ENGINE_SHA256 = fields[0]
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
