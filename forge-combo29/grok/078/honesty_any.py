#!/usr/bin/env python3
"""Honesty check. One fresh process per line. No setoption. Paths from argv."""
import hashlib
import subprocess
import sys
from pathlib import Path

COMMANDS = [
    ("bench11", "bench 11", "312866"),
    ("bench13", "bench 13", "862329"),
    ("bench16", "bench 16", "3024920"),
    ("perft5", "go perft 5", "4865609"),
]
STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    exe = Path(sys.argv[1])
    out = Path(sys.argv[2])
    prefix = sys.argv[3]
    digest = sha256(exe)
    summary = [f"exe: {exe}", f"sha256: {digest}"]
    failed = False
    for name, command, expect in COMMANDS:
        proc = subprocess.Popen([str(exe)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        assert proc.stdin is not None and proc.stdout is not None
        lines: list[str] = []
        id_name = ""

        def send(line: str) -> None:
            proc.stdin.write(line + "\n")
            proc.stdin.flush()

        send("uci")
        while True:
            line = proc.stdout.readline()
            if line == "":
                raise SystemExit(f"STOP eof during uci for {name}")
            if any(mark in line for mark in STOP_MARKS):
                raise SystemExit("STOP " + line.strip())
            lines.append(line)
            if line.startswith("id name "):
                id_name = line.strip()
            if line.startswith("uciok"):
                break
        send("isready")
        while True:
            line = proc.stdout.readline()
            if line == "":
                raise SystemExit(f"STOP eof during isready for {name}")
            if any(mark in line for mark in STOP_MARKS):
                raise SystemExit("STOP " + line.strip())
            lines.append(line)
            if line.startswith("readyok"):
                break
        send(command)
        while True:
            line = proc.stdout.readline()
            if line == "":
                break
            if any(mark in line for mark in STOP_MARKS):
                raise SystemExit("STOP " + line.strip())
            lines.append(line)
            if name.startswith("bench") and line.startswith("info string bench "):
                break
            if name.startswith("perft") and line.startswith("nodes "):
                break
        send("quit")
        try:
            proc.wait(timeout=180)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=10)
        text = "".join(lines)
        (out / f"{prefix}_{name}.txt").write_text(text)
        (out / f"{prefix}_{name}.meta").write_text(
            f"exe: {exe}\nsha256: {digest}\nid_name: {id_name}\noptions:\ncommand: {command}\n"
        )
        got = ""
        for line in text.splitlines():
            if name.startswith("bench") and line.startswith("info string bench "):
                parts = line.split()
                got = parts[parts.index("nodes") + 1]
            elif name.startswith("perft") and line.startswith("nodes "):
                got = line.split()[1]
        ok = got == expect
        failed = failed or not ok
        row = f"{command} -> nodes {got} expected {expect} {'OK' if ok else 'FAIL'}"
        summary.append(row)
        print(row, flush=True)
    (out / f"{prefix}.txt").write_text("\n".join(summary) + "\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
