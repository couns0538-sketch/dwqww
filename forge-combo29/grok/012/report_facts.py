#!/usr/bin/env python3
"""Read the raw evidence and print the report table and the proof numbers."""
from pathlib import Path

folder = Path(__file__).resolve().parent


def text(name: str) -> str:
    return (folder / name).read_text()


def row_sum(name: str) -> str:
    nodes = []
    for line in text(name).splitlines():
        if line.strip():
            nodes.append(int(line.split("\t")[1]))
    return f"positions {len(nodes)} sum {sum(nodes)} first3 {nodes[0]} {nodes[1]} {nodes[2]}"


def nodes_of(name: str) -> str:
    for line in text(name).splitlines():
        if "nodes " in line and ("bench depth" in line or line.startswith("nodes ")):
            return line
    raise SystemExit(f"no nodes line in {name}")


print("HONESTY_B")
for name in ("honesty_b_bench11.txt", "honesty_b_bench13.txt", "honesty_b_bench16.txt", "honesty_b_perft5.txt"):
    print(nodes_of(name))
print("HONESTY_P")
for name in ("honesty_p_bench11.txt", "honesty_p_bench13.txt", "honesty_p_bench16.txt", "honesty_p_perft5.txt"):
    print(nodes_of(name))
print("PARTNER_HONESTY")
for name in ("partner_bench11.txt", "partner_bench13.txt", "partner_bench16.txt", "partner_perft5.txt"):
    print(nodes_of(name))
print("PROOFS")
for name in ("cmp_off_O.txt", "cmp_off_G.txt", "cmp_on_O.txt", "cmp_on_G.txt", "cmp_probe.txt", "sum_on_O.txt", "why_o_zero.txt", "partner_cmp_off_O.txt", "partner_cmp_on_O.txt", "partner_apply_check.txt"):
    print(f"--- {name}")
    print(text(name).rstrip())
print("UCI")
for line in text("uci_p.txt").splitlines():
    if "DeadMaterial" in line or "IdeaP20" in line or line.startswith("id name"):
        print(line)
print("ASAN")
for line in text("asan_G100_d10.meta").splitlines():
    if line.startswith("nm_"):
        print(line)
raw = text("asan_G100_d10.raw.txt")
print("asan_error_lines", sum(1 for line in raw.splitlines() if "ERROR:" in line or "runtime error" in line or "LeakSanitizer" in line))
print("SCRATCH")
for line in text("scratch_asan.raw.txt").splitlines():
    if "ERROR:" in line or line.startswith("SUMMARY:"):
        print(line)
print("MATCH")
print(text("match_og_summary.txt").rstrip())
print("PARTNER_MATCH")
print(text("partner_match_summary.txt").rstrip())
print("TABLE")
print("step | status | evidence | result")
items = [
    ("1 seat", "done", "SEAT.txt", "seat file present"),
    ("2 honesty B", "done", "HONESTY_B.txt", nodes_of("honesty_b_bench11.txt").split("nodes ")[1].split()[0]),
    ("2 O sum", "done", "B_O_d12.rows.txt", row_sum("B_O_d12.rows.txt")),
    ("2 G sum", "done", "B_G_d12.rows.txt", row_sum("B_G_d12.rows.txt")),
    ("3 patch applies", "done", "apply_check.txt", text("apply_check.txt").strip()),
    ("3 proof off O", "done", "cmp_off_O.txt", text("cmp_off_O.txt").strip().replace("\n", "; ")),
    ("3 proof off G", "done", "cmp_off_G.txt", text("cmp_off_G.txt").strip().replace("\n", "; ")),
    ("3 proof on O", "done", "cmp_on_O.txt", text("cmp_on_O.txt").strip().replace("\n", "; ")),
    ("3 uci options", "done", "uci_p.txt", " | ".join(line for line in text("uci_p.txt").splitlines() if "DeadMaterial" in line or "IdeaP20" in line)),
    ("3 sanitizer", "done", "asan_G100_d10.meta", next(line for line in text("asan_G100_d10.meta").splitlines() if line.startswith("nm_asan_count=")) + f" error_lines {sum(1 for line in text('asan_G100_d10.raw.txt').splitlines() if 'ERROR:' in line or 'runtime error' in line or 'LeakSanitizer' in line)}"),
    ("3 scratch", "done", "scratch_asan.raw.txt", next(line for line in text("scratch_asan.raw.txt").splitlines() if line.startswith("SUMMARY:"))),
    ("3 match", "done", "match_og_summary.txt", "1106 games"),
    ("4 partner", "done", "partner_cmp_on_O.txt", text("partner_cmp_on_O.txt").strip().replace("\n", "; ")),
    ("4 partner match", "done", "partner_match_summary.txt", "600 games"),
]
for step, status, evidence, result in items:
    print(f"{step} | {status} | {evidence} | {result}")
