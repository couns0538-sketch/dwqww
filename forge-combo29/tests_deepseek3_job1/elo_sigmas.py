#!/usr/bin/env python3
"""Sigma-from-zero for each job-1 match, so the report's significance numbers
are computed rather than asserted.  Reads fastchess's own final Elo line out of
each match's last40.txt.
"""
import re
import sys
from pathlib import Path

LOGS = Path(__file__).resolve().parent / "logs"

MATCHES = [
    ("M1_NullThreatVerify", "NullThreatVerify"),
    ("M2_NullSeeVeto", "NullSeeVeto"),
    ("M3_AspArmLate", "AspArmLate"),
    ("M3re_AspArmLate", "AspArmLate (repeat, seed 9305)"),
    ("M4_EvalRule50Damp", "EvalRule50Damp"),
    ("M5_DeadMaterial", "DeadMaterial"),
]

LINE = re.compile(r"^Elo:\s*(-?[\d.]+)\s*\+/-\s*([\d.]+)")


def main():
    print(f"{'match':<32} {'Elo':>8} {'err':>7} {'sigma':>6}  95%-ish interval")
    for directory, label in MATCHES:
        path = LOGS / directory / "last40.txt"
        if not path.exists():
            print(f"{label:<32} MISSING {path}")
            continue
        elo = err = None
        for line in path.read_text().splitlines():
            m = LINE.match(line)
            if m:
                elo, err = float(m.group(1)), float(m.group(2))
        if elo is None:
            print(f"{label:<32} no Elo line found")
            continue
        sigma = abs(elo) / err if err else float("inf")
        print(f"{label:<32} {elo:>8.2f} {err:>7.2f} {sigma:>6.2f}  "
              f"{elo - err:+.1f} .. {elo + err:+.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
