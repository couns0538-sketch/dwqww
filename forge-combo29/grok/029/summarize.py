#!/usr/bin/env python3
"""Print the measured numbers from the raw files in this folder."""

from pathlib import Path

HERE = Path(__file__).resolve().parent


def search_nodes(path: Path) -> list[int]:
    found: list[int] = []
    last = None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("info depth ") and " nodes " in line:
            bits = line.split()
            last = int(bits[bits.index("nodes") + 1])
        elif line.startswith("bestmove "):
            if last is None:
                raise SystemExit(f"bestmove without nodes in {path}")
            found.append(last)
            last = None
    return found


def honesty(label: str) -> None:
    text = (HERE / f"HONESTY_{label}.txt").read_text(encoding="utf-8").strip()
    print(f"honesty {label}")
    print(text)


def compare(name: str, left: Path, right: Path) -> None:
    a = search_nodes(left)
    b = search_nodes(right)
    differ = sum(x != y for x, y in zip(a, b))
    print(
        f"{name} n={len(a)}/{len(b)} equal={a == b} differ={differ} "
        f"sum_left={sum(a)} sum_right={sum(b)} first3_left={a[:3]} first3_right={b[:3]}"
    )


def main() -> None:
    honesty("B")
    honesty("P")
    compare("O off vs B", HERE / "B_O_d12.txt", HERE / "P_off_O_d12.txt")
    compare("G off vs B", HERE / "B_G_d12.txt", HERE / "P_off_G_d12.txt")
    compare("O on vs B", HERE / "B_O_d12.txt", HERE / "P_on_O_d12.txt")
    asan = (HERE / "asan_G100_d10.txt").read_text(encoding="utf-8", errors="replace").splitlines()
    scratch = (HERE / "asan_scratch.txt").read_text(encoding="utf-8", errors="replace").splitlines()
    def hits(lines: list[str]) -> int:
        return sum(
            1
            for line in lines
            if "AddressSanitizer" in line or "UndefinedBehaviorSanitizer" in line or "runtime error:" in line
        )
    print(f"asan_G100 sanitizer_lines={hits(asan)}")
    print(f"asan_scratch sanitizer_lines={hits(scratch)}")
    for line in scratch:
        if "runtime error:" in line or "AddressSanitizer" in line:
            print(line)
            break
    for meta in (HERE / "asan_G100_d10.txt.meta", HERE / "asan_scratch.txt.meta"):
        for line in meta.read_text(encoding="utf-8").splitlines():
            if line.startswith("nm_asan_count:"):
                print(meta.name, line)
    for line in (HERE / "uci_options.txt").read_text(encoding="utf-8").splitlines():
        if "IdeaB10" in line:
            print(line)


if __name__ == "__main__":
    main()
