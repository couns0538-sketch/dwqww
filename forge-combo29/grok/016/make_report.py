#!/usr/bin/env python3
"""Print the report tables from the raw files in this folder. Nothing is typed."""
from pathlib import Path

here = Path(__file__).resolve().parent


def tail_result(path: Path) -> str:
    lines = path.read_text().splitlines()
    idxs = [i for i, line in enumerate(lines) if line.startswith("Results of ")]
    if not idxs:
        return path.read_text()
    return "\n".join(lines[idxs[-1]: idxs[-1] + 8])


def show(title: str, path: Path) -> None:
    print(f"## {title}")
    print(f"file {path.name}")
    print(path.read_text().rstrip())
    print()


print("# pasted evidence")
print()
show("honesty B", here / "HONESTY_B.txt")
show("honesty P", here / "HONESTY_P.txt")
show("off O versus B", here / "compare_off_O.txt")
show("off G versus B", here / "compare_off_G.txt")
show("on O versus B", here / "compare_on_O.txt")
show("uci options", here / "uci_options.txt")
# only the IdeaS13 lines, the file is the full uci dump
print("## IdeaS13 lines from uci_options.txt")
for line in (here / "uci_options.txt").read_text().splitlines():
    if "IdeaS13" in line or line.startswith("id name "):
        print(line)
print()
show("asan clean meta", here / "asan_G100.meta")
show("asan scratch meta", here / "asan_scratch.meta")
print("## asan scratch sanitizer lines")
for line in (here / "asan_scratch.txt").read_text().splitlines():
    if "runtime error:" in line or "AddressSanitizer" in line or "SUMMARY:" in line:
        print(line)
print()
show("apply check", here / "apply_check.txt")
print("## match")
print(tail_result(here / "match_s13.txt"))
print()
print("## on O sum from meta")
for line in (here / "P_on_O_d12.meta").read_text().splitlines():
    if line.startswith("sum ") or line.startswith("count "):
        print(line)
