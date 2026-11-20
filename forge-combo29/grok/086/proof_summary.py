#!/usr/bin/env python3
"""Print the proof numbers by reading the raw result files. No hand-typed counts."""
from pathlib import Path

HERE = Path(__file__).resolve().parent


def nodes_of(text: str) -> int | None:
    found = None
    for line in text.splitlines():
        parts = line.split()
        if "nodes" in parts:
            found = int(parts[parts.index("nodes") + 1])
    return found


def load_rows(path: Path) -> list[int]:
    return [int(line) for line in path.read_text().splitlines() if line.strip()]


def differ(a: list[int], b: list[int]) -> int:
    if len(a) != len(b):
        raise SystemExit(f"length {len(a)} vs {len(b)}")
    return sum(x != y for x, y in zip(a, b))


def main() -> int:
    print("honesty_P")
    for name, expect in (
        ("HONESTY_P_bench11.txt", 312866),
        ("HONESTY_P_bench13.txt", 862329),
        ("HONESTY_P_bench16.txt", 3024920),
        ("HONESTY_P_perft5.txt", 4865609),
    ):
        got = nodes_of((HERE / name).read_text())
        print(f"  {name} {got} expected {expect} {'OK' if got == expect else 'FAIL'}")

    b_o = load_rows(HERE / "B_O_d12.nodes")
    b_g = load_rows(HERE / "B_G_d12.nodes")
    off_o = load_rows(HERE / "P_off_O_d12.nodes")
    off_g = load_rows(HERE / "P_off_G_d12.nodes")
    on_o = load_rows(HERE / "P_on_O_d12.nodes")
    print(f"off_O differ {differ(b_o, off_o)} of {len(b_o)} sum {sum(off_o)}")
    print(f"off_G differ {differ(b_g, off_g)} of {len(b_g)} sum {sum(off_g)}")
    print(f"on_O differ {differ(b_o, on_o)} of {len(b_o)} sum {sum(on_o)}")
    print(f"on_O first3 {' '.join(str(n) for n in on_o[:3])}")

    uci = (HERE / "P_uci.txt").read_text().splitlines()
    for line in uci:
        if "IdeaA5" in line:
            print("uci", line)

    print("apply_check")
    print((HERE / "apply_check.txt").read_text().rstrip())
    print("asan_nm", (HERE / "asan_nm_count.txt").read_text().strip())
    raw = (HERE / "asan_G100_d10.raw").read_text()
    print("asan_bestmoves", raw.count("bestmove "))
    print("asan_error_lines", sum(1 for line in raw.splitlines() if "ERROR: AddressSanitizer" in line))
    scratch = (HERE / "asan_scratch.raw").read_text(errors="replace")
    print("scratch_heap", sum(1 for line in scratch.splitlines() if "ERROR: AddressSanitizer: heap-buffer-overflow" in line))
    print("scratch_nm", (HERE / "asan_scratch_nm_count.txt").read_text().strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
