#!/usr/bin/env python3
"""Honesty check of exe B. One fresh process per line. No setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path

EXE = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
OUT.mkdir(parents=True, exist_ok=True)

CASES = [
    ("bench11", "bench 11\nquit\n", 312866),
    ("bench13", "bench 13\nquit\n", 862329),
    ("bench16", "bench 16\nquit\n", 3024920),
    ("perft5", "go perft 5\nquit\n", 4865609),
]

digest = hashlib.sha256(EXE.read_bytes()).hexdigest()
id_name = ""
proc = subprocess.run(
    [str(EXE)],
    input="uci\nquit\n",
    text=True,
    capture_output=True,
    timeout=60,
)
uci_lines = proc.stdout.splitlines()
for line in uci_lines:
    if line.startswith("id name "):
        id_name = line[len("id name "):]
        break

rows = []
for name, payload, expect in CASES:
    run = subprocess.run(
        [str(EXE)],
        input=payload,
        text=True,
        capture_output=True,
        timeout=300,
    )
    raw = run.stdout
    if run.stderr:
        raw += "\n# stderr\n" + run.stderr
    (OUT / f"honesty_b_{name}.txt").write_text(raw)
    nodes = None
    for line in raw.splitlines():
        if " nodes " in line or line.startswith("nodes "):
            parts = line.split()
            if "nodes" in parts:
                nodes = int(parts[parts.index("nodes") + 1])
    meta = (
        f"exe={EXE}\n"
        f"sha256={digest}\n"
        f"id_name={id_name}\n"
        f"options=\n"
        f"command={payload.strip()}\n"
        f"returncode={run.returncode}\n"
        f"nodes={nodes}\n"
        f"expect={expect}\n"
    )
    (OUT / f"honesty_b_{name}.meta").write_text(meta)
    ok = nodes == expect
    rows.append((name, nodes, expect, ok))
    print(f"{name} nodes={nodes} expect={expect} {'OK' if ok else 'FAIL'}", flush=True)

lines = ["HONESTY_B"]
lines.append(f"exe={EXE}")
lines.append(f"sha256={digest}")
lines.append(f"id_name={id_name}")
all_ok = all(ok for _, _, _, ok in rows)
for name, nodes, expect, ok in rows:
    lines.append(f"{name} nodes={nodes} expect={expect} {'OK' if ok else 'FAIL'}")
lines.append("PASS" if all_ok else "FAIL")
text = "\n".join(lines) + "\n"
(OUT / "HONESTY_B.txt").write_text(text)
print(text, end="")
sys.exit(0 if all_ok else 1)
