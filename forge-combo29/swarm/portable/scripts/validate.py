"""Validate the slot-bias correction independently, then run the identity sweep.

The correction geomean(fwd, rev^-1) cancels a constant multiplicative slot bias
by algebra, so the A/A control CANNOT validate it -- A/A also cancels to 1.0 by
construction. It only measures the bias.

The real check: the same algebra gives fwd / rev^-1 = s^2, so each pair IMPLIES
its own slot bias. If the bias is what we think it is, that implied value must
land on the directly measured A/A value. That is a prediction the correction
does not get to choose.
"""

import json
import statistics
import math


def ratios(path, invert=False):
    rows = json.load(open(path))["rows"]
    r = [row["B_med"] / row["A_med"] for row in rows]
    return [1.0 / x for x in r] if invert else r


aa = ratios("/tmp/build/abba-AA.json")
s_measured = statistics.median(aa)
print(f"directly measured slot bias (A/A): s = {s_measured:.4f}")
print(f"  -> the B slot is {(1-s_measured)*100:.2f}% faster than the A slot, regardless of binary")
print()
print("implied s = sqrt(fwd / rev^-1) from each experimental pair:")
print("  (a prediction the correction cannot tune -- it is fixed by the four raw medians)")
for label, fwd, rev in [
    ("v2", "/tmp/build/abba-native-v2.json", "/tmp/build/abba-rev-v2.json"),
    ("v3", "/tmp/build/abba-native-v3.json", "/tmp/build/abba-rev-v3.json"),
]:
    f = statistics.median(ratios(fwd))
    r = statistics.median(ratios(rev, invert=True))
    implied = math.sqrt(f / r)
    print(f"  {label}: fwd {f:.4f}  rev^-1 {r:.4f}  -> implied s = {implied:.4f}   "
          f"agreement with A/A: {abs(implied-s_measured)/s_measured*100:.2f}%")

print()
print("If those agree, the slot bias is a constant multiplicative factor and the")
print("correction below is exact rather than fitted. If they did not, the correction")
print("would be an assumption and the ratio would have to be reported uncorrected")
print("with the bias stated beside it.")
