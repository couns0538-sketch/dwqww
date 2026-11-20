#!/usr/bin/env python3
"""Read the raw honesty and O-run files and print the measured numbers."""
import re
from pathlib import Path

OUT = Path(__file__).resolve().parent


def honesty_nodes(path):
    found = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("info string bench ") and " nodes " in line:
            found = int(re.search(r" nodes (\d+)", line).group(1))
        elif line.startswith("nodes "):
            found = int(line.split()[1])
    if found is None:
        raise SystemExit(f"no node line in {path.name}")
    return found


def o_nodes(path):
    last_info = None
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("info "):
            last_info = line
        elif line.startswith("bestmove "):
            match = re.search(r" nodes (\d+)", last_info or "")
            if not match:
                raise SystemExit(f"no nodes before bestmove in {path.name}: {last_info}")
            rows.append(int(match.group(1)))
            last_info = None
    return rows


def meta_lines(path):
    text = path.read_text(encoding="utf-8").splitlines()
    keep = [line for line in text if line.startswith(("exe:", "sha256:", "id_name:", "command:", "options_sent:", "setoption "))]
    return keep


def main():
    expected = {
        "bench11": 312866,
        "bench13": 862329,
        "bench16": 3024920,
        "perft5": 4865609,
    }
    print("honesty")
    for tag in ("B", "P"):
        for stem, want in expected.items():
            path = OUT / f"honesty_{tag}_{stem}.txt"
            got = honesty_nodes(path)
            print(f"{tag} {stem} {got} expected {want} {'ok' if got == want else 'MISS'}")
    print("meta")
    for path in sorted(OUT.glob("honesty_*.meta")) + sorted(OUT.glob("o_*.meta")):
        print(f"-- {path.name}")
        for line in meta_lines(path):
            print(line)
    runs = {label: o_nodes(OUT / f"o_{label}.txt") for label in ("B", "Poff", "Pon")}
    for label, rows in runs.items():
        print(f"o {label} n {len(rows)} sum {sum(rows)} first {rows[0]} {rows[1]} {rows[2]}")
    differ_off = sum(a != b for a, b in zip(runs["B"], runs["Poff"]))
    differ_on = sum(a != b for a, b in zip(runs["B"], runs["Pon"]))
    print(f"Poff positions differing from B: {differ_off}")
    print(f"Pon positions differing from B: {differ_on}")
    print(f"B sum expected 9500069 {'ok' if sum(runs['B']) == 9500069 else 'MISS'}")
    print(f"B first expected 41311 24872 28574 {'ok' if runs['B'][:3] == [41311, 24872, 28574] else 'MISS'}")
    print(f"Pon sum expected 9718009 {'ok' if sum(runs['Pon']) == 9718009 else 'MISS'}")
    print(f"Pon first expected 17283 17878 31115 {'ok' if runs['Pon'][:3] == [17283, 17878, 31115] else 'MISS'}")
    print(f"Pon differ expected 200 {'ok' if differ_on == 200 else 'MISS'}")
    print(f"Poff identical expected 0 {'ok' if differ_off == 0 else 'MISS'}")


if __name__ == "__main__":
    main()
