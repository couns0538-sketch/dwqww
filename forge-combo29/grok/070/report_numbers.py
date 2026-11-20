#!/usr/bin/env python3
"""Print the numbers the report quotes, by reading the raw evidence files."""
import pathlib
import sys

root = pathlib.Path(__file__).resolve().parent


def text(name):
    return (root / name).read_text(encoding="utf-8", errors="replace")


def nodes_line(name, needle):
    for line in text(name).splitlines():
        if needle in line:
            return line
    return "MISSING " + name


print("honesty_B")
for name, needle in (
    ("honesty_b_bench11.txt", "nodes"),
    ("honesty_b_bench13.txt", "nodes"),
    ("honesty_b_bench16.txt", "nodes"),
    ("honesty_b_perft5.txt", "nodes 4865609"),
):
    if name.endswith("perft5.txt"):
        last = [line for line in text(name).splitlines() if line.startswith("nodes ")]
        print(last[-1] if last else "MISSING perft")
    else:
        print(nodes_line(name, "bench depth"))

print("honesty_P")
for name in ("P_bench11.txt", "P_bench13.txt", "P_bench16.txt"):
    print(nodes_line(name, "bench depth"))
last = [line for line in text("P_perft5.txt").splitlines() if line.startswith("nodes ")]
print(last[-1] if last else "MISSING perft")

print("cmp_off_O")
print(text("cmp_off_O.txt"), end="")
print("cmp_off_G")
print(text("cmp_off_G.txt"), end="")
print("cmp_on_O_head")
print("\n".join(text("cmp_on_O.txt").splitlines()[:4]))
print("uci")
print(text("uci_options_IdeaS22.txt"), end="")
print("asan_meta_nm")
for line in text("asan_G_d10.meta").splitlines():
    if line.startswith("nm_"):
        print(line)
asan_hits = 0
for line in text("asan_G_d10.raw.txt").splitlines():
    if "AddressSanitizer" in line or "UndefinedBehaviorSanitizer" in line or "runtime error" in line:
        asan_hits += 1
print(f"asan_clean_hit_lines {asan_hits}")
scratch_hits = [
    line for line in text("asan_scratch.raw.txt").splitlines()
    if "heap-buffer-overflow" in line or "runtime error" in line
]
print(f"asan_scratch_hit_lines {len(scratch_hits)}")
if scratch_hits:
    print(scratch_hits[0])
print("match")
print(text("match_result.txt"), end="")
print("partner_apply")
print(text("partner020_apply_check.txt"), end="")
print("partner_off")
print(text("partner_cmp_off_O.txt"), end="")
print("partner_on_vs_theirs")
print(text("partner_cmp_on_O.txt"), end="")
print("partner_on_vs_B_head")
print("\n".join(text("partner_cmp_on_vs_B.txt").splitlines()[:4]))
print("partner_match")
print(text("partner_match_result.txt"), end="")
print("stamps")
print(text("stamps.txt"), end="")
