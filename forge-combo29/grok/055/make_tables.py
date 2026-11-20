#!/usr/bin/env python3
"""Print the report tables from raw files. Numbers are read, not typed."""
import pathlib
import re

folder = pathlib.Path(__file__).resolve().parent
node_re = re.compile(r"nodes (\d+)")


def last_nodes(name: str) -> str:
    found = node_re.findall((folder / name).read_text())
    return found[-1] if found else "MISSING"


def head_lines(name: str, count: int = 20) -> str:
    path = folder / name
    if not path.exists():
        return f"MISSING {name}"
    return "\n".join(path.read_text().splitlines()[:count])


print("HONESTY_B")
print((folder / "HONESTY_B.txt").read_text().rstrip())
print("HONESTY_P")
print((folder / "HONESTY_P.txt").read_text().rstrip())
print("BASELINE_SUMS")
for name in ("B_O_d12.txt", "B_G_d12.txt"):
    lines = (folder / name).read_text().splitlines()
    print(name, lines[0], lines[1])
print("OFF_COMPARE")
print((folder / "cmp_off_O.txt").read_text().rstrip())
print((folder / "cmp_off_G.txt").read_text().rstrip())
print("ON_COMPARE")
print((folder / "cmp_on_O.txt").read_text().rstrip())
print("UCI_OPTIONS")
for line in (folder / "uci_p.txt").read_text().splitlines():
    if "IdeaS37" in line:
        print(line)
print("ASAN_META_TAIL")
meta = (folder / "P_asan_G100.meta").read_text().splitlines()
print("\n".join(meta[:3]))
print("\n".join(meta[-4:]))
print("asan_positions", (folder / "P_asan_G100.txt").read_text().splitlines()[1])
print("asan_stderr_bytes", (folder / "P_asan_G100.stderr").stat().st_size)
print("SCRATCH_SANITIZER_FIRST")
stderr = (folder / "scratch_asan.stderr").read_text().splitlines()
print(stderr[0] if stderr else "MISSING")
print("MATCH")
log = (folder / "match_og.log").read_text().splitlines()
indexes = [index for index, line in enumerate(log) if line.startswith("Results of ")]
index = indexes[-1]
print("\n".join(log[index - 1:index + 12]))
print("pgn_events", sum(1 for line in (folder / "match_og.pgn").read_text().splitlines() if line.startswith("[Event ")))
print("PARTNER")
print("commit", (folder / "partner105_commit.txt").read_text().rstrip())
print((folder / "partner_apply_check.txt").read_text().rstrip())
print((folder / "partner_honesty.txt").read_text().rstrip())
print((folder / "partner_cmp_off.txt").read_text().rstrip())
print((folder / "partner_cmp_on.txt").read_text().rstrip())
print((folder / "partner_cmp_on_vs_B.txt").read_text().rstrip())
print("partner_uci")
print((folder / "partner_uci.txt").read_text().rstrip())
plog = (folder / "partner_r.log").read_text().splitlines()
pindexes = [index for index, line in enumerate(plog) if line.startswith("Results of ")]
pindex = pindexes[-1]
print("\n".join(plog[pindex - 1:pindex + 12]))
print("partner_pgn_events", sum(1 for line in (folder / "partner_r.pgn").read_text().splitlines() if line.startswith("[Event ")))
print("partner_unknown_option", sum(1 for line in plog if "unknown option" in line.lower()))
print("PREDICTION")
print((folder / "prediction.txt").read_text().rstrip())
print("ON_SUM", (folder / "P_on_O_d12.txt").read_text().splitlines()[0])
print("STEP_TABLE")
print("step\tstatus\tevidence\tresult")
rows = [
    ("1 seat", "done", "SEAT.txt", "seat file"),
    ("2 honesty B", "done", "HONESTY_B.txt", "HONESTY_B"),
    ("2 O and G sums", "done", "B_O_d12.txt B_G_d12.txt", "BASELINE_SUMS"),
    ("3 patch", "done", "idea.patch.txt apply_check.txt", "APPLY_CHECK_OK"),
    ("3 proof 1 honesty P", "done", "HONESTY_P.txt", "HONESTY_P"),
    ("3 proof 2 switch off", "done", "cmp_off_O.txt cmp_off_G.txt", "OFF_COMPARE"),
    ("3 proof 3 switch on", "done", "cmp_on_O.txt", "ON_COMPARE"),
    ("3 proof 4 uci", "done", "uci_p.txt", "UCI_OPTIONS"),
    ("3 proof 5 sanitizer", "done", "P_asan_G100.meta scratch_asan.stderr", "ASAN_META_TAIL"),
    ("3 match", "done", "match_og.log match_og.pgn", "MATCH"),
    ("4 partner", "done", "partner_cmp_off.txt partner_cmp_on.txt partner_r.log", "PARTNER"),
    ("5 report", "done", "REPORT.md RESULT.txt", "this report"),
]
for row in rows:
    print("\t".join(row))
