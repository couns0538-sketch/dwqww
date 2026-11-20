#!/usr/bin/env python3
"""Append the asan symbol count to a search .meta file."""
import subprocess
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: note_asan.py <exe> <meta>")
    exe = Path(sys.argv[1]).resolve()
    meta = Path(sys.argv[2])
    count = subprocess.run(
        ["nm", "-C", str(exe)],
        text=True,
        capture_output=True,
        check=True,
    )
    n = sum(1 for line in count.stdout.splitlines() if "__asan_" in line)
    with meta.open("a") as handle:
        handle.write(f"nm_asan_count {n}\n")
        handle.write("nm command: nm -C <exe> | grep -c __asan_\n")
    print(f"nm_asan_count {n}")
    if n <= 0:
        raise SystemExit("asan symbols missing")


if __name__ == "__main__":
    main()
