#!/usr/bin/env python3
"""Record the uci option list of one exe. No setoption is sent."""
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


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: uci_options.py EXE OUT_PREFIX", file=sys.stderr)
        return 2
    exe = Path(sys.argv[1]).resolve()
    prefix = Path(sys.argv[2])
    proc = subprocess.run([str(exe)], input="uci\nquit\n", text=True, capture_output=True, timeout=30)
    text = proc.stdout + proc.stderr
    prefix.parent.mkdir(parents=True, exist_ok=True)
    prefix.with_suffix(".txt").write_text(text)
    id_name = ""
    wanted = []
    for line in text.splitlines():
        if line.startswith("id name "):
            id_name = line[len("id name "):]
        if "IdeaS38_" in line or line.startswith("option name LmrSignedCorrection "):
            wanted.append(line)
    meta = (
        f"exe={exe}\nsha256={sha256_file(exe)}\nid_name={id_name}\noptions:\n"
    )
    Path(str(prefix) + ".meta").write_text(meta)
    print(f"id_name={id_name}")
    for line in wanted:
        print(line)
    missing = [name for name in ("LmrSignedCorrection", "IdeaS38_Divisor", "IdeaS38_Cap") if not any(name in line for line in wanted)]
    if missing:
        print("MISSING " + ",".join(missing))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
