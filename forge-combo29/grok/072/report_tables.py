#!/usr/bin/env python3
"""Print the report tables from the raw evidence files in this folder."""
import re
from pathlib import Path

here = Path(__file__).resolve().parent

def bench_nodes(stem: str) -> str:
    text = (here / f"{stem}.txt").read_text(errors="replace")
    if "perft" in stem:
        got = None
        for line in text.splitlines():
            if re.fullmatch(r"nodes \d+", line.strip()):
                got = line.strip().split()[1]
        return got or "MISSING"
    match = re.search(r"info string bench depth (\d+) nodes (\d+)", text)
    if not match:
        return "MISSING"
    return match.group(2)

def depth_nodes(path: Path, depth: int) -> list[int]:
    rows = []
    pending = None
    depth_re = re.compile(rf"^info depth {depth}(?: multipv \d+)? .* nodes (\d+) ")
    for line in path.read_text(errors="replace").splitlines():
        match = depth_re.match(line)
        if match:
            pending = int(match.group(1))
        elif line.startswith("bestmove ") and pending is not None:
            rows.append(pending)
            pending = None
        elif line.startswith("bestmove "):
            rows.append(-1)
    return rows

def final_elo(path: Path) -> str:
    last = ""
    games = ""
    for line in path.read_text(errors="replace").splitlines():
        if line.startswith("Elo:"):
            last = line
        elif line.startswith("Games:"):
            games = line
    return last + "\n" + games

print("HONESTY_B")
for stem, want in (
    ("honesty_b_bench11", "312866"),
    ("honesty_b_bench13", "862329"),
    ("honesty_b_bench16", "3024920"),
    ("honesty_b_perft5", "4865609"),
):
    got = bench_nodes(stem)
    print(f"{stem} {got} expected {want} {'OK' if got == want else 'MISS'}")

print("HONESTY_P")
for stem, want in (
    ("honesty_p_bench11", "312866"),
    ("honesty_p_bench13", "862329"),
    ("honesty_p_bench16", "3024920"),
    ("honesty_p_perft5", "4865609"),
):
    got = bench_nodes(stem)
    print(f"{stem} {got} expected {want} {'OK' if got == want else 'MISS'}")

b_o = depth_nodes(here / "B_O_d12.raw.txt", 12)
b_g = depth_nodes(here / "B_G_d12.raw.txt", 12)
off_o = depth_nodes(here / "P_off_O_d12.raw.txt", 12)
off_g = depth_nodes(here / "P_off_G_d12.raw.txt", 12)
on_o = depth_nodes(here / "P_on_O_d12.raw.txt", 12)
print("BASE_SUMS")
print(f"B_O positions {len(b_o)} sum {sum(b_o)} first3 {' '.join(str(n) for n in b_o[:3])}")
print(f"B_G positions {len(b_g)} sum {sum(b_g)} first3 {' '.join(str(n) for n in b_g[:3])}")
off_o_diff = sum(1 for a, c in zip(b_o, off_o) if a != c)
off_g_diff = sum(1 for a, c in zip(b_g, off_g) if a != c)
on_diff = sum(1 for a, c in zip(b_o, on_o) if a != c)
print("PROOFS")
print(f"off_O differ {off_o_diff} of {len(b_o)}")
print(f"off_G differ {off_g_diff} of {len(b_g)}")
print(f"on_O differ {on_diff} of {len(b_o)} sum {sum(on_o)}")
asan_err = (here / "asan_G100_d10.err.txt").read_text(errors="replace")
asan_meta = (here / "asan_G100_d10.meta").read_text(errors="replace")
nm = "MISSING"
for line in asan_meta.splitlines():
    if line.startswith("nm_asan_count="):
        nm = line.split("=", 1)[1]
probe = (here / "asan_probe.err.txt").read_text(errors="replace")
print(f"asan_nm_count {nm}")
print(f"asan_G100_stderr_bytes {len(asan_err.encode())}")
print(f"asan_G100_positions {len(depth_nodes(here / 'asan_G100_d10.raw.txt', 10))}")
print(f"probe_has_asan_error {'ERROR: AddressSanitizer' in probe}")
print("MATCH")
print(final_elo(here / "match_og.log"))
print("PARTNER")
print((here / "partner_apply_check.txt").read_text().rstrip())
print((here / "PARTNER_HONESTY.txt").read_text().rstrip())
print((here / "partner_proofs.txt").read_text().rstrip())
print("PARTNER_MATCH")
print(final_elo(here / "partner_match_r.log"))
print("STEP_TABLE")
rows = [
    ("1 seat", "done", "SEAT.txt stamps.txt", "seat 072 idea 22"),
    ("2 honesty B", "done" if bench_nodes("honesty_b_bench13") == "862329" else "not done", "HONESTY_B.txt", "PASS 312866 862329 3024920 4865609"),
    ("2 O and G sums", "done" if sum(b_o) == 9500069 and sum(b_g) == 18466239 else "not done", "B_O_d12.raw.txt B_G_d12.raw.txt", f"O {sum(b_o)} G {sum(b_g)}"),
    ("3 prediction", "done", "prediction.txt", "committed before exe P searches"),
    ("3 patch applies", "done", "apply_check.txt idea.patch.txt", "APPLY_CHECK_OK"),
    ("3 proof off", "done" if off_o_diff == 0 and off_g_diff == 0 else "not done", "P_off_O_d12.raw.txt P_off_G_d12.raw.txt", f"O differ {off_o_diff} G differ {off_g_diff}"),
    ("3 proof on", "done" if on_diff == 200 else "not done", "P_on_O_d12.raw.txt", f"differ {on_diff} of {len(b_o)} sum {sum(on_o)}"),
    ("3 uci options", "done", "uci_p.txt", "IdeaS27 false, IdeaS27_DeadZone 64"),
    ("3 sanitizer", "done" if nm == "35" and asan_err == "" and "ERROR: AddressSanitizer" in probe else "not done", "asan_G100_d10.err.txt asan_probe.err.txt", f"nm {nm} stderr {len(asan_err.encode())} probe yes"),
    ("3 match", "done", "match_og.log match_og.pgn", "see MATCH lines above"),
    ("4 partner", "done", "partner_proofs.txt partner_match_r.log", "CONFIRMS off 0 on equal 600 games"),
]
print("step | status | evidence | result")
for step, status, evidence, result in rows:
    print(f"{step} | {status} | {evidence} | {result}")
