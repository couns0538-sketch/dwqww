#!/usr/bin/env python3
"""Print the report table from the raw result files in this folder."""
from pathlib import Path

out = Path(__file__).resolve().parent

def read(name: str) -> str:
    p = out / name
    return p.read_text() if p.exists() else "MISSING"

def field(text: str, key: str) -> str:
    for line in text.splitlines():
        if line.startswith(key + "=") or line.startswith(key + " "):
            return line.split("=", 1)[-1].strip() if "=" in line else line
    return ""

def sum_of(name: str) -> str:
    text = read(name)
    for line in text.splitlines():
        if line.startswith("sum="):
            return line.split("=", 1)[1]
    return "MISSING"

rows = [
    ("STEP 1 seat", "done", "SEAT.txt stamps.txt", read("SEAT.txt").strip()),
    ("honesty B", "done", "HONESTY_B.txt", read("HONESTY_B.txt").strip().replace("\n", " | ")),
    ("baseline O d12", "done", "B_O_d12.sum.txt", f"sum={sum_of('B_O_d12.sum.txt')}"),
    ("baseline G d12", "done", "B_G_d12.sum.txt", f"sum={sum_of('B_G_d12.sum.txt')}"),
    ("prediction", "done", "prediction.txt", "committed before measuring"),
    ("patch applies", "done", "apply_check.txt", read("apply_check.txt").strip()),
    ("honesty P", "done", "HONESTY_P.txt", read("HONESTY_P.txt").strip().replace("\n", " | ")),
    ("uci options", "done", "uci_options_p.txt", read("uci_options_p.txt").strip().replace("\n", " | ")),
    ("proof off O", "done", "cmp_off_O.txt", read("cmp_off_O.txt").strip().replace("\n", " | ")),
    ("proof off G", "done", "cmp_off_G.txt", read("cmp_off_G.txt").strip().replace("\n", " | ")),
    ("proof on O", "done", "cmp_on_O.txt", read("cmp_on_O.txt").strip().replace("\n", " | ") + f" sum={sum_of('P_on_O_d12.sum.txt')}"),
    ("sanitizer clean", "done", "asan_G100_d10.meta", field(read("asan_G100_d10.meta"), "nm_asan_symbol_lines") and (
        "nm_asan_symbol_lines=" + field(read("asan_G100_d10.meta"), "nm_asan_symbol_lines")
        + " crashed=" + field(read("asan_G100_d10.meta"), "crashed")
        + " asan_lines=" + str(sum(1 for ln in read("asan_G100_d10.raw.txt").splitlines() if "AddressSanitizer" in ln or "runtime error" in ln))
        + " " + read("asan_G100_d10.sum.txt").strip().replace("\n", " ")
    )),
    ("sanitizer trap", "done", "scratch_special.raw.txt", next((ln.strip() for ln in read("scratch_special.raw.txt").splitlines() if "SUMMARY: AddressSanitizer" in ln), "MISSING")),
    ("match O+G", "done", "match_OG.summary.txt", read("match_OG.summary.txt").strip().replace("\n", " | ")),
    ("partner apply", "done", "partner_apply_check.txt", read("partner_apply_check.txt").strip()),
    ("partner honesty", "done", "partner_honesty.txt", read("partner_honesty.txt").strip().replace("\n", " | ")),
    ("partner nodes", "done", "partner_compare.txt", read("partner_compare.txt").strip().replace("\n", " | ")),
    ("partner match", "done", "partner_match.summary.txt", read("partner_match.summary.txt").strip().replace("\n", " | ")),
]
print("step | status | evidence | result")
for step, status, evidence, result in rows:
    print(f"{step} | {status} | {evidence} | {result}")
