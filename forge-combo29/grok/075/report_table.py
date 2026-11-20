#!/usr/bin/env python3
"""Print the step table and the proof numbers from the raw files in this folder."""
import pathlib
import sys

root = pathlib.Path(sys.argv[1])

def text(name):
    return (root / name).read_text(encoding="utf-8")

def last(name):
    lines = text(name).splitlines()
    return lines[-1] if lines else ""

def results(name):
    nodes = []
    for line in text(name).splitlines():
        if line.startswith("RESULT "):
            bits = line.split()
            nodes.append(int(bits[bits.index("nodes") + 1]))
    return nodes

def differ(a, b):
    left, right = results(a), results(b)
    n = min(len(left), len(right))
    return len(left), sum(left), len(right), sum(right), sum(1 for i in range(n) if left[i] != right[i])

def plain(name):
    return [int(line.split()[0]) for line in text(name).splitlines() if line.strip()]

print("honesty_b_bench11", last("honesty_b_bench11.txt"))
print("honesty_b_bench13", last("honesty_b_bench13.txt"))
print("honesty_b_bench16", last("honesty_b_bench16.txt"))
print("honesty_b_perft5", last("honesty_b_perft5.txt"))
print("honesty_p_bench11", last("honesty_p_bench11.txt"))
print("honesty_p_bench13", last("honesty_p_bench13.txt"))
print("honesty_p_bench16", last("honesty_p_bench16.txt"))
print("honesty_p_perft5", last("honesty_p_perft5.txt"))
print("partner_bench11", last("partner_025_bench11.txt"))
print("partner_bench13", last("partner_025_bench13.txt"))
print("partner_bench16", last("partner_025_bench16.txt"))
print("partner_perft5", last("partner_025_perft5.txt"))

for label, a, b in (
    ("O_off", "o_b_d12.txt", "o_p_off_d12.txt"),
    ("G_off", "g_b_d12.txt", "g_p_off_d12.txt"),
    ("O_on", "o_b_d12.txt", "o_p_on_d12.txt"),
    ("partner_O_off", "o_b_d12.txt", "partner_025_o_off.txt"),
):
    ln, ls, rn, rs, d = differ(a, b)
    print(label, "left", ln, ls, "right", rn, rs, "differ", d)

mine = results("partner_025_o_on.txt")
theirs = plain("partner_025_O_on.nodes")
n = min(len(mine), len(theirs))
d = sum(1 for i in range(n) if mine[i] != theirs[i])
print("partner_O_on_vs_their_rows", "mine", len(mine), sum(mine), "theirs", len(theirs), sum(theirs), "differ", d)
base = results("o_b_d12.txt")
d_base = sum(1 for i in range(min(len(base), len(mine))) if base[i] != mine[i])
print("partner_O_on_vs_exe_B", "differ", d_base, "of", min(len(base), len(mine)))

asan_errors = 0
for line in text("asan_g100_d10.txt").splitlines():
    if "ERROR:" in line or "runtime error:" in line:
        asan_errors += 1
print("asan_g100_positions", len(results("asan_g100_d10.txt")), "error_lines", asan_errors)
meta = text("asan_g100_d10.txt.meta")
for line in meta.splitlines():
    if line.startswith("nm_asan_count="):
        print(line)
canary_hits = 0
for line in text("asan_canary.txt").splitlines():
    if "runtime error:" in line or "ERROR:" in line:
        canary_hits += 1
        print("canary", line)
print("canary_sanitizer_lines", canary_hits)
print("idea_apply_check_bytes", (root / "idea_apply_check.txt").stat().st_size)
print("partner_apply_check_bytes", (root / "partner_025_apply_check.txt").stat().st_size)
print("--- match ---")
print(text("match_final.txt").rstrip())
print("--- partner match ---")
print(text("partner_025_match_final.txt").rstrip())
