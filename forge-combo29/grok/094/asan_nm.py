#!/usr/bin/env python3
"""Print how many nm symbols contain __asan_."""

import subprocess
import sys

completed = subprocess.run(["nm", "-C", sys.argv[1]], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
text = completed.stdout.decode("utf-8", "replace")
count = sum(1 for line in text.splitlines() if "__asan_" in line)
print(count)
sys.exit(0 if count > 0 else 1)
