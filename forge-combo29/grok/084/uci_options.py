#!/usr/bin/env python3
"""Save the uci option list. Usage: uci_options.py EXE OUT_PREFIX"""
import hashlib
import subprocess
import sys
from pathlib import Path

WANTED = ("option name IdeaA3 ", "option name IdeaA3_Threshold ", "option name IdeaA3_Extension ")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    exe = Path(sys.argv[1]).resolve()
    prefix = Path(sys.argv[2]).resolve()
    proc = subprocess.run(
        [str(exe)],
        input="uci\nquit\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
        check=False,
    )
    text = proc.stdout
    Path(str(prefix) + ".txt").write_text(text)
    id_name = ""
    found = []
    for line in text.splitlines():
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
        for wanted in WANTED:
            if line.startswith(wanted):
                found.append(line)
    Path(str(prefix) + ".meta").write_text(
        f"exe: {exe}\nsha256: {sha256(exe)}\nid name: {id_name}\noptions:\n"
    )
    print(f"id name: {id_name}")
    for line in found:
        print(line)
    missing = [name for name in WANTED if not any(line.startswith(name) for line in found)]
    if missing:
        print("MISSING " + " ".join(missing))
        raise SystemExit(1)
    if "option name IdeaA3 type check default false" not in text:
        raise SystemExit("IdeaA3 default is not false")
    if "option name IdeaA3_Threshold type spin default 0 " not in text:
        raise SystemExit("IdeaA3_Threshold default is not 0")
    if "option name IdeaA3_Extension type spin default 1 " not in text:
        raise SystemExit("IdeaA3_Extension default is not 1")
    print("defaults ok")


if __name__ == "__main__":
    main()
