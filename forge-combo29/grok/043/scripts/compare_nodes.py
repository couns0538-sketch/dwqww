#!/usr/bin/env python3
"""Compare two search_set transcripts position by position. Prints counts only."""
import subprocess, sys
from pathlib import Path

def rows(path: Path) -> list[int]:
    script = Path(__file__).with_name("summarize_nodes.py")
    text = subprocess.check_output([sys.executable, str(script), str(path)], text=True)
    out = []
    for line in text.splitlines():
        if "\t" not in line:
            continue
        out.append(int(line.split("\t", 1)[1]))
    return out

def main() -> int:
    a = rows(Path(sys.argv[1]))
    b = rows(Path(sys.argv[2]))
    n = min(len(a), len(b))
    differ = sum(x != y for x, y in zip(a, b))
    print("left", sys.argv[1])
    print("right", sys.argv[2])
    print("left_n", len(a), "left_sum", sum(a))
    print("right_n", len(b), "right_sum", sum(b))
    print("compared", n, "differ", differ)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
