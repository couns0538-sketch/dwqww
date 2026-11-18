#!/usr/bin/env python3
"""Run one of the seven Job 23 matches with the pinned dual-preflight harness."""

from pathlib import Path
import re
import sys

PCA_SHA256 = "49b56941b2acc0c2b9272c4e14992f2561c9ef71dbaf3da74a8a684ae8bc416a"
PCA_MATCHES = ("F5kr",)


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
    zero, dose64, dose128 = swing(0, 200), swing(64, 200), swing(128, 200)
    fhb0 = (*swing(0), ("FailHighBlend", "0"))
    fhb5 = (*swing(0), ("FailHighBlend", "5"))
    matches = {
        # games, seed, workers, nodes A, nodes B, extra options A and B
        "K12": (100, 7231, 4, 2000, 2000, dose128, dose128),
        "C12": (200, 7232, 4, 10000, 20000, zero, zero),
        "F5kr": (2000, 7233, 2, 2000, 2000, fhb5, fhb0),
        "M128k": (2000, 7234, 2, 2000, 2000, dose128, dose64),
        "X400k": (2000, 7235, 2, 2000, 2000, swing(64, 400), dose64),
        "M96k": (2000, 7236, 2, 2000, 2000, swing(96, 200), dose64),
        "M128w": (1600, 7237, 2, 20000, 20000, dose128, dose64),
    }
    previous, description = run_match16.MATCHES, run_match16.__doc__
    original_digest, original_run = run_match16.ENGINE_SHA256, run_match16.run

    def run_with_engine_pin(args):
        if args.match in PCA_MATCHES:
            expected_digest = PCA_SHA256
        else:
            receipt = here / "w.sha256"
            fields = receipt.read_text(encoding="utf-8").split()
            if not fields or not re.fullmatch(r"[a-f0-9]{64}", fields[0]):
                raise SystemExit(f"{receipt} must start with the validated W SHA-256")
            expected_digest = fields[0]
        run_match16.ENGINE_SHA256 = expected_digest
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
