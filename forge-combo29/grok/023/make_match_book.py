#!/usr/bin/env python3
"""Concatenate O and G into one EPD of 6-field FENs, in that order."""
import sys
from pathlib import Path


def fens(path: Path) -> list[str]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 6:
            raise SystemExit(f"short fen: {line}")
        rows.append(" ".join(parts[:6]))
    return rows


def main() -> int:
    o_path, g_path, out_path = sys.argv[1:]
    rows = fens(Path(o_path)) + fens(Path(g_path))
    Path(out_path).write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"positions={len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
