#!/usr/bin/env python3
"""Save the uci option list. No setoption."""
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
    if len(sys.argv) != 3:
        print("usage: uci_options.py EXE OUT", file=sys.stderr)
        return 2
    exe = Path(sys.argv[1]).resolve()
    out = Path(sys.argv[2])
    proc = subprocess.run([str(exe)], input="uci\nquit\n", text=True, capture_output=True, timeout=60)
    text = proc.stdout
    if proc.stderr:
        text += proc.stderr
    out.write_text(text)
    id_name = ""
    for line in proc.stdout.splitlines():
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
        if "IdeaS33" in line or line.startswith("id name"):
            print(line)
    out.with_suffix(".meta").write_text(
        f"exe {exe}\nsha256 {sha256(exe)}\nid_name {id_name}\noptions\ncommands\nuci\nquit\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
