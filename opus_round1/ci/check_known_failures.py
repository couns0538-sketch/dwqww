#!/usr/bin/env python3
"""Accept a ctest log only if every failure is a known one (4_tests/FORGE_KNOWN_TEST_FAILURES.md):
the only failing test is forge_tests and it prints exactly the 4 known AL1 s198 FAIL lines
(WAC 001 x2, rook underpromotion x2). Also rejects any sanitizer report found in the log or
in an optional sanitizer log directory.
usage: check_known_failures.py <ctest.log> [sanitizer_log_dir]"""
import os
import re
import sys

KNOWN = sorted([
    "FAIL: WAC 001 expected g3g6 got f6h5",
    "FAIL: WAC 001 score 623 below 31997",
    "FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion",
    "FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion",
])
SANITIZER = re.compile(r"(runtime error:|ERROR: AddressSanitizer|ERROR: LeakSanitizer|WARNING: ThreadSanitizer|"
                       r"ThreadSanitizer: reported|SUMMARY: (Address|Undefined|Thread)Sanitizer)")

log = open(sys.argv[1], encoding="utf-8", errors="replace").read()
failed = sorted(set(re.findall(r"^\s*\d+ - (\S+) \(", log, re.M)))
fail_lines = sorted(re.findall(r"^FAIL: .*$", log, re.M))
problems = []
if any(name != "forge_tests" for name in failed):
    problems.append("unexpected failing tests: " + ", ".join(n for n in failed if n != "forge_tests"))
if fail_lines != KNOWN:
    problems.append("forge_tests FAIL lines differ from the known set:\n  got:  " + "\n        ".join(fail_lines)
                    + "\n  want: " + "\n        ".join(KNOWN))
if not re.search(r"tests passed", log):
    problems.append("no ctest summary line found")
if SANITIZER.search(log):
    problems.append("sanitizer report inside the ctest log")
if len(sys.argv) > 2 and os.path.isdir(sys.argv[2]):
    for name in sorted(os.listdir(sys.argv[2])):
        path = os.path.join(sys.argv[2], name)
        if os.path.getsize(path) > 0:
            problems.append(f"sanitizer report file {name}:\n" + open(path, errors="replace").read()[:4000])
summary = re.search(r"^.*tests passed.*$", log, re.M)
print("ctest:", summary.group(0) if summary else "?")
print("failing tests:", failed or "none")
if problems:
    print("KNOWN-FAILURE CHECK: FAIL")
    for p in problems:
        print(" -", p)
    sys.exit(1)
print("KNOWN-FAILURE CHECK: PASS (only the 4 known forge_tests lines; no sanitizer report)")
