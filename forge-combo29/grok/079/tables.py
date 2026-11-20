#!/usr/bin/env python3
"""Print the proof tables from the raw node files. Does not invent numbers."""

import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name: str) -> list[int]:
    return [int(line) for line in (HERE / name).read_text(encoding="utf-8").split() if line.strip()]


def differ(a: str, b: str) -> None:
    left, right = load(a), load(b)
    count = sum(x != y for x, y in zip(left, right))
    print(f"{a} vs {b} n={len(left)}/{len(right)} differ={count} sum_left={sum(left)} sum_right={sum(right)}")


def main() -> None:
    print("honesty B")
    print((HERE / "HONESTY_B.txt").read_text(encoding="utf-8"), end="")
    print("honesty P")
    print((HERE / "HONESTY_P.txt").read_text(encoding="utf-8"), end="")
    first = load("B_O_d12.nodes")[:3]
    print("B O first3", *first)
    differ("B_O_d12.nodes", "P_off_O_d12.nodes")
    differ("B_G_d12.nodes", "P_off_G_d12.nodes")
    differ("B_O_d12.nodes", "P_on_O_d12.nodes")
    exe = "/tmp/forge-asan/forge"
    meta_path = HERE / "asan_G100_d10.meta"
    meta = meta_path.read_text(encoding="utf-8")
    started = ""
    for line in meta.splitlines():
        if line.startswith("exe "):
            started = line.split(" ", 1)[1]
    count = subprocess.check_output(["nm", "-C", started or exe], text=True)
    asan_n = sum(1 for line in count.splitlines() if "__asan_" in line)
    print(f"asan exe {started or exe}")
    print(f"nm -C grep -c __asan_ {asan_n}")
    raw = (HERE / "asan_G100_d10.raw.txt").read_text(encoding="utf-8", errors="replace")
    clean_hits = sum(1 for line in raw.splitlines() if "AddressSanitizer" in line or "runtime error" in line)
    print(f"clean sanitizer lines {clean_hits}")
    bad = (HERE / "asan_bad.partial.txt").read_text(encoding="utf-8", errors="replace")
    summaries = [line for line in bad.splitlines() if line.startswith("SUMMARY:")]
    print("bad summary", summaries[0] if summaries else "MISSING")
    extra = f"nm_asan_count {asan_n}\nclean_sanitizer_lines {clean_hits}\n"
    if "nm_asan_count " not in meta:
        meta_path.write_text(meta + extra, encoding="utf-8")


if __name__ == "__main__":
    main()
