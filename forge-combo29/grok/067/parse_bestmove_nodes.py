#!/usr/bin/env python3
"""Node count of the last info depth line before each bestmove."""
import sys
from pathlib import Path

def main() -> None:
    last = None
    rows = []
    for line in Path(sys.argv[1]).read_text(errors="replace").splitlines():
        if line.startswith("info depth ") and " nodes " in line:
            last = int(line.split(" nodes ", 1)[1].split()[0])
        elif line.startswith("bestmove "):
            if last is None:
                raise SystemExit(f"bestmove without nodes at position {len(rows)}")
            rows.append(last)
            last = None
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    text = "\n".join(f"{index}\t{value}\t" for index, value in enumerate(rows)) + "\n"
    if out:
        out.write_text(text)
    print(f"count {len(rows)} sum {sum(rows)}")

if __name__ == "__main__":
    main()
