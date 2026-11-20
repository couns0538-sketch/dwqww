#!/usr/bin/env python3
"""Honesty check: one fresh process per command, no setoption. Writes raw stdout and a .meta."""
import hashlib
import subprocess
import sys
from pathlib import Path

COMMANDS = [
    ("bench11", "bench 11", 312866),
    ("bench13", "bench 13", 862329),
    ("bench16", "bench 16", 3024920),
    ("perft5", "go perft 5", 4865609),
]

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def id_name(exe: Path) -> str:
    proc = subprocess.run(
        [str(exe)],
        input="uci\nquit\n",
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    for line in proc.stdout.splitlines():
        if line.startswith("id name "):
            return line[len("id name ") :]
    return "MISSING"


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit("usage: honesty.py <exe> <tag> <outdir>")
    exe = Path(sys.argv[1]).resolve()
    tag = sys.argv[2]
    out = Path(sys.argv[3]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    digest = sha256(exe)
    name = id_name(exe)
    fails = []
    for stem, command, expected in COMMANDS:
        proc = subprocess.run(
            [str(exe)],
            input=command + "\nquit\n",
            text=True,
            capture_output=True,
            timeout=180,
            check=False,
        )
        raw_path = out / f"honesty_{tag}_{stem}.txt"
        raw_path.write_text(proc.stdout, encoding="utf-8")
        meta = out / f"honesty_{tag}_{stem}.meta"
        meta.write_text(
            "\n".join(
                [
                    f"exe={exe}",
                    f"sha256={digest}",
                    f"id_name={name}",
                    "id_name_source=separate uci query of this same exe; measured process sent only the command and quit",
                    f"command={command}",
                    "options=",
                    f"returncode={proc.returncode}",
                    f"stderr={proc.stderr.strip()}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        nodes = None
        for line in proc.stdout.splitlines():
            if any(bad in line for bad in BAD):
                fails.append(f"{stem} STOP {line}")
            parts = line.split()
            if "nodes" in parts:
                try:
                    nodes = int(parts[parts.index("nodes") + 1])
                except (ValueError, IndexError):
                    nodes = None
        status = "ok" if nodes == expected else "MISS"
        if nodes != expected:
            fails.append(f"{stem} nodes {nodes} expected {expected}")
        print(f"{tag} {command} nodes {nodes} expected {expected} {status}")
    if fails:
        print("HONESTY MISS")
        for item in fails:
            print(item)
        sys.exit(1)
    print(f"{tag} HONESTY OK")


if __name__ == "__main__":
    main()
