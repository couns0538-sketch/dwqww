#!/usr/bin/env python3
"""Save a fresh engine's uci identity and option list. No setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    exe = Path(sys.argv[1]).resolve()
    out = Path(sys.argv[2])
    proc = subprocess.run([str(exe)], input="uci\nquit\n", text=True, capture_output=True, check=True)
    raw = proc.stdout
    if proc.stderr:
        raw += proc.stderr
    out.write_text(raw)
    id_name = next((line.strip() for line in raw.splitlines() if line.startswith("id name ")), "")
    meta = f"exe {exe}\nsha256 {sha256_file(exe)}\n{id_name}\noptions\ncommand uci\n"
    out.with_suffix(".meta").write_text(meta)
    for line in raw.splitlines():
        if "IdeaS13" in line or line.startswith("id name "):
            print(line)


if __name__ == "__main__":
    main()
