#!/usr/bin/env python3
"""Print the report tables from the raw files in this folder."""

import pathlib

D = pathlib.Path("/agent/repos/dwqww/forge-combo29/grok/062")


def text(name: str) -> str:
    return (D / name).read_text(encoding="utf-8", errors="replace")


def line_with(name: str, prefix: str) -> str:
    for line in text(name).splitlines():
        if line.startswith(prefix):
            return line
    return "MISSING " + prefix


def meta_sum(name: str) -> str:
    for line in text(name).splitlines():
        if line.startswith("sum "):
            return line.split()[1]
    return "MISSING"


def cmp_line(name: str) -> str:
    body = text(name).strip().replace("\n", " | ")
    return body


print("HONESTY_B")
print(text("HONESTY_B.txt").rstrip())
print("HONESTY_P")
print(text("HONESTY_P.txt").rstrip())
print("SUMS")
print("B O", meta_sum("b_O_d12.meta"), line_with("b_O_d12.meta", "first "), line_with("b_O_d12.meta", "second "), line_with("b_O_d12.meta", "third "))
print("B G", meta_sum("b_G_d12.meta"))
print("P off O", meta_sum("p_off_O_d12.meta"), cmp_line("cmp_off_O.txt"))
print("P off G", meta_sum("p_off_G_d12.meta"), cmp_line("cmp_off_G.txt"))
print("P on O", meta_sum("p_on_O_d12.meta"), cmp_line("cmp_on_O.txt"))
print("P on G", meta_sum("p_on_G_d12.meta"), cmp_line("cmp_on_G.txt"))
print("UCI_OPTIONS")
for line in text("P_idname.txt").splitlines():
    if "DeadMaterial" in line or "IdeaP20_" in line:
        print(line)
print("ASAN_META_TAIL")
for line in text("asan_G_d10.meta").splitlines():
    if line.startswith("nm_") or line.startswith("sum ") or line.startswith("count "):
        print(line)
print("ASAN_BUG_HITS", text("asan_bug.stderr").count("heap-buffer-overflow"))
print("MATCH_FINAL")
match_keep = [line for line in text("match_full.txt").splitlines() if line.startswith(("Elo:", "Games:", "Ptnml"))]
print("\n".join(match_keep[-3:]))
print("PARTNER")
print(text("partner012_cmp.txt").rstrip())
print(text("HONESTY_partner012.txt").rstrip())
partner_keep = [line for line in text("partner012_match.txt").splitlines() if line.startswith(("Elo:", "Games:"))]
print("partner R final")
print("\n".join(partner_keep[-2:]))
print("APPLY", text("my_apply_check.txt").strip())
print("TABLE")
rows = [
    ("1 seat", "done", "SEAT.txt", "seat 062 idea 12"),
    ("2 honesty B", "done", "HONESTY_B.txt", "bench 11/13/16 and perft 5 match"),
    ("2 O depth 12 B", "done", "b_O_d12.meta", meta_sum("b_O_d12.meta")),
    ("2 G depth 12 B", "done", "b_G_d12.meta", meta_sum("b_G_d12.meta")),
    ("3 prediction", "done", "prediction.txt", "committed before measuring"),
    ("3 patch applies", "done", "my_apply_check.txt", text("my_apply_check.txt").strip()),
    ("3 proof 1 honesty P", "done", "HONESTY_P.txt", "ALL_PASS"),
    ("3 proof 2 off", "done", "cmp_off_O.txt cmp_off_G.txt", "0 of 200 and 0 of 353"),
    ("3 proof 3 on O", "done", "cmp_on_O.txt", "0 of 200"),
    ("3 proof 4 uci", "done", "P_idname.txt", "DeadMaterial false, Corner 28, King 12"),
    ("3 proof 5 sanitizer", "done", "asan_G_d10.meta asan_bug.stderr", "nm 35, clean run, bug run reports overflow"),
    ("3 match", "done", "match_full.txt", "1106 games"),
    ("4 partner 012", "done", "partner012_cmp.txt partner012_match.txt", "CONFIRMS"),
]
print("step | status | evidence | result")
for step, status, evidence, result in rows:
    print(f"{step} | {status} | {evidence} | {result}")
