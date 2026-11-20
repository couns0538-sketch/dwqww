"""o_table.py: sums, first three, and differences from the raw O transcripts.

Usage: python3 o_table.py B.raw POFF.raw PON.raw
"""
import re
import sys


def rows(path):
    last = None
    out = []
    for line in open(path, encoding="utf-8"):
        if line.startswith("info "):
            last = line
        elif line.startswith("bestmove"):
            match = re.search(r" nodes (\d+)", last or "")
            if match is None:
                sys.exit(f"STOP: no nodes on last info line before bestmove {len(out) + 1} in {path}: {last!r}")
            out.append(int(match.group(1)))
            last = None
    return out


def show(label, nums):
    print(f"{label} n={len(nums)} sum={sum(nums)} first={nums[0]} {nums[1]} {nums[2]}")


def main():
    if len(sys.argv) != 4:
        sys.exit("usage: o_table.py B.raw POFF.raw PON.raw")
    b, off, on = (rows(p) for p in sys.argv[1:])
    for name, nums in (("B", b), ("Poff", off), ("Pon", on)):
        if len(nums) != 200:
            sys.exit(f"STOP: {name} has {len(nums)} positions")
    show("B", b)
    show("Poff", off)
    show("Pon", on)
    differ_off = sum(1 for x, y in zip(b, off) if x != y)
    differ_on = sum(1 for x, y in zip(b, on) if x != y)
    print(f"Poff_differ_from_B {differ_off}")
    print(f"Pon_differ_from_B {differ_on}")
    print(f"B_expected_sum 9500069 match {sum(b) == 9500069}")
    print(f"B_expected_first 41311 24872 28574 match {b[:3] == [41311, 24872, 28574]}")
    print(f"Pon_expected_sum 8921190 match {sum(on) == 8921190}")
    print(f"Pon_expected_first 24693 26341 35070 match {on[:3] == [24693, 26341, 35070]}")
    print(f"Pon_expected_differ 200 match {differ_on == 200}")


if __name__ == "__main__":
    main()
