#!/usr/bin/env python3
"""Honesty check for exe B. One fresh process per line. No setoption."""

import hashlib
import subprocess
import sys
from pathlib import Path

EXE = Path("/agent/repos/base/build/forge")
OUT = Path("/agent/repos/dwqww/forge-combo29/grok/094")

CHECKS = [
    ("bench11", ["bench 11", "quit"], 312866),
    ("bench13", ["bench 13", "quit"], 862329),
    ("bench16", ["bench 16", "quit"], 3024920),
    ("perft5", ["go perft 5", "quit"], 4865609),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(commands: list[str]) -> str:
    completed = subprocess.run(
        [str(EXE)],
        input=("\n".join(commands) + "\n").encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=300,
        check=False,
    )
    return completed.stdout.decode("utf-8", "replace")


def last_nodes(text: str) -> int | None:
    found = None
    for line in text.splitlines():
        parts = line.split()
        if "nodes" not in parts:
            continue
        index = parts.index("nodes")
        if index + 1 < len(parts) and parts[index + 1].isdigit():
            found = int(parts[index + 1])
    return found


def main() -> int:
    digest = sha256(EXE)
    identity = run(["uci", "quit"])
    id_name = ""
    for line in identity.splitlines():
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
            break
    (OUT / "HONESTY_B_id.txt").write_text(identity)
    pieces = []
    failed = False
    for name, commands, expected in CHECKS:
        text = run(commands)
        (OUT / f"HONESTY_B_{name}.txt").write_text(text)
        meta = (
            f"exe {EXE}\n"
            f"sha256 {digest}\n"
            f"id name {id_name}\n"
            f"options\n"
            f"commands {commands[0]}\n"
        )
        (OUT / f"HONESTY_B_{name}.meta").write_text(meta)
        got = last_nodes(text)
        status = "OK" if got == expected else "MISS"
        if got != expected:
            failed = True
        print(f"{name} {status} nodes {got} expected {expected}")
        pieces.append(f"===== {commands[0]} =====\n{text}")
    (OUT / "HONESTY_B.txt").write_text("".join(pieces))
    (OUT / "HONESTY_B.meta").write_text(
        f"exe {EXE}\nsha256 {digest}\nid name {id_name}\noptions\n"
        "commands bench 11; bench 13; bench 16; go perft 5\n"
        "each command is a fresh process with no setoption\n"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
