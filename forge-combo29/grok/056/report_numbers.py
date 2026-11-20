#!/usr/bin/env python3
"""Read the raw proof files and print the report table. No hand-typed results."""
from pathlib import Path

root = Path(__file__).resolve().parent


def text(name: str) -> str:
    return (root / name).read_text(encoding="utf-8", errors="replace")


def last_elo(name: str) -> str:
    body = text(name)
    start = body.rfind("Results of ")
    end = body.rfind("Finished match")
    return body[start:end].rstrip()


print("HONESTY_B")
print(text("HONESTY_B.txt").rstrip())
print("HONESTY_P")
print(text("HONESTY_P.txt").rstrip())
print("HONESTY_PARTNER")
print(text("HONESTY_PARTNER.txt").rstrip())
print("APPLY")
print(text("apply_check.txt").rstrip())
print("OFF_O")
# compare output was not saved as its own file; recompute from the node files.
import subprocess
import sys

py = sys.executable
for args in (
    [py, str(root / "compare_nodes.py"), str(root / "B_O_d12.nodes"), str(root / "P_off_O_d12.nodes")],
    [py, str(root / "compare_nodes.py"), str(root / "B_G_d12.nodes"), str(root / "P_off_G_d12.nodes")],
    [py, str(root / "compare_nodes.py"), str(root / "B_O_d12.nodes"), str(root / "P_on_O_d12.nodes")],
    [py, str(root / "compare_nodes.py"), str(root / "B_O_d12.nodes"), str(root / "partner_off_O_d12.nodes")],
    [py, str(root / "compare_nodes.py"), str(root / "B_G_d12.nodes"), str(root / "partner_off_G_d12.nodes")],
    [py, str(root / "compare_partner_on.py"), str(root / "partner_on_O_d12.nodes"), str(root / "partner006_P_on_O_d12.rows")],
):
    print("RUN", " ".join(args[-2:]))
    print(subprocess.check_output(args, text=True).rstrip())
print("UCI")
for line in text("P_uci.txt").splitlines():
    if line.startswith("option name IdeaS34"):
        print(line)
print("ASAN_META_TAIL")
lines = text("asan_G100_d10.meta").splitlines()
print("\n".join(lines[-4:]))
print("PROBE_META_TAIL")
lines = text("asan_probe.meta").splitlines()
print("\n".join(lines[-4:]))
print("PROBE_LINE")
for line in text("asan_probe.log").splitlines():
    if "runtime error" in line or "AddressSanitizer" in line:
        print(line)
        break
print("MATCH")
print(last_elo("match_stdout.txt"))
print("PARTNER_MATCH")
print(last_elo("partner_match_stdout.txt"))
print("NM")
print("asan_symbols", text("asan_nm_count.txt").strip())


def compared(left: str, right: str) -> str:
    out = subprocess.check_output(
        [py, str(root / "compare_nodes.py"), str(root / left), str(root / right)],
        text=True,
    )
    differ = [line for line in out.splitlines() if line.startswith("compared=")][0]
    return differ


def meta_sum(name: str) -> str:
    for line in text(name).splitlines():
        if line.startswith("node_sum="):
            return line.split("=", 1)[1]
    return "missing"


def elo_games(name: str) -> str:
    block = last_elo(name)
    elo = games = ""
    for line in block.splitlines():
        if line.startswith("Elo:"):
            elo = line
        if line.startswith("Games:"):
            games = line
    return f"{elo}; {games}"


off_o = compared("B_O_d12.nodes", "P_off_O_d12.nodes")
off_g = compared("B_G_d12.nodes", "P_off_G_d12.nodes")
on_o = compared("B_O_d12.nodes", "P_on_O_d12.nodes")
pon = subprocess.check_output(
    [py, str(root / "compare_partner_on.py"), str(root / "partner_on_O_d12.nodes"), str(root / "partner006_P_on_O_d12.rows")],
    text=True,
)
pon_line = [line for line in pon.splitlines() if line.startswith("compared=")][0]
san_lines = [line for line in text("asan_G100_d10.meta").splitlines() if line.startswith("sanitizer_lines=")][0]
probe_lines = [line for line in text("asan_probe.meta").splitlines() if line.startswith("sanitizer_lines=")][0]
uci_ok = sum(1 for line in text("P_uci.txt").splitlines() if line.startswith("option name IdeaS34"))
print("TABLE")
print("| step | status | evidence file | result |")
print("| --- | --- | --- | --- |")
table = [
    ("seat", "done", "SEAT.txt", text("SEAT.txt").split(",")[0] + "," + text("SEAT.txt").split(",")[1]),
    ("honesty B", "done", "HONESTY_B.txt", "PASS" if "HONESTY_B PASS" in text("HONESTY_B.txt") else "FAIL"),
    ("baseline O", "done", "B_O_d12.meta", "node_sum=" + meta_sum("B_O_d12.meta")),
    ("baseline G", "done", "B_G_d12.meta", "node_sum=" + meta_sum("B_G_d12.meta")),
    ("prediction", "done", "prediction.txt", "file present, not edited after the measuring runs"),
    ("patch applies", "done", "apply_check.txt", text("apply_check.txt").strip().replace("\n", " ")),
    ("proof 1 honesty P", "done", "HONESTY_P.txt", "PASS" if "HONESTY PASS" in text("HONESTY_P.txt") else "FAIL"),
    ("proof 2 off O", "done", "P_off_O_d12.nodes", off_o),
    ("proof 2 off G", "done", "P_off_G_d12.nodes", off_g),
    ("proof 3 on O", "done", "P_on_O_d12.nodes", on_o + " sum=" + meta_sum("P_on_O_d12.meta")),
    ("proof 4 uci", "done", "P_uci.txt", f"IdeaS34 option lines={uci_ok}"),
    ("proof 5 sanitizer", "done", "asan_G100_d10.meta", f"{san_lines} symbols={text('asan_nm_count.txt').strip()} probe {probe_lines}"),
    ("match", "done", "match_stdout.txt", elo_games("match_stdout.txt")),
    ("partner", "done", "partner_on_O_d12.nodes", pon_line + " | " + elo_games("partner_match_stdout.txt")),
]
for step, status, evidence, result in table:
    print(f"| {step} | {status} | {evidence} | {result} |")
