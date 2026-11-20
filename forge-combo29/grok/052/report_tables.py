#!/usr/bin/env python3
"""Read the raw result files and print the report tables."""
import pathlib

seat = pathlib.Path.home().joinpath("grok_seat.txt").read_text().strip()
root = pathlib.Path(pathlib.Path.home().joinpath("grok_repo.txt").read_text().strip())
d = root / "forge-combo29" / "grok" / seat


def show(name: str) -> None:
    print(f"--- {name} ---")
    print((d / name).read_text().rstrip())
    print()


def field(name: str, key: str) -> str:
    for line in (d / name).read_text().splitlines():
        if line.startswith(key):
            return line.split(None, 1)[1]
    return "MISSING"


off_o = field("cmp_off_O.txt", "differ")
off_g = field("cmp_off_G.txt", "differ")
on_o = field("cmp_on_O.txt", "differ")
pon = field("partner_cmp_on_claimed.txt", "differ")
poff = field("partner_cmp_off_O.txt", "differ")
print("step\tstatus\tevidence\tresult")
rows = [
    ("STEP 1", "done", "SEAT.txt", (d / "SEAT.txt").read_text().strip()),
    ("STEP 2", "done", "HONESTY_B.txt B_O_d12.sum B_G_d12.sum", "see those files"),
    ("STEP 3", "done", "cmp_off_O.txt cmp_off_G.txt cmp_on_O.txt match_summary.txt san_g100.meta", f"off O differ {off_o}; off G differ {off_g}; on O differ {on_o}"),
    ("STEP 4", "done", "partner_cmp_off_O.txt partner_cmp_on_claimed.txt partner_match_summary.txt partner_seat.txt", f"off differ {poff}; on vs claimed differ {pon}"),
    ("STEP 5", "done", "REPORT.md RESULT.txt", "this report"),
]
for row in rows:
    print("\t".join(row))
print()
for name in (
    "HONESTY_B.txt",
    "HONESTY_P.txt",
    "B_O_d12.sum",
    "B_G_d12.sum",
    "cmp_off_O.txt",
    "cmp_off_G.txt",
    "cmp_on_O.txt",
    "P_on_O.sum",
    "apply_check.txt",
    "match_summary.txt",
    "PARTNER_HONESTY.txt",
    "partner_cmp_off_O.txt",
    "partner_cmp_on_claimed.txt",
    "partner_on_O.sum",
    "partner_match_summary.txt",
    "san_g100.meta",
    "san_canary.meta",
    "prediction.txt",
    "stamps.txt",
):
    show(name)
print("--- IdeaS28 uci line ---")
for line in (d / "HONESTY_P_bench11.txt").read_text().splitlines():
    if "IdeaS28" in line:
        print(line)
print()
print("--- canary sanitizer line ---")
err = (d / "san_canary.err").read_text().splitlines()
print(err[0] if err else "MISSING")
