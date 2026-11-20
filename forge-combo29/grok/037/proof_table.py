#!/usr/bin/env python3
"""Print the report table from the raw files in this folder. Nothing is typed."""
from pathlib import Path


def lines(name: str):
    return Path(name).read_text().splitlines()


def main() -> None:
    here = Path(__file__).resolve().parent
    print("file\tcontent")
    print(f"HONESTY_B.txt\t{' | '.join(lines(here / 'HONESTY_B.txt'))}")
    print(f"HONESTY_P.txt\t{' | '.join(lines(here / 'HONESTY_P.txt'))}")
    for name in ("compare_off_O.txt", "compare_off_G.txt", "compare_on_O.txt", "compare_on_zero_O.txt"):
        body = " ".join(lines(here / name)[:2])
        print(f"{name}\t{body}")
    print(f"uci_options_table.txt\t{' | '.join(lines(here / 'uci_options_table.txt'))}")
    meta = (here / "asan_G100_d10.meta").read_text().splitlines()
    keep = [line for line in meta if line.startswith("nm_asan_count=") or line.startswith("sanitizer_lines=")]
    print(f"asan_G100_d10.meta\t{' | '.join(keep)}")
    scratch = (here / "asan_scratch.meta").read_text().splitlines()
    keep = [line for line in scratch if line.startswith("nm_asan_count=") or "AddressSanitizer" in line or line.startswith("sanitizer_lines=")]
    print(f"asan_scratch.meta\t{' | '.join(keep)}")
    print(f"match_elo.txt\t{' | '.join(lines(here / 'match_elo.txt'))}")
    print(f"apply_check.txt\t{' | '.join(lines(here / 'apply_check.txt'))}")
    b = (here / "B_O_d12.meta").read_text().splitlines()
    print("B_O_d12.meta\t" + " | ".join(line for line in b if line.startswith("sum=") or line.startswith("first3=")))
    g = (here / "B_G_d12.meta").read_text().splitlines()
    print("B_G_d12.meta\t" + " | ".join(line for line in g if line.startswith("sum=") or line.startswith("first3=")))


if __name__ == "__main__":
    main()
