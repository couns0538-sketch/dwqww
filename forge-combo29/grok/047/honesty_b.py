#!/usr/bin/env python3
"""Honesty check for exe B. Fresh process per line. No setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path

EXE = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
TAG = sys.argv[3] if len(sys.argv) > 3 else "b"
OUT.mkdir(parents=True, exist_ok=True)

EXPECTED = {
    "bench11": ("bench 11", 312866),
    "bench13": ("bench 13", 862329),
    "bench16": ("bench 16", 3024920),
    "perft5": ("go perft 5", 4865609),
}

sha = hashlib.sha256(EXE.read_bytes()).hexdigest()
id_proc = subprocess.run(
    [str(EXE)],
    input="uci\nquit\n",
    text=True,
    capture_output=True,
    check=False,
)
id_name = ""
for line in id_proc.stdout.splitlines():
    if line.startswith("id name "):
        id_name = line[len("id name "):]
        break

rows = []
failed = False
for key, (command, expected) in EXPECTED.items():
    proc = subprocess.run(
        [str(EXE)],
        input=command + "\nquit\n",
        text=True,
        capture_output=True,
        check=False,
    )
    raw_path = OUT / f"honesty_{TAG}_{key}.txt"
    raw_path.write_text(proc.stdout)
    err_path = OUT / f"honesty_{TAG}_{key}.err"
    err_path.write_text(proc.stderr)
    meta_path = OUT / f"honesty_{TAG}_{key}.meta"
    meta_path.write_text(
        f"exe={EXE}\nsha256={sha}\nid_name={id_name}\noptions_sent=none\ncommand={command}\n"
    )
    nodes = None
    for line in proc.stdout.splitlines():
        if key.startswith("bench") and line.startswith("info string bench "):
            parts = line.split()
            if "nodes" in parts:
                nodes = int(parts[parts.index("nodes") + 1])
        if key == "perft5" and line.startswith("nodes "):
            nodes = int(line.split()[1])
    ok = nodes == expected
    if not ok:
        failed = True
    rows.append((key, command, nodes, expected, "PASS" if ok else "FAIL"))

summary = OUT / f"HONESTY_{TAG.upper()}.txt"
lines = [
    f"exe={EXE}",
    f"sha256={sha}",
    f"id_name={id_name}",
    "key command nodes expected result",
]
for key, command, nodes, expected, result in rows:
    lines.append(f"{key} {command} {nodes} {expected} {result}")
lines.append("ALL_PASS" if not failed else "ALL_FAIL")
summary.write_text("\n".join(lines) + "\n")
print("\n".join(lines))
sys.exit(0 if not failed else 1)
