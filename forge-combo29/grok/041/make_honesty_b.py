#!/usr/bin/env python3
"""Build HONESTY_B.txt from the raw honesty transcripts. Nothing is typed."""
import pathlib
import sys

def main() -> None:
    raw = pathlib.Path(sys.argv[1])
    out = pathlib.Path(sys.argv[2])
    lines = []
    for name in ("bench11", "bench13", "bench16", "perft5"):
        text = (raw / f"honesty_{name}.txt").read_text()
        picked = [
            line
            for line in text.splitlines()
            if line.startswith("info string bench") or line.startswith("nodes ")
        ]
        lines.append(f"# {name}")
        lines.extend(picked if picked else ["MISSING"])
    out.write_text("\n".join(lines) + "\n")
    print(out.read_text(), end="")

if __name__ == "__main__":
    main()
