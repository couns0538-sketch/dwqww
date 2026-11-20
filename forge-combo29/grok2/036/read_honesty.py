#!/usr/bin/env python3
"""Read honesty raw files and print the node on each bench / perft line."""
import pathlib
import re
import sys

expected = {
    "bench11": 312866,
    "bench13": 862329,
    "bench16": 3024920,
    "perft5": 4865609,
}


def nodes_of(path: pathlib.Path, kind: str) -> int:
    text = path.read_text(encoding="utf-8", errors="replace")
    if kind == "perft5":
        found = re.findall(r"^nodes (\d+)\s*$", text, flags=re.M)
    else:
        found = re.findall(r"bench depth \d+ nodes (\d+)", text)
    if len(found) != 1:
        sys.exit(f"STOP: {path} has {len(found)} node lines")
    return int(found[0])


def main() -> None:
    out = pathlib.Path(sys.argv[1])
    tag = sys.argv[2]
    print(f"tag {tag}")
    ok = True
    for kind, want in expected.items():
        got = nodes_of(out / f"{tag}_{kind}.txt", kind)
        flag = "ok" if got == want else "MISS"
        if flag != "ok":
            ok = False
        print(f"{kind} nodes {got} expected {want} {flag}")
    print("honesty", "ok" if ok else "MISS")


if __name__ == "__main__":
    main()
