#!/usr/bin/env python3
"""Meta for the planted heap-overrun engine, from the exe and its raw log."""
import hashlib
import subprocess
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: bug_meta.py <exe> <raw> <meta>")
    exe = Path(sys.argv[1]).resolve()
    raw = Path(sys.argv[2])
    meta = Path(sys.argv[3])
    digest = hashlib.sha256(exe.read_bytes()).hexdigest()
    symbols = subprocess.run(["nm", "-C", str(exe)], text=True, capture_output=True, check=True)
    count = sum(1 for line in symbols.stdout.splitlines() if "__asan_" in line)
    text = raw.read_text(errors="replace")
    hits = [line for line in text.splitlines() if "runtime error:" in line or "AddressSanitizer" in line]
    meta.write_text(
        "\n".join(
            [
                f"exe {exe}",
                f"sha256 {digest}",
                "runner search_set.py",
                "fen 8/8/8/3k4/8/8/3K4/8 w - - 0 1",
                f"nm_asan_count {count}",
                f"sanitizer_lines {len(hits)}",
                "planted read past the end of a 4-int heap array in apply_position",
            ]
        )
        + "\n"
    )
    print(meta.read_text())


if __name__ == "__main__":
    main()
