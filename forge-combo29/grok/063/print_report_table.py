#!/usr/bin/env python3
"""Print the report table from the evidence files in this folder."""
import pathlib

here = pathlib.Path(__file__).resolve().parent

def text(name):
    return (here / name).read_text().strip()

def line_with(name, prefix):
    for line in text(name).splitlines():
        if line.startswith(prefix):
            return line
    return "missing"

def nodes_summary(name):
    rows = []
    for line in (here / name).read_text().splitlines():
        if not line.strip():
            continue
        index, nodes = line.split()
        rows.append((int(index), int(nodes)))
    rows.sort()
    first = " ".join(str(nodes) for _, nodes in rows[:3])
    total = sum(nodes for _, nodes in rows)
    return f"positions {len(rows)} first3 {first} sum {total}"

rows = [
    ("STEP 1 seat", "done", "SEAT.txt stamps.txt", text("SEAT.txt")),
    ("STEP 2 honesty B", "done", "HONESTY_B.txt", line_with("HONESTY_B.txt", "honesty_b")),
    ("STEP 2 O and G baseline", "done", "O_B_d12.nodes G_B_d12.nodes", nodes_summary("O_B_d12.nodes") + "; " + nodes_summary("G_B_d12.nodes")),
    ("STEP 3 prediction", "done", "prediction.txt", "committed before the patched measurements"),
    ("apply check", "done", "apply_check.txt", text("apply_check.txt")),
    ("proof 1 honesty P", "done", "HONESTY_P.txt", line_with("HONESTY_P.txt", "honesty_p")),
    ("proof 2 switch off", "done", "compare_O_off.txt compare_G_off.txt", line_with("compare_O_off.txt", "differ") + "; " + line_with("compare_G_off.txt", "differ")),
    ("proof 3 switch on O", "done", "compare_O_on.txt sum_O_on.txt", line_with("compare_O_on.txt", "differ") + "; " + line_with("sum_O_on.txt", "sum")),
    ("proof 3 why O is 0", "done", "compare_rook.txt compare_G_on.txt", line_with("compare_rook.txt", "differ") + "; " + line_with("compare_G_on.txt", "differ")),
    ("proof 4 uci options", "done", "uci_p.txt", " | ".join(line for line in text("uci_p.txt").splitlines() if "IdeaS15" in line)),
    ("proof 5 sanitizer", "done", "san_g100.meta san_g100.hits san_scratch.hits", line_with("san_g100.meta", "nm_asan_symbols") + "; " + line_with("san_g100.hits", "sanitizer_lines") + "; " + line_with("san_scratch.hits", "sanitizer_lines")),
    ("test match", "done", "match_og_summary.txt match_og.txt", text("match_og_summary.txt").replace("\n", "; ")),
    ("partner 013 proofs", "done", "partner_honesty.txt partner_compare_off.txt partner_compare_on.txt", line_with("partner_honesty.txt", "partner_honesty") + "; off " + line_with("partner_compare_off.txt", "differ") + "; on " + line_with("partner_compare_on.txt", "differ")),
    ("partner match", "done", "partner_match_summary.txt", text("partner_match_summary.txt").replace("\n", "; ")),
]
print("step | status | evidence | result")
for step, status, evidence, result in rows:
    print(f"{step} | {status} | {evidence} | {result}")
