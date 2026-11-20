#!/usr/bin/env python3
"""Four honesty lines, no setoption. Usage: run_honesty.py EXE TAG OUTFILE"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXE = sys.argv[1]
TAG = sys.argv[2]
OUT = Path(sys.argv[3])
LINES = [
    (f"honesty_{TAG}_bench11", ["bench", "11"]),
    (f"honesty_{TAG}_bench13", ["bench", "13"]),
    (f"honesty_{TAG}_bench16", ["bench", "16"]),
    (f"honesty_{TAG}_perft5", ["go", "perft", "5"]),
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
    OUT.write_text("".join(chunks), encoding="utf-8")
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
