#!/usr/bin/env python3
"""Print the numbers the report quotes. Reads only files in this folder."""
from pathlib import Path


def show(path: Path) -> None:
    print(f"----- {path.name} -----")
    text = path.read_text(encoding="utf-8", errors="replace").rstrip()
    print(text if text else "(empty)")


def main() -> int:
    folder = Path(__file__).resolve().parent
    names = [
        "HONESTY_B.txt",
        "HONESTY_P.txt",
        "sum_B_O.txt",
        "sum_B_G.txt",
        "sum_P_off_O.txt",
        "sum_P_off_G.txt",
        "sum_P_on_O.txt",
        "compare_off_O.txt",
        "compare_off_G.txt",
        "compare_on_O.txt",
        "asan_g100.meta",
        "asan_g100.sanitizer.txt",
        "asan_nm_count.txt",
        "asan_scratch.sanitizer.txt",
        "asan_scratch_nm_count.txt",
        "match_s28.parsed.txt",
        "prediction.txt",
        "stamps.txt",
    ]
    for name in names:
        show(folder / name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
