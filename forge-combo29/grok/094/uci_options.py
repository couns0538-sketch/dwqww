#!/usr/bin/env python3
"""Record the uci option lines for IdeaK5 and its spins."""

import argparse
import hashlib
import subprocess
from pathlib import Path

WANTED = ("IdeaK5", "IdeaK5_Divisor", "IdeaK5_Depth")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    exe = Path(args.exe).resolve()
    out = Path(args.out)
    digest = hashlib.sha256(exe.read_bytes()).hexdigest()
    completed = subprocess.run(
        [str(exe)],
        input=b"uci\nquit\n",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
        check=False,
    )
    text = completed.stdout.decode("utf-8", "replace")
    (out / "UCI_OPTIONS.log").write_text(text)
    id_name = ""
    found = []
    for line in text.splitlines():
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
        if line.startswith("option name "):
            parts = line.split()
            if len(parts) >= 3 and parts[2] in WANTED:
                found.append(line)
    (out / "UCI_OPTIONS_IDEA.txt").write_text("\n".join(found) + "\n")
    (out / "UCI_OPTIONS.meta").write_text(
        f"exe {exe}\nsha256 {digest}\nid name {id_name}\noptions\n"
    )
    print(f"id name {id_name}")
    for line in found:
        print(line)
    missing = [name for name in WANTED if not any(f"option name {name} " in line for line in found)]
    if missing:
        print("MISSING " + " ".join(missing))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
