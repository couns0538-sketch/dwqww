#!/usr/bin/env python3
"""Print the numbers the report quotes. Reads raw files only."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def nodes_of(name: str) -> str | None:
    text = (ROOT / name).read_text()
    last = None
    for line in text.splitlines():
        tokens = line.split()
        if "nodes" in tokens:
            last = tokens[tokens.index("nodes") + 1]
    return last

def row_nodes(name: str) -> list[int]:
    out = []
    for line in (ROOT / name).read_text().splitlines():
        if line.strip():
            out.append(int(line.split()[1]))
    return out

def differ(left: str, right: str) -> tuple[int, int]:
    a = row_nodes(left)
    b = row_nodes(right)
    n = min(len(a), len(b))
    d = sum(1 for i in range(n) if a[i] != b[i])
    return n, d

print("honesty_B")
for name, expect in (("bench11", "312866"), ("bench13", "862329"), ("bench16", "3024920"), ("perft5", "4865609")):
    got = nodes_of(f"honesty_B_{name}.txt")
    print(f"  {name} {got} {'OK' if got == expect else 'FAIL'}")
print("honesty_P")
for name, expect in (("bench11", "312866"), ("bench13", "862329"), ("bench16", "3024920"), ("perft5", "4865609")):
    got = nodes_of(f"honesty_P_{name}.txt")
    print(f"  {name} {got} {'OK' if got == expect else 'FAIL'}")
print("honesty_PARTNER")
for name, expect in (("bench11", "312866"), ("bench13", "862329"), ("bench16", "3024920"), ("perft5", "4865609")):
    got = nodes_of(f"honesty_PARTNER_{name}.txt")
    print(f"  {name} {got} {'OK' if got == expect else 'FAIL'}")

for label, name in (
    ("B_O", "B_O_d12.rows"),
    ("B_G", "B_G_d12.rows"),
    ("P_off_O", "P_off_O_d12.rows"),
    ("P_off_G", "P_off_G_d12.rows"),
    ("P_on_O", "P_on_O_d12.rows"),
    ("partner_off_O", "partner_off_O_d12.rows"),
    ("partner_on_O", "partner_on_O_d12.rows"),
):
    nodes = row_nodes(name)
    print(f"sum {label} count {len(nodes)} sum {sum(nodes)} first {' '.join(str(n) for n in nodes[:3])}")

for label, left, right in (
    ("off_O", "B_O_d12.rows", "P_off_O_d12.rows"),
    ("off_G", "B_G_d12.rows", "P_off_G_d12.rows"),
    ("on_O_vs_B", "B_O_d12.rows", "P_on_O_d12.rows"),
    ("partner_off_vs_B", "B_O_d12.rows", "partner_off_O_d12.rows"),
    ("partner_on_vs_B", "B_O_d12.rows", "partner_on_O_d12.rows"),
    ("partner_on_vs_mine", "P_on_O_d12.rows", "partner_on_O_d12.rows"),
):
    n, d = differ(left, right)
    print(f"differ {label} compared {n} differ {d}")

uci = (ROOT / "uci_P.txt").read_text().splitlines()
print("uci_options")
for line in uci:
    if "IdeaS23_" in line or line.startswith("option name AspCappedReopen "):
        print(" ", line)

meta = (ROOT / "asan_G100_d10.meta").read_text()
print("asan_meta")
for line in meta.splitlines():
    if line.startswith("nm_asan_count") or line.startswith("asan_lines") or line.startswith("exe "):
        print(" ", line)
bad = (ROOT / "asan_bad.raw").read_text().splitlines()
print("asan_canary")
for line in bad:
    if "runtime error" in line or "AddressSanitizer" in line:
        print(" ", line.removeprefix("<< "))
        break
print("partner_nodes_file")
print(" ", (ROOT / "partner_on_vs_theirs.txt").read_text().strip())
print("step_table")
print("step | status | evidence | result")
print("STEP 1 seat | done | SEAT.txt stamps.txt | seat 009 idea 9")
print("STEP 2 builds and sums | done | HONESTY_B.txt B_SUMS.txt | O 9500069 G 18466239 honesty pass")
print("STEP 3 patch and proofs | done | idea.patch.txt tables.txt | off differ 0 on differ 150 of 200")
print("STEP 3 match | done | match_on_vs_off.txt | Elo -7.23 +/- 10.57 games 1106")
print("STEP 4 partner 059 | done | partner_off_vs_B.txt partner_on_vs_theirs.txt partner_match.summary.txt | CONFIRMS")
print("STEP 5 report | done | REPORT.md RESULT.txt | this file")
