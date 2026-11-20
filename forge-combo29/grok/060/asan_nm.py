#!/usr/bin/env python3
"""Append the AddressSanitizer symbol count to a .meta file.

The count is nm -C EXE | grep -c __asan_
"""
import subprocess
import sys

def main():
    exe = sys.argv[1]
    meta = sys.argv[2]
    out = subprocess.check_output(["nm", "-C", exe], text=True, errors="replace")
    count = sum(1 for line in out.splitlines() if "__asan_" in line)
    line = "nm -C " + exe + " | grep -c __asan_ " + str(count)
    with open(meta, "a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    print(line)

if __name__ == "__main__":
    main()
