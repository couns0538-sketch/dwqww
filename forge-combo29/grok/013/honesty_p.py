#!/usr/bin/env python3
"""Honesty check of exe P. One fresh process per line. No setoption."""
import hashlib, os, select, subprocess, sys
from pathlib import Path
EXE = Path("/agent/repos/work/forge-combo29/build/forge")
OUT = Path("/agent/repos/dwqww/forge-combo29/grok/013")
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
def nodes_of(line):
    parts = line.split()
    return int(parts[parts.index("nodes") + 1])
def run_case(stem, command, marker):
    proc = subprocess.Popen([str(EXE)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0)
    pending = b""
    lines = []
    def send(text):
        proc.stdin.write((text + "\n").encode())
        proc.stdin.flush()
    def readline(timeout=180):
        nonlocal pending
        while b"\n" not in pending:
            ready, _, _ = select.select([proc.stdout], [], [], timeout)
            if not ready:
                proc.kill()
                raise SystemExit("timeout " + stem)
            chunk = os.read(proc.stdout.fileno(), 1 << 16)
            if not chunk:
                proc.kill()
                raise SystemExit("closed " + stem)
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
    send("quit")
    proc.wait(timeout=30)
    (OUT / f"honesty_p_{stem}.txt").write_text("\n".join(lines) + "\n")
    id_name = next(item[len("id name "):] for item in lines if item.startswith("id name "))
    (OUT / f"honesty_p_{stem}.meta").write_text(
        f"exe {EXE}\nsha256 {sha256(EXE)}\nid_name {id_name}\noptions\ncommand {command}\n")
    return nodes_of(hit), id_name
def main():
    digest = sha256(EXE)
    rows = []
    id_name = ""
    for stem, command, marker, expected in CASES:
        got, id_name = run_case(stem, command, marker)
        flag = "ok" if got == expected else "MISS"
        rows.append((command, got, expected, flag))
        print(f"{command} nodes {got} expected {expected} {flag}", flush=True)
    body = [f"exe {EXE}", f"sha256 {digest}", f"id_name {id_name}", "setoption none"]
    for command, got, expected, flag in rows:
        body.append(f"{command} nodes {got} expected {expected} {flag}")
    (OUT / "HONESTY_P.txt").write_text("\n".join(body) + "\n")
    if any(flag != "ok" for *_, flag in rows):
        sys.exit(1)
if __name__ == "__main__":
    main()
