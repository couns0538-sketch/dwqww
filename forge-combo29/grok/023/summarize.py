#!/usr/bin/env python3
"""Print the numbers the report quotes. Reads only files next to this script."""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent


def nodes_in(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    benches = re.findall(r"bench depth (\d+) nodes (\d+)", text)
    perfts = re.findall(r"(?m)^nodes (\d+)\s*$", text)
    return [f"bench {d} nodes {n}" for d, n in benches] + [f"perft nodes {n}" for n in perfts]


def main() -> int:
    print("== honesty B ==")
    for line in nodes_in(HERE / "HONESTY_B.txt"):
        print(line)
    print("== honesty P ==")
    for line in nodes_in(HERE / "HONESTY_P.txt"):
        print(line)
    print("== compare ==")
    print((HERE / "proof_compare.txt").read_text(encoding="utf-8"), end="")
    meta = (HERE / "asan_G100_d10.meta").read_text(encoding="utf-8")
    print("== asan meta tail ==")
    for line in meta.splitlines():
        if line.startswith("asan_") or line.startswith("sanitizer_") or line.startswith("switch=") or line.startswith("count="):
            print(line)
    scratch = (HERE / "asan_scratch.txt").read_text(encoding="utf-8", errors="replace")
    hits = [line for line in scratch.splitlines() if "AddressSanitizer" in line or "heap-buffer-overflow" in line]
    print("== scratch sanitizer lines ==")
    for line in hits[:6]:
        print(line)
    match = HERE / "match_OG.txt"
    if match.exists():
        text = match.read_text(encoding="utf-8", errors="replace")
        print("== match tail ==")
        print("\n".join(text.splitlines()[-25:]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
