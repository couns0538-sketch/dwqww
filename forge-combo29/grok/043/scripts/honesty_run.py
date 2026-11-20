#!/usr/bin/env python3
"""Fresh-process honesty checks. No setoption is sent before the measured command."""
import hashlib
import subprocess
import sys
from pathlib import Path

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def run_one(exe: Path, command: str, out_path: Path) -> None:
    digest = sha256(exe)
    proc = subprocess.Popen(
        [str(exe)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None
    # Measured command first. Nothing, including setoption, is sent before it.
    proc.stdin.write(command + "\n")
    proc.stdin.flush()
    lines = []
    seen = False
    while True:
        line = proc.stdout.readline()
        if line == "":
            break
        lines.append(line)
        if "nodes " in line and ("bench depth" in line or line.startswith("nodes ")):
            seen = True
            break
    # id name from the same process, after the measurement.
    proc.stdin.write("uci\nquit\n")
    proc.stdin.flush()
    id_name = ""
    while True:
        line = proc.stdout.readline()
        if line == "":
            break
        lines.append(line)
        if line.startswith("id name "):
            id_name = line[len("id name "):].rstrip("\r\n")
    proc.wait(timeout=30)
    out_path.write_text("".join(lines))
    meta = out_path.with_suffix(out_path.suffix + ".meta")
    meta.write_text(
        "exe=" + str(exe.resolve()) + "\n"
        "sha256=" + digest + "\n"
        "id_name=" + id_name + "\n"
        "options_sent=\n"
        "command=" + command + "\n"
        "saw_nodes_line=" + ("yes" if seen else "no") + "\n"
    )

def main() -> int:
    if len(sys.argv) != 3:
        print("usage: honesty_run.py EXE OUTDIR", file=sys.stderr)
        return 2
    exe = Path(sys.argv[1])
    outdir = Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    jobs = [
        ("bench 11", "bench11.txt"),
        ("bench 13", "bench13.txt"),
        ("bench 16", "bench16.txt"),
        ("go perft 5", "perft5.txt"),
    ]
    for command, name in jobs:
        print("RUN", command, flush=True)
        run_one(exe, command, outdir / name)
        text = (outdir / name).read_text()
        for line in text.splitlines():
            if "nodes " in line and ("bench depth" in line or line.startswith("nodes ")):
                print(line)
                break
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
