#!/usr/bin/env python3
"""Compare per-position nodes from two depth_run.py raw files."""
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("depth_sum", HERE / "depth_sum.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def rows(path: str) -> list[int]:
    text = open(path, encoding="utf-8").read().splitlines()
    out = []
    current = None
    last = None
    for line in text:
        if line.startswith("### position "):
            current = int(line.split()[2])
            last = None
            continue
        if line.startswith(">>> go "):
            last = None
            continue
        if line.startswith("<<< ") and current is not None:
            body = line[4:]
            found = mod.nodes_re.findall(body)
            if found and not body.startswith("bestmove"):
                last = int(found[-1])
            if body.startswith("bestmove ") and last is not None:
                out.append(last)
                current = None
                last = None
    return out


def main() -> None:
    a = rows(sys.argv[1])
    b = rows(sys.argv[2])
    n = min(len(a), len(b))
    differ = [i + 1 for i in range(n) if a[i] != b[i]]
    print(f"left {sys.argv[1]}")
    print(f"right {sys.argv[2]}")
    print(f"left_positions {len(a)}")
    print(f"right_positions {len(b)}")
    print(f"compared {n}")
    print(f"equal {n - len(differ)}")
    print(f"differ {len(differ)}")
    if differ[:20]:
        print("first_differ " + " ".join(str(i) for i in differ[:20]))
        for i in differ[:5]:
            print(f"pos {i} left {a[i - 1]} right {b[i - 1]}")


if __name__ == "__main__":
    main()
