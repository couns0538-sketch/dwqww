"""Validate the slot-bias correction independently.

The correction geomean(fwd, rev^-1) cancels a constant multiplicative slot bias
by algebra, so the A/A control CANNOT validate it -- A/A also cancels to 1.0 by
construction. It only measures the bias.

The real check: the same algebra gives fwd / rev^-1 = s^2, so each pair IMPLIES
its own slot bias. If the bias is what we think it is, that implied value must
land on the directly measured A/A value. That is a prediction the correction
does not get to choose.
"""

import json
import math
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

import paths

PAIRS = [
    ("v2", "abba-native-v2.json", "abba-rev-v2.json"),
    ("v3", "abba-native-v3.json", "abba-rev-v3.json"),
    ("v3+pext", "abba-v3pext.json", "abba-rev-v3pext.json"),
]


def ratios(name, invert=False):
    """Read one ABBA arm from the work dir, validated.

    A missing arm is reported as a missing arm. An earlier version of this script
    read its inputs by bare path, and a wrong path would have surfaced as a
    KeyError deep inside the median rather than as "that arm was never produced".
    """
    path = paths.in_path(name)
    if not os.path.isfile(path):
        raise paths.InputError(
            f"ABBA arm {name!r} not found in the work dir -- run scripts/abba.py for it first")
    with open(path, encoding="utf-8") as f:
        rows = json.load(f)["rows"]
    if not rows:
        raise paths.InputError(f"ABBA arm {name!r} has no rows")
    r = [row["B_med"] / row["A_med"] for row in rows]
    return [1.0 / x for x in r] if invert else r


def main():
    try:
        aa = ratios("abba-AA.json")
    except paths.InputError as exc:
        print(f"validate.py: {exc}", file=sys.stderr)
        return 2

    s_measured = statistics.median(aa)
    print(f"directly measured slot bias (A/A): s = {s_measured:.4f}")
    print(f"  -> the B slot is {(1-s_measured)*100:.2f}% faster than the A slot, regardless of binary")
    print()
    print("implied s = sqrt(fwd / rev^-1) from each experimental pair:")
    print("  (a prediction the correction cannot tune -- it is fixed by the four raw medians)")

    for label, fwd_name, rev_name in PAIRS:
        try:
            f = statistics.median(ratios(fwd_name))
            r = statistics.median(ratios(rev_name, invert=True))
        except paths.InputError as exc:
            print(f"  {label}: SKIPPED -- {exc}")
            continue
        implied = math.sqrt(f / r)
        print(f"  {label}: fwd {f:.4f}  rev^-1 {r:.4f}  -> implied s = {implied:.4f}   "
              f"agreement with A/A: {abs(implied-s_measured)/s_measured*100:.2f}%")

    print()
    print("If those agree, the slot bias is a constant multiplicative factor and the")
    print("correction is exact rather than fitted. If they did not, the correction")
    print("would be an assumption and the ratio would have to be reported uncorrected")
    print("with the bias stated beside it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
