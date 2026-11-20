#!/usr/bin/env python3
"""Honesty of the partner build. Fresh process, no setoption."""
import hashlib, os, select, subprocess, sys
from pathlib import Path
EXE = Path(sys.argv[1])
OUT = Path(sys.argv[2])
CASES = [
    ("bench11", "bench 11", "info string bench", 312866),
    ("bench13", "bench 13", "info string bench", 862329),
    ("bench16", "bench 16", "info string bench", 3024920),
    ("perft5", "go perft 5", "nodes ", 4865609),
]
def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
def run_case(stem, command, marker):
    proc = subprocess.Popen([str(EXE)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0)
    pending = b""
    lines = []
    def send(text):
        proc.stdin.write((text + "\n").encode()); proc.stdin.flush()
    def readline(timeout=180):
        nonlocal pending
        while b"\n" not in pending:
            ready, _, _ = select.select([proc.stdout], [], [], timeout)
            if not ready:
                proc.kill(); raise SystemExit("timeout")
            chunk = os.read(proc.stdout.fileno(), 1 << 16)
            if not chunk:
                proc.kill(); raise SystemExit("closed")
            pending += chunk
        raw, pending = pending.split(b"\n", 1)
        line = raw.decode().rstrip("\r")
        lines.append(line)
        return line
    send("uci")
    while readline(30) != "uciok":
        pass
    send(command)
    hit = None
    while True:
        line = readline()
        if line.startswith(marker):
            hit = line
            break
    send("quit"); proc.wait(timeout=30)
    (OUT / f"partner_h_{stem}.txt").write_text("\n".join(lines) + "\n")
    parts = hit.split()
    return int(parts[parts.index("nodes") + 1])
digest = sha256(EXE)
rows = []
for stem, command, marker, expected in CASES:
    got = run_case(stem, command, marker)
    flag = "ok" if got == expected else "MISS"
    rows.append((command, got, expected, flag))
    print(f"{command} nodes {got} expected {expected} {flag}", flush=True)
(OUT / "partner_HONESTY.txt").write_text(
    f"exe {EXE}\nsha256 {digest}\n" + "\n".join(f"{c} nodes {g} expected {e} {f}" for c, g, e, f in rows) + "\n")
if any(f != "ok" for *_, f in rows):
    sys.exit(1)
