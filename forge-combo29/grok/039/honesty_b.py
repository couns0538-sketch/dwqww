#!/usr/bin/env python3
"""Honesty check for one engine. Fresh process per line. No setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path

EXE = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
PREFIX = sys.argv[3] if len(sys.argv) > 3 else ""
SUMMARY = sys.argv[4] if len(sys.argv) > 4 else "HONESTY_B.txt"
OUT.mkdir(parents=True, exist_ok=True)

EXPECTED = {
    "bench11": 312866,
    "bench13": 862329,
    "bench16": 3024920,
    "perft5": 4865609,
}
COMMANDS = {
    "bench11": "bench 11",
    "bench13": "bench 13",
    "bench16": "bench 16",
    "perft5": "go perft 5",
}

sha = hashlib.sha256(EXE.read_bytes()).hexdigest()
id_name = ""
uci = subprocess.run([str(EXE)], input="uci\nquit\n", text=True, capture_output=True, timeout=60)
for line in uci.stdout.splitlines():
    if line.startswith("id name "):
        id_name = line[len("id name "):]
        break

def nodes_of(text, kind):
    if kind.startswith("bench"):
        for line in text.splitlines():
            if "nodes " in line and line.startswith("info string bench"):
                parts = line.split()
                return int(parts[parts.index("nodes") + 1])
        return None
    last = None
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] == "nodes" and parts[1].isdigit():
            last = int(parts[1])
    return last

summary = []
ok = True
for kind, cmd in COMMANDS.items():
    proc = subprocess.run([str(EXE)], input=cmd + "\nquit\n", text=True, capture_output=True, timeout=180)
    raw = proc.stdout
    if proc.stderr:
        raw += "\n# stderr\n" + proc.stderr
    (OUT / f"{PREFIX}{kind}.txt").write_text(raw)
    got = nodes_of(proc.stdout, kind)
    meta = (
        f"exe={EXE}\n"
        f"sha256={sha}\n"
        f"id_name={id_name}\n"
        f"options=\n"
        f"command={cmd}\n"
        f"nodes={got}\n"
        f"returncode={proc.returncode}\n"
    )
    (OUT / f"{PREFIX}{kind}.meta").write_text(meta)
    exp = EXPECTED[kind]
    flag = "OK" if got == exp else "MISS"
    if got != exp:
        ok = False
    summary.append(f"{kind} nodes {got} expected {exp} {flag}")

text = "\n".join(summary) + ("\nPASS\n" if ok else "\nFAIL\n")
(OUT / SUMMARY).write_text(text)
print(text, end="")
sys.exit(0 if ok else 1)
