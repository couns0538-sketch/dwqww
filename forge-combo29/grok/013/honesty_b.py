#!/usr/bin/env python3
"""Honesty check: one fresh engine process per line, no setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path

EXE = Path("/agent/repos/base/forge-combo29/build/forge")
OUT = Path("/agent/repos/dwqww/forge-combo29/grok/013")
CASES = [
    ("bench11", "bench 11", "info string bench", 312866),
    ("bench13", "bench 13", "info string bench", 862329),
    ("bench16", "bench 16", "info string bench", 3024920),
    ("perft5", "go perft 5", "nodes ", 4865609),
]

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def nodes_of(line: str) -> int:
    parts = line.split()
    if "nodes" not in parts:
        raise SystemExit(f"no nodes in {line!r}")
    return int(parts[parts.index("nodes") + 1])

def run_case(stem: str, command: str, marker: str) -> tuple[int, str]:
    proc = subprocess.Popen(
        [str(EXE)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None
    lines: list[str] = []

    def send(text: str) -> None:
        proc.stdin.write(text + "\n")
        proc.stdin.flush()

    def read_until(pred) -> str:
        while True:
            raw = proc.stdout.readline()
            if raw == "":
                proc.kill()
                raise SystemExit(f"{stem}: engine closed before {command}")
            line = raw.rstrip("\r\n")
            lines.append(line)
            if "unknown option" in line or "invalid value" in line or "invalid FEN" in line or "illegal move" in line:
                proc.kill()
                raise SystemExit(f"{stem}: stopped on {line}")
            if pred(line):
                return line

    send("uci")
    read_until(lambda line: line == "uciok")
    send(command)
    hit = read_until(lambda line: line.startswith(marker))
    send("quit")
    proc.stdin.close()
    rest = proc.stdout.read()
    if rest:
        lines.extend(rest.splitlines())
    code = proc.wait(timeout=180)
    raw_path = OUT / f"honesty_b_{stem}.txt"
    raw_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    id_name = next((line[len("id name "):] for line in lines if line.startswith("id name ")), "")
    meta = OUT / f"honesty_b_{stem}.meta"
    meta.write_text(
        "\n".join([
            f"exe {EXE}",
            f"sha256 {sha256(EXE)}",
            f"id_name {id_name}",
            "options",
            f"command {command}",
            f"exit {code}",
        ]) + "\n",
        encoding="utf-8",
    )
    return nodes_of(hit), id_name

def main() -> None:
    digest = sha256(EXE)
    rows = []
    id_name = ""
    for stem, command, marker, expected in CASES:
        got, id_name = run_case(stem, command, marker)
        rows.append((command, got, expected, "ok" if got == expected else "MISS"))
        print(f"{command} nodes {got} expected {expected} {'ok' if got == expected else 'MISS'}", flush=True)
    body = [f"exe {EXE}", f"sha256 {digest}", f"id_name {id_name}", "setoption none"]
    for command, got, expected, flag in rows:
        body.append(f"{command} nodes {got} expected {expected} {flag}")
    (OUT / "HONESTY_B.txt").write_text("\n".join(body) + "\n", encoding="utf-8")
    if any(flag != "ok" for *_, flag in rows):
        sys.exit(1)

if __name__ == "__main__":
    main()
