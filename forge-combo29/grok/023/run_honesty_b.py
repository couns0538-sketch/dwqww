#!/usr/bin/env python3
"""Run the four honesty lines on exe B and paste the raw files into HONESTY_B.txt."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXE = sys.argv[1]
LINES = [
    ("honesty_b_bench11", ["bench", "11"]),
    ("honesty_b_bench13", ["bench", "13"]),
    ("honesty_b_bench16", ["bench", "16"]),
    ("honesty_b_perft5", ["go", "perft", "5"]),
]


def main() -> int:
    chunks = []
    for name, cmd in LINES:
        prefix = str(HERE / name)
        result = subprocess.run(
            [sys.executable, str(HERE / "harness_honesty.py"), EXE, prefix, *cmd],
            check=False,
        )
        if result.returncode != 0:
            return result.returncode
        raw = Path(prefix + ".txt").read_text(encoding="utf-8")
        chunks.append(f"===== {name} {' '.join(cmd)} =====\n{raw}")
    (HERE / "HONESTY_B.txt").write_text("".join(chunks), encoding="utf-8")
    print("wrote", HERE / "HONESTY_B.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
