#!/usr/bin/env python3
"""Honesty check of exe B. One fresh process per line. No setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path

EXE = Path("/agent/repos/base/forge-combo29/build/forge").resolve()
OUT_DIR = Path(__file__).resolve().parent
EXPECTED = {
    "bench 11": 312866,
    "bench 13": 862329,
    "bench 16": 3024920,
    "go perft 5": 4865609,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_case(command: str) -> tuple[str, str, list[str]]:
    process = subprocess.Popen(
        [str(EXE)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert process.stdin is not None and process.stdout is not None
    lines: list[str] = []

    def send(text: str) -> None:
        process.stdin.write(text + "\n")
        process.stdin.flush()

    def read_until(prefix: str) -> None:
        while True:
            line = process.stdout.readline()
            if line == "":
                raise RuntimeError(f"eof before {prefix!r} during {command}")
            lines.append(line)
            if "unknown option" in line or "invalid value" in line or "invalid FEN" in line or "illegal move" in line:
                raise RuntimeError(line.rstrip("\n"))
            if line.startswith(prefix):
                return

    send("uci")
    id_name = ""
    while True:
        line = process.stdout.readline()
        if line == "":
            raise RuntimeError("eof during uci")
        lines.append(line)
        if line.startswith("id name "):
            id_name = line[len("id name ") :].rstrip("\r\n")
        if line.startswith("uciok"):
            break
    send(command)
    if command.startswith("bench"):
        read_until("info string bench ")
    else:
        read_until("nodes ")
    send("quit")
    process.stdin.close()
    rest = process.stdout.read()
    if rest:
        lines.append(rest if rest.endswith("\n") else rest + "\n")
    code = process.wait(timeout=180)
    if code != 0:
        raise RuntimeError(f"{command} exit {code}")
    return id_name, "".join(lines), lines


def parse_nodes(command: str, lines: list[str]) -> int:
    if command.startswith("bench"):
        for line in lines:
            if line.startswith("info string bench "):
                parts = line.split()
                return int(parts[parts.index("nodes") + 1])
        raise RuntimeError("no bench line")
    for line in reversed(lines):
        if line.startswith("nodes "):
            return int(line.split()[1])
    raise RuntimeError("no perft nodes")


def main() -> int:
    digest = sha256(EXE)
    summary: list[str] = []
    failed = False
    for command, expected in EXPECTED.items():
        slug = command.replace(" ", "_")
        id_name, raw, lines = run_case(command)
        nodes = parse_nodes(command, lines)
        raw_path = OUT_DIR / f"honesty_b_{slug}.out"
        meta_path = OUT_DIR / f"honesty_b_{slug}.meta"
        raw_path.write_text(raw)
        meta_path.write_text(
            f"exe={EXE}\nsha256={digest}\nid_name={id_name}\noptions:\n"
        )
        status = "OK" if nodes == expected else "MISMATCH"
        if status != "OK":
            failed = True
        summary.append(f"{command} nodes {nodes} expected {expected} {status}")
        print(summary[-1], flush=True)
    text = "\n".join(summary) + "\n"
    (OUT_DIR / "HONESTY_B.txt").write_text(text)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
