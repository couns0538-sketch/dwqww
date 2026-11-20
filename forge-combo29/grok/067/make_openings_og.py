#!/usr/bin/env python3
"""Concatenate the O and G position lists into one EPD file."""
import sys
from pathlib import Path

def main() -> None:
    out = Path(sys.argv[1])
    lines = []
    for path in sys.argv[2:]:
        for line in Path(path).read_text().splitlines():
            text = line.split(";")[0].strip()
            if text:
                lines.append(text)
    out.write_text("\n".join(lines) + "\n")
    print(f"WROTE {out} N {len(lines)}")

if __name__ == "__main__":
    main()
