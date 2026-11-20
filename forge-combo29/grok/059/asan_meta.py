#!/usr/bin/env python3
"""Append the AddressSanitizer symbol count to a search_set meta file and count sanitizer lines."""
import subprocess
import sys
from pathlib import Path

NEEDLES = ("AddressSanitizer", "UndefinedBehaviorSanitizer", "runtime error:")


def main() -> int:
    exe = Path(sys.argv[1]).resolve()
    meta = Path(sys.argv[2])
    err = Path(sys.argv[3])
    counted = subprocess.run(["nm", "-C", str(exe)], check=False, capture_output=True, text=True)
    asan = sum(1 for line in counted.stdout.splitlines() if "__asan_" in line)
    text = err.read_text(errors="replace") if err.exists() else ""
    hits = [line for line in text.splitlines() if any(needle in line for needle in NEEDLES)]
    with meta.open("a") as handle:
        handle.write(f"nm_asan_symbols={asan}\n")
        handle.write("nm_command=nm -C <exe> | grep -c __asan_\n")
        handle.write(f"sanitizer_lines={len(hits)}\n")
        for line in hits:
            handle.write(f"sanitizer_line={line}\n")
    print(f"nm_asan_symbols={asan}")
    print(f"sanitizer_lines={len(hits)}")
    for line in hits[:8]:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
