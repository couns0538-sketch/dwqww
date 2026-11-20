#!/usr/bin/env python3
"""Compare node rows parsed from measure.py transcripts."""
import sys
from pathlib import Path


def nodes_of(path: Path) -> list[int]:
    nodes = []
    pending = []
    in_go = False
    for line in path.read_text().splitlines():
        if line.startswith(">>> go "):
            in_go = True
            pending = []
            continue
        if not in_go:
            continue
        if line.startswith(">>>"):
            in_go = False
            pending = []
            continue
        pending.append(line)
        if line.startswith("bestmove "):
            found = None
            for item in pending:
                if " nodes " not in item:
                    continue
                fields = item.split()
                if "nodes" in fields:
                    found = int(fields[fields.index("nodes") + 1])
            if found is None:
                raise SystemExit(f"{path}: bestmove without nodes")
            nodes.append(found)
            in_go = False
            pending = []
    return nodes


def main() -> None:
    left = nodes_of(Path(sys.argv[1]))
    right = nodes_of(Path(sys.argv[2]))
    if len(left) != len(right):
        raise SystemExit(f"length {len(left)} vs {len(right)}")
    differ = [i + 1 for i, (a, b) in enumerate(zip(left, right)) if a != b]
    print(
        f"{Path(sys.argv[1]).name} vs {Path(sys.argv[2]).name} "
        f"positions {len(left)} differ {len(differ)} of {len(left)} "
        f"sum {sum(left)} vs {sum(right)}"
    )
    if differ[:12]:
        print("first_differ", " ".join(str(i) for i in differ[:12]))


if __name__ == "__main__":
    main()
