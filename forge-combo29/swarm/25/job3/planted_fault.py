#!/usr/bin/env python3
"""planted_fault.py FAKE_ENGINE : the Rule-1 / brief-required planted fault.

The brief demands TWO proofs before a "0 sanitizer lines" counts:
  (1) nm -C <exe> | grep -c __asan_  above 0        -> recorded in sanitizer_symbols.txt (35 asan, 15 ubsan)
  (2) a scratch copy with ONE planted fault behind input we control, run through THE SAME RUNNER,
      which must count the sanitizer line.

This program builds nothing; it only checks that the runner (run_mate_roots.sh) counts a sanitizer line
from a fake engine that deliberately prints one. If the runner reports 0 for the fake, the runner cannot
see sanitizer output and every real "0 lines" result is "not shown".
"""
import subprocess
import sys

RUNNER = sys.argv[1]
FAKE = sys.argv[2]
out = subprocess.run(["bash", RUNNER, FAKE, "/tmp/plant_mate"], capture_output=True, text=True)
print(out.stdout[-2000:])
count = 0
for line in open("/tmp/plant_mate/sanitizer_lines.txt"):
    pass
try:
    val = open("/tmp/plant_mate/sanitizer_count.txt").read().strip()
    count = int(val)
except Exception:
    count = -1
print(f"\nPLANT RESULT: runner counted {count} sanitizer lines on the planted fake")
if count > 0:
    print("PASS: the runner can see a sanitizer line, so a real '0 lines' is a measurement")
    sys.exit(0)
print("FAIL: the runner counted 0 on a planted fault — '0 sanitizer lines' would be 'not shown'")
sys.exit(3)
