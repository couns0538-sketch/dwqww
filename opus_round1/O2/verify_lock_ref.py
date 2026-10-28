#!/usr/bin/env python3
"""Check that the lock_ref sections of tests/nnue_parity_tests.cpp are verbatim copies of the
AL1 s198 lock (git 294dbed) src/nnue.cpp. Each section is delimited by
  // ---- BEGIN verbatim AL1 s198 src/nnue.cpp lines A-B ----
  // ---- END verbatim ----
usage: verify_lock_ref.py [repo_dir]   (exit 0 = every section identical)"""
import re
import subprocess
import sys

repo = sys.argv[1] if len(sys.argv) > 1 else "."
lock = subprocess.run(["git", "-C", repo, "show", "294dbed:src/nnue.cpp"], capture_output=True, text=True,
                      check=True).stdout.split("\n")
test = open(f"{repo}/tests/nnue_parity_tests.cpp", encoding="utf-8").read().split("\n")
sections = 0
i = 0
while i < len(test):
    m = re.match(r"// ---- BEGIN verbatim AL1 s198 src/nnue\.cpp lines (\d+)-(\d+) ----$", test[i])
    if not m:
        i += 1
        continue
    a, b = int(m.group(1)), int(m.group(2))
    end = test.index("// ---- END verbatim ----", i)
    body = test[i + 1:end]
    if body != lock[a - 1:b]:
        raise SystemExit(f"FAIL: section lines {a}-{b} differs from 294dbed:src/nnue.cpp")
    print(f"section lines {a}-{b}: {len(body)} lines identical")
    sections += 1
    i = end + 1
if sections == 0:
    raise SystemExit("FAIL: no verbatim sections found")
print(f"PASS: {sections} sections identical to the lock")
