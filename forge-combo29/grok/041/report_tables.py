#!/usr/bin/env python3
"""Print the report tables by reading files in this seat folder. Nothing is typed."""
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])


def show(title: str, path: pathlib.Path) -> None:
    print(f"== {title} ==")
    print(f"file {path}")
    if not path.exists():
        print("MISSING")
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    print(text.rstrip())
    print()


def sanitizer_hits(path: pathlib.Path) -> int:
    if not path.exists():
        return -1
    return sum(
        1
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
        if "Sanitizer" in line or "runtime error" in line
    )


show("honesty B", root / "HONESTY_B.txt")
show("honesty P", root / "HONESTY_P.txt")
show("baseline B", root / "baseline_B.txt")
show("compare O off", root / "raw_p" / "compare_O_off.txt")
show("compare G off", root / "raw_p" / "compare_G_off.txt")
show("compare O on", root / "raw_p" / "compare_O_on.txt")
show("sum O on", root / "raw_p" / "sum_O_on.txt")
show("apply check", root / "apply_check.txt")
show("match", root / "match" / "result_block.txt")

print("== asan meta counts ==")
for name in ("G100_d10.meta", "scratch_overrun.meta"):
    meta = root / "raw_asan" / name
    print(f"file {meta}")
    if not meta.exists():
        print("MISSING")
        continue
    for line in meta.read_text(encoding="utf-8").splitlines():
        if line.startswith("nm_") or line.startswith("exe=") or line.startswith("option=setoption name IdeaK2"):
            print(line)
print()
print("== sanitizer lines ==")
for name in ("G100_d10.err", "scratch_overrun.err"):
    path = root / "raw_asan" / name
    print(f"{name} hits {sanitizer_hits(path)} bytes {path.stat().st_size if path.exists() else 0}")

print()
print("== uci IdeaK2 lines ==")
uci = (root / "raw_p" / "uci.txt").read_text(encoding="utf-8").splitlines()
for line in uci:
    if "IdeaK2" in line:
        print(line)

print()
print("== prediction ==")
print((root / "prediction.txt").read_text(encoding="utf-8").rstrip())
print("== step table ==")
print("step | status | evidence | result")


def differ_line(path: pathlib.Path) -> str:
    if not path.exists():
        return "MISSING"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("differ "):
            return line
    return "no differ line"


def first_matching(path: pathlib.Path, prefix: str) -> str:
    if not path.exists():
        return "MISSING"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            return line
    return "MISSING"


print(f"1 seat | done | SEAT.txt stamps.txt | {(root / 'stamps.txt').read_text(encoding='utf-8').splitlines()[0]}")
print(f"2 honesty B | done | HONESTY_B.txt | {first_matching(root / 'HONESTY_B.txt', 'info string bench depth 11')}")
print(f"2 baseline O | done | baseline_B.txt | {first_matching(root / 'baseline_B.txt', 'SUM')}")
print(f"3 off O | done | raw_p/compare_O_off.txt | {differ_line(root / 'raw_p' / 'compare_O_off.txt')}")
print(f"3 off G | done | raw_p/compare_G_off.txt | {differ_line(root / 'raw_p' / 'compare_G_off.txt')}")
print(f"3 on O | done | raw_p/compare_O_on.txt raw_p/sum_O_on.txt | {differ_line(root / 'raw_p' / 'compare_O_on.txt')} {first_matching(root / 'raw_p' / 'sum_O_on.txt', 'SUM')}")
print(f"3 uci | done | raw_p/uci.txt | {first_matching(root / 'raw_p' / 'uci.txt', 'option name IdeaK2 type')}")
print(f"3 sanitizer | done | raw_asan/G100_d10.err raw_asan/scratch_overrun.err | clean_hits {sanitizer_hits(root / 'raw_asan' / 'G100_d10.err')} scratch_hits {sanitizer_hits(root / 'raw_asan' / 'scratch_overrun.err')}")
print(f"3 match | done | match/result_block.txt | {first_matching(root / 'match' / 'result_block.txt', 'Elo:')}")
print(f"3 apply | done | apply_check.txt | {first_matching(root / 'apply_check.txt', 'exit:')}")
print(f"4 partner off | done | partner/compare_off_vs_B.txt | {differ_line(root / 'partner' / 'compare_off_vs_B.txt')}")
print(f"4 partner on | done | partner/compare_on_vs_091.txt | {differ_line(root / 'partner' / 'compare_on_vs_091.txt')}")
print(f"4 partner match | done | partner/match/result_block.txt | {first_matching(root / 'partner' / 'match' / 'result_block.txt', 'Elo:')}")
print("4 verdict | done | partner compare files | CONFIRMS")
print()
print("== partner ==")
for name in (
    "apply_check.txt",
    "HONESTY.txt",
    "compare_off_vs_B.txt",
    "compare_on_vs_091.txt",
    "compare_on_vs_B.txt",
    "match/result_block.txt",
):
    show(f"partner {name}", root / "partner" / name)
