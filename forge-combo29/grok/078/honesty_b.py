#!/usr/bin/env python3
"""Honesty check on exe B. One fresh process per line. No setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path

EXE = Path("/agent/repos/base/build/forge")
OUT = Path(__file__).resolve().parent

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


def stop_if_bad(line: str) -> None:
    for mark in STOP_MARKS:
        if mark in line:
            raise SystemExit("STOP " + line.strip())


def run_one(name: str, command: str, digest: str) -> str:
    proc = subprocess.Popen(
        [str(EXE)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None
    assert proc.stdout is not None
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
        stop_if_bad(line)
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
        stop_if_bad(line)
        lines.append(line)
        if line.startswith("readyok"):
            break
    send(command)
    while True:
        line = proc.stdout.readline()
        if line == "":
            break
        stop_if_bad(line)
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
    err = proc.stderr.read() if proc.stderr is not None else ""
    text = "".join(lines)
    (OUT / f"honesty_b_{name}.txt").write_text(text)
    if err:
        (OUT / f"honesty_b_{name}.err").write_text(err)
    meta = (
        f"exe: {EXE}\n"
        f"sha256: {digest}\n"
        f"id_name: {id_name}\n"
        "options:\n"
        f"command: {command}\n"
    )
    (OUT / f"honesty_b_{name}.meta").write_text(meta)
    return text


def nodes_of(name: str, text: str) -> str:
    found = ""
    for line in text.splitlines():
        if name.startswith("bench") and line.startswith("info string bench "):
            parts = line.split()
            found = parts[parts.index("nodes") + 1]
        elif name.startswith("perft") and line.startswith("nodes "):
            found = line.split()[1]
    return found


def main() -> int:
    digest = sha256(EXE)
    summary = [f"exe: {EXE}", f"sha256: {digest}"]
    failed = False
    for name, command, expect in COMMANDS:
        text = run_one(name, command, digest)
        got = nodes_of(name, text)
        ok = got == expect
        failed = failed or not ok
        row = f"{command} -> nodes {got} expected {expect} {'OK' if ok else 'FAIL'}"
        summary.append(row)
        print(row, flush=True)
    (OUT / "HONESTY_B.txt").write_text("\n".join(summary) + "\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
