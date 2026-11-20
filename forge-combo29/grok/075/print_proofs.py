#!/usr/bin/env python3
"""Read the raw logs and print the proof numbers. Nothing here is typed."""
import pathlib
import sys

root = pathlib.Path(sys.argv[1])

def last_line(name):
    lines = (root / name).read_text(encoding="utf-8").splitlines()
    return lines[-1] if lines else ""

def result_nodes(name):
    nodes = []
    for line in (root / name).read_text(encoding="utf-8").splitlines():
        if line.startswith("RESULT "):
            bits = line.split()
            nodes.append(int(bits[bits.index("nodes") + 1]))
    return nodes

def show(title, name):
    print(title)
    print(last_line(name))

show("bench11_b", "honesty_b_bench11.txt")
show("bench13_b", "honesty_b_bench13.txt")
show("bench16_b", "honesty_b_bench16.txt")
show("perft5_b", "honesty_b_perft5.txt")
show("bench11_p", "honesty_p_bench11.txt")
show("bench13_p", "honesty_p_bench13.txt")
show("bench16_p", "honesty_p_bench16.txt")
show("perft5_p", "honesty_p_perft5.txt")

def cmp(label, a, b):
    left, right = result_nodes(a), result_nodes(b)
    n = min(len(left), len(right))
    differ = sum(1 for i in range(n) if left[i] != right[i])
    print(label)
    print("left_n", len(left), "left_sum", sum(left), "right_n", len(right), "right_sum", sum(right), "differ", differ)

cmp("O_off", "o_b_d12.txt", "o_p_off_d12.txt")
cmp("G_off", "g_b_d12.txt", "g_p_off_d12.txt")
cmp("O_on", "o_b_d12.txt", "o_p_on_d12.txt")

uci = (root / "uci_p.txt").read_text(encoding="utf-8").splitlines()
print("uci_options")
for line in uci:
    if "IdeaS33" in line:
        print(line)
meta = (root / "asan_g100_d10.txt.meta").read_text(encoding="utf-8")
print("asan_meta")
print(meta)
errors = 0
for line in (root / "asan_g100_d10.txt").read_text(encoding="utf-8").splitlines():
    if "ERROR:" in line or "runtime error:" in line:
        errors += 1
print("asan_error_lines", errors)
print("asan_positions", len(result_nodes("asan_g100_d10.txt")))
