#!/usr/bin/env python3
"""Save the uci identity and option list of one engine."""
import argparse
import hashlib
import subprocess
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    exe = Path(args.exe)
    proc = subprocess.Popen(
        [str(exe)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None
    proc.stdin.write("uci\n")
    proc.stdin.flush()
    lines = []
    id_name = ""
    while True:
        line = proc.stdout.readline()
        if line == "":
            break
        lines.append(line)
        if line.startswith("id name "):
            id_name = line.strip()
        if line.startswith("uciok"):
            break
    proc.stdin.write("quit\n")
    proc.stdin.flush()
    proc.wait(timeout=20)
    text = "".join(lines)
    out = Path(args.out)
    out.write_text(text)
    Path(str(out) + ".meta").write_text(
        f"exe: {exe}\nsha256: {sha256(exe)}\nid_name: {id_name}\noptions:\ncommand: uci\n"
    )
    wanted = [line.strip() for line in lines if "IdeaB8" in line]
    print("\n".join(wanted))
    return 0


if __name__ == "__main__":
    sys.exit(main())
