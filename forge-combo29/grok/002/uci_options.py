#!/usr/bin/env python3
"""Save the uci option list. No setoption is sent.

Usage: uci_options.py <exe> <outbase>
"""
import hashlib
import sys
from pathlib import Path

from uci_io import Engine


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: uci_options.py <exe> <outbase>", file=sys.stderr)
        return 2
    exe = Path(sys.argv[1]).resolve()
    outbase = Path(sys.argv[2])
    engine = Engine(exe)
    id_name = ""
    try:
        engine.send("uci")
        lines = engine.read_until(lambda line: line == "uciok", 30)
    finally:
        engine.close()
    for line in lines:
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
    options = [line for line in lines if line.startswith("option name ")]
    Path(str(outbase) + ".txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    Path(str(outbase) + ".meta").write_text(
        f"exe {exe}\nsha256 {sha256(exe)}\nid name {id_name}\nsetoption lines: none\ncommand uci\n",
        encoding="utf-8",
    )
    for wanted in (
        "option name IdeaS28 type check default false",
    ):
        print(("FOUND " if wanted in options else "MISSING ") + wanted)
    return 0


if __name__ == "__main__":
    sys.exit(main())
