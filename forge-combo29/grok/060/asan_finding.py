#!/usr/bin/env python3
"""Print sanitizer lines from a raw engine log. Usage: asan_finding.py RAW"""
import sys

def main():
    path = sys.argv[1]
    hits = []
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if "Sanitizer" in line or "sanitizer" in line:
                hits.append(line.rstrip("\n"))
    print("sanitizer_lines", len(hits))
    for line in hits[:8]:
        print(line)

if __name__ == "__main__":
    main()
