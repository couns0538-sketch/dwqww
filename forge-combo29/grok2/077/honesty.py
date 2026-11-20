#!/usr/bin/env python3
"""Honesty check: one fresh engine process per line, no setoption.

Usage: python3 honesty.py <exe> <out-dir> <tag>
Writes <tag>_bench11.txt/.meta, bench13, bench16, perft5.
Prints the parsed node counts. Exits 1 when a known number misses.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

EXPECTED = {
    "bench11": ("bench 11", 312866),
    "bench13": ("bench 13", 862329),
    "bench16": ("bench 16", 3024920),
    "perft5": ("go perft 5", 4865609),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def id_name(exe: str) -> str:
    proc = subprocess.run(
        [exe],
        input="uci\nquit\n",
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    for line in proc.stdout.splitlines():
        if line.startswith("id name "):
            return line
    return "id name MISSING"


def parse_nodes(kind: str, text: str) -> int | None:
    if kind.startswith("bench"):
        for line in text.splitlines():
            if "bench depth" in line and " nodes " in line:
                parts = line.split()
                return int(parts[parts.index("nodes") + 1])
        return None
    last = None
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0] == "nodes":
            last = int(parts[1])
    return last


def main() -> int:
    if len(sys.argv) != 4:
        sys.exit("usage: honesty.py <exe> <out-dir> <tag>")
    exe = str(Path(sys.argv[1]).resolve())
    out_dir = Path(sys.argv[2])
    tag = sys.argv[3]
    out_dir.mkdir(parents=True, exist_ok=True)
    name = id_name(exe)
    digest = sha256_file(Path(exe))
    failed = False
    for key, (command, expected) in EXPECTED.items():
        proc = subprocess.run(
            [exe],
            input=command + "\nquit\n",
            text=True,
            capture_output=True,
            timeout=180,
            check=False,
        )
        raw = proc.stdout
        if proc.stderr:
            raw += proc.stderr
        stem = out_dir / f"{tag}_{key}"
        stem.with_suffix(".txt").write_text(raw, encoding="utf-8")
        nodes = parse_nodes(key, raw)
        meta = [
            f"exe={exe}",
            f"sha256={digest}",
            name,
            "command=" + command,
            "options:",
            "(none; no setoption before this line)",
            f"exit={proc.returncode}",
            f"nodes={nodes}",
            f"expected={expected}",
        ]
        stem.with_suffix(".meta").write_text("\n".join(meta) + "\n", encoding="utf-8")
        status = "ok" if nodes == expected else "MISS"
        if nodes != expected:
            failed = True
        print(f"{tag} {command} nodes {nodes} expected {expected} {status}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
