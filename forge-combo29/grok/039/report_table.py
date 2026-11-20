#!/usr/bin/env python3
"""Print the report table from the raw files in this directory."""
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(name):
    return (HERE / name).read_text()


def meta_value(name, key):
    for line in read(name).splitlines():
        if line.startswith(key + "="):
            return line.split("=", 1)[1]
    return ""


def cmp_field(name, key):
    for line in read(name).splitlines():
        if line.startswith(key + " "):
            return line.split(" ", 1)[1]
    return ""


def elo_line(name):
    found = "missing"
    for line in read(name).splitlines():
        if line.startswith("Elo:"):
            found = line
    return found


rows = [
    ("STEP 1 seat", "done", "SEAT.txt", read("SEAT.txt").strip()),
    ("STEP 2 honesty B", "done", "HONESTY_B.txt", read("HONESTY_B.txt").replace("\n", " | ").strip()),
    ("STEP 2 O depth 12", "done", "B_O_d12.meta", f"sum={meta_value('B_O_d12.meta', 'sum')} positions={meta_value('B_O_d12.meta', 'positions')}"),
    ("STEP 2 G depth 12", "done", "B_G_d12.meta", f"sum={meta_value('B_G_d12.meta', 'sum')} positions={meta_value('B_G_d12.meta', 'positions')}"),
    ("3b prediction", "done", "prediction.txt", "committed before measuring P"),
    ("3c patch applies", "done", "apply_check_own.txt", read("apply_check_own.txt").strip()),
    ("3d honesty P", "done", "HONESTY_P.txt", read("HONESTY_P.txt").replace("\n", " | ").strip()),
    ("3d off O", "done", "cmp_off_O.txt", f"differ={cmp_field('cmp_off_O.txt', 'differ')} equal={cmp_field('cmp_off_O.txt', 'equal')}"),
    ("3d off G", "done", "cmp_off_G.txt", f"differ={cmp_field('cmp_off_G.txt', 'differ')} equal={cmp_field('cmp_off_G.txt', 'equal')}"),
    ("3d on O", "done", "cmp_on_O.txt", f"differ={cmp_field('cmp_on_O.txt', 'differ')} sum_right={cmp_field('cmp_on_O.txt', 'sum_right')}"),
    ("3d uci options", "done", "P_uci.txt", " ; ".join(line.strip() for line in read("P_uci.txt").splitlines() if "IdeaA8" in line)),
    ("3d sanitizer", "done", "asan_G_d10.meta", f"nm_asan_count={meta_value('asan_G_d10.meta', 'nm_asan_count')} sanitizer_lines={meta_value('asan_G_d10.meta', 'sanitizer_lines')} positions={meta_value('asan_G_d10.meta', 'positions')}"),
    ("3d sanitizer canary", "done", "canary_d10.meta", f"nm_asan_count={meta_value('canary_d10.meta', 'nm_asan_count')} sanitizer_lines={meta_value('canary_d10.meta', 'sanitizer_lines')}"),
    ("3e match", "done", "match.txt", elo_line("match.txt")),
    ("STEP 4 partner patch", "done", "apply_check_partner.txt", read("apply_check_partner.txt").strip()),
    ("STEP 4 partner off", "done", "cmp_partner_off_O.txt", f"differ={cmp_field('cmp_partner_off_O.txt', 'differ')}"),
    ("STEP 4 partner on vs own rows", "done", "cmp_partner_on_O.txt", f"differ={cmp_field('cmp_partner_on_O.txt', 'differ')} sum_mine={cmp_field('cmp_partner_on_O.txt', 'sum_mine')}"),
    ("STEP 4 partner on vs B", "done", "cmp_partner_on_vs_B.txt", f"differ={cmp_field('cmp_partner_on_vs_B.txt', 'differ')} sum_right={cmp_field('cmp_partner_on_vs_B.txt', 'sum_right')}"),
    ("STEP 4 partner match", "done", "partner_match.txt", elo_line("partner_match.txt")),
]

print("step | status | evidence | result")
for step, status, evidence, result in rows:
    print(f"{step} | {status} | {evidence} | {result}")
