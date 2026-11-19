#!/usr/bin/env python3
"""Generate and verify the Job 39 seeded tuning draws."""

import argparse
from pathlib import Path
import random


# The handoff table in order: name, start, minimum, maximum, step.
SETTINGS = (
    ("DrawJitter", 0, 0, 8, 1),
    ("LmrQuietBase", 93, 0, 300, 8),
    ("LmrQuietDivisor", 205, 100, 500, 12),
    ("LmrNoisyBase", 13, 0, 300, 6),
    ("LmrNoisyDivisor", 333, 100, 800, 20),
    ("NullMoveMinDepth", 3, 1, 10, 1),
    ("NullMoveBase", 5, 1, 6, 1),
    ("NullMoveDepthDivisor", 3, 1, 10, 1),
    ("NullMoveEvalDivisor", 200, 50, 1000, 20),
    ("RfpDepth", 8, 0, 15, 1),
    ("RfpMargin", 72, 10, 300, 6),
    ("RfpImproving", 40, 0, 200, 6),
    ("RazorDepth", 2, 0, 6, 1),
    ("RazorBase", 150, 0, 1000, 20),
    ("RazorMultiplier", 350, 0, 1000, 25),
    ("FutilityDepth", 7, 0, 15, 1),
    ("FutilityBase", 100, 0, 500, 12),
    ("FutilityMultiplier", 110, 0, 500, 10),
    ("LmpBase", 8, 0, 20, 1),
    ("HistoryPruneDepth", 3, 0, 10, 1),
    ("HistoryPruneMultiplier", 2220, 0, 20000, 200),
    ("SeeQuietMultiplier", 24, 0, 200, 3),
    ("SeeNoisyMultiplier", 150, 0, 1000, 12),
    ("SingularDepth", 6, 2, 20, 1),
    ("SingularMargin", 2, 0, 10, 1),
    ("IirDepth", 2, 1, 20, 1),
    ("ProbcutDepth", 5, 1, 20, 1),
    ("ProbcutMargin", 180, 0, 1000, 15),
    ("QsFutilityMargin", 160, 0, 1000, 14),
    ("AspirationDelta", 18, 4, 200, 2),
    ("HistoryBonusQuadratic", 24, 0, 100, 3),
    ("HistoryBonusLinear", 54, 0, 500, 6),
    ("HistoryBonusMax", 2212, 100, 10000, 180),
    ("LmrHistoryDivisor", 5643, 1000, 30000, 500),
    ("CheckExtensionDepth", 2, 1, 30, 1),
    ("LmrCutoffThreshold", 3, 0, 20, 1),
    ("MaterialCorrectionWeight", 100, 0, 300, 10),
    ("CaptureFutilityBase", 0, 0, 1000, 20),
    ("FailLowContinuationBonus", 0, 0, 300, 15),
    ("EvalSwingMult", 0, 0, 64, 3),
)
NAMES = tuple(option[0] for option in SETTINGS)

KNOWN = {
    1: (
        4, 141, 181, 0, 293, 9, 6, 1, 180, 12, 42, 76, 0, 230, 225, 12, 148, 140, 5, 2, 1620,
        30, 138, 9, 2, 1, 8, 225, 244, 26, 42, 18, 1672, 4143, 1, 0, 90, 100, 0, 0,
    ),
    100: (
        0, 53, 229, 19, 253, 6, 1, 1, 100, 11, 102, 16, 0, 50, 325, 12, 112, 140, 11, 6, 3220,
        42, 150, 10, 6, 6, 5, 90, 118, 6, 30, 90, 2392, 2643, 2, 9, 160, 0, 0, 3,
    ),
}


def draw_values(number):
    rng = random.Random(390000 + number)
    return tuple(
        min(max(start + rng.randint(-6, 6) * step, low), high)
        for _, start, low, high, step in SETTINGS
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, metavar="draws.tsv")
    args = parser.parse_args()

    if len(NAMES) != 40 or len(set(NAMES)) != 40:
        raise SystemExit("expected 40 distinct tuning names")
    draws = {number: draw_values(number) for number in range(1, 101)}
    for number, expected in KNOWN.items():
        if draws[number] != expected:
            raise SystemExit(f"draw {number} differs from the handoff\nexpected {expected}\nobserved {draws[number]}")
    contents = "".join("\t".join(map(str, (number, *values))) + "\n" for number, values in draws.items())
    args.output.write_bytes(contents.encode("ascii"))
    for number in KNOWN:
        print(f"draw {number} PASS\t" + "\t".join(map(str, draws[number])))


if __name__ == "__main__":
    main()
