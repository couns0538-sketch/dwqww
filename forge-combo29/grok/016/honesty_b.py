#!/usr/bin/env python3
"""Honesty check on one engine. One fresh process per command. No setoption."""
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_one(exe: Path, command: str) -> tuple[str, str]:
    proc = subprocess.Popen(
        [str(exe)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert proc.stdin is not None
    assert proc.stdout is not None
    proc.stdin.write("uci\n")
    proc.stdin.flush()
    lines: list[str] = []
    id_name = ""
    while True:
        line = proc.stdout.readline()
        if line == "":
            break
        lines.append(line)
        if line.startswith("id name "):
            id_name = line.strip()
        if line.strip() == "uciok":
            break
    proc.stdin.write(command + "\nquit\n")
    proc.stdin.flush()
    rest = proc.stdout.read()
    code = proc.wait()
    if code != 0:
        raise SystemExit(f"{command} exit {code}")
    return id_name, "".join(lines) + rest


def node_count(raw: str, command: str) -> int:
    if command.startswith("bench"):
        for line in raw.splitlines():
            if "bench depth" in line and " nodes " in line:
                parts = line.split()
                return int(parts[parts.index("nodes") + 1])
        raise SystemExit(f"no bench nodes in output for {command}")
    last = None
    for line in raw.splitlines():
        if line.startswith("nodes "):
            last = int(line.split()[1])
    if last is None:
        raise SystemExit(f"no perft nodes in output for {command}")
    return last


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: honesty_b.py EXE OUTDIR")
    exe = Path(sys.argv[1]).resolve()
    out_dir = Path(sys.argv[2]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    digest = sha256_file(exe)
    summary = [f"exe {exe}", f"sha256 {digest}"]
    failed = False
    for command, expected in EXPECTED.items():
        tag = command.replace(" ", "_")
        id_name, raw = run_one(exe, command)
        nodes = node_count(raw, command)
        status = "OK" if nodes == expected else "MISMATCH"
        if nodes != expected:
            failed = True
        (out_dir / f"honesty_B_{tag}.txt").write_text(raw)
        meta = (
            f"exe {exe}\n"
            f"sha256 {digest}\n"
            f"{id_name}\n"
            f"options\n"
            f"command {command}\n"
        )
        (out_dir / f"honesty_B_{tag}.meta").write_text(meta)
        summary.append(f"{command} nodes {nodes} expected {expected} {status}")
        print(summary[-1], flush=True)
    text = "\n".join(summary) + "\n"
    (out_dir / "HONESTY_B.txt").write_text(text)
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
