#!/usr/bin/env python3
"""Count sanitizer lines in the clean run and print the scratch report line."""
import sys

def count(path, needle):
    text = open(path, "r", encoding="utf-8", errors="replace").read()
    return text.count(needle), text

def main():
    clean, scratch = sys.argv[1], sys.argv[2]
    n, _ = count(clean, "runtime error:")
    a, _ = count(clean, "ERROR: AddressSanitizer")
    print(f"clean runtime_error {n}")
    print(f"clean address_sanitizer {a}")
    _, text = count(scratch, "runtime error:")
    print(f"scratch runtime_error {text.count('runtime error:')}")
    print(f"scratch address_sanitizer {text.count('ERROR: AddressSanitizer')}")
    for line in text.splitlines():
        if "runtime error:" in line or "ERROR: AddressSanitizer" in line:
            print("scratch_line " + line)

if __name__ == "__main__":
    main()
