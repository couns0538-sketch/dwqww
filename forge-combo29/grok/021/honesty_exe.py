#!/usr/bin/env python3
"""Honesty check: one fresh process per line, uci then the command, no setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path

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


def run_case(exe: Path, command: str) -> tuple[str, str, int]:
    process = subprocess.Popen(
        [str(exe)],
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

    send("uci")
    id_name = ""
    while True:
        line = process.stdout.readline()
        if line == "":
            raise RuntimeError("eof during uci")
        lines.append(line)
        if line.startswith("id name "):
            id_name = line[len("id name ") :].rstrip("\r\n")
        if "unknown option" in line or "invalid value" in line:
            raise RuntimeError(line.rstrip("\n"))
        if line.startswith("uciok"):
            break
    send(command)
    nodes = None
    while True:
        line = process.stdout.readline()
        if line == "":
            break
        lines.append(line)
        if line.startswith("info string bench "):
            parts = line.split()
            nodes = int(parts[parts.index("nodes") + 1])
            break
        if line.startswith("nodes "):
            nodes = int(line.split()[1])
            break
    send("quit")
    process.stdin.close()
    rest = process.stdout.read()
    if rest:
        lines.append(rest if rest.endswith("\n") else rest + "\n")
    process.wait(timeout=180)
    if nodes is None:
        raise RuntimeError(f"no nodes for {command}")
    return id_name, "".join(lines), nodes


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: honesty_exe.py EXE TAG", file=sys.stderr)
        return 2
    exe = Path(sys.argv[1]).resolve()
    tag = sys.argv[2]
    out_dir = Path(__file__).resolve().parent
    digest = sha256(exe)
    summary = []
    failed = False
    id_name = ""
    for command, expected in EXPECTED.items():
        slug = command.replace(" ", "_")
        id_name, raw, nodes = run_case(exe, command)
        (out_dir / f"{tag}_{slug}.out").write_text(raw)
        (out_dir / f"{tag}_{slug}.meta").write_text(
            f"exe={exe}\nsha256={digest}\nid_name={id_name}\noptions:\n"
        )
        status = "OK" if nodes == expected else "MISMATCH"
        if status != "OK":
            failed = True
        summary.append(f"{command} nodes {nodes} expected {expected} {status}")
        print(summary[-1], flush=True)
    (out_dir / f"{tag}.txt").write_text("\n".join(summary) + "\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
