#!/usr/bin/env python3
"""Read the raw honesty outputs and write HONESTY_B.txt. Numbers come only from those files."""
import pathlib
import sys

EXPECT = {
    "honesty_b_bench11.txt": 312866,
    "honesty_b_bench13.txt": 862329,
    "honesty_b_bench16.txt": 3024920,
    "honesty_b_perft5.txt": 4865609,
}


def nodes_of(text: str) -> int | None:
    found = None
    for line in text.splitlines():
        parts = line.replace(",", " ").split()
        if "nodes" in parts:
            i = parts.index("nodes")
            if i + 1 < len(parts) and parts[i + 1].isdigit():
                found = int(parts[i + 1])
    return found


def main() -> int:
    folder = pathlib.Path(__file__).resolve().parent
    lines = []
    ok = True
    for name, want in EXPECT.items():
        text = (folder / name).read_text()
        got = nodes_of(text)
        flag = "ok" if got == want else "MISMATCH"
        if got != want:
            ok = False
        lines.append(f"{name} nodes {got} expected {want} {flag}")
    lines.append("all_match yes" if ok else "all_match no")
    out = folder / "HONESTY_B.txt"
    out.write_text("\n".join(lines) + "\n")
    sys.stdout.write(out.read_text())
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
