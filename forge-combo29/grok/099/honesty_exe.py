#!/usr/bin/env python3
"""Honesty check. One fresh process per line. No setoption.

usage: honesty_exe.py EXE PREFIX
writes PREFIX_bench11.txt and .meta, and PREFIX_HONESTY.txt
"""
import hashlib
import subprocess
import sys
from pathlib import Path

LINES = [
    ("bench11", ["bench", "11"], 312866),
    ("bench13", ["bench", "13"], 862329),
    ("bench16", ["bench", "16"], 3024920),
    ("perft5", ["go", "perft", "5"], 4865609),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def run_line(exe: Path, args: list[str]) -> str:
    script = "uci\n" + " ".join(args) + "\nquit\n"
    proc = subprocess.run(
        [str(exe)],
        input=script,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    return proc.stdout + (proc.stderr or "")


def nodes_of(text: str, kind: str) -> int | None:
    found = None
    for line in text.splitlines():
        if kind.startswith("bench") and line.startswith("info string bench depth "):
            parts = line.split()
            if "nodes" in parts:
                found = int(parts[parts.index("nodes") + 1])
        if kind == "perft5" and line.startswith("nodes "):
            found = int(line.split()[1])
    return found


def main() -> int:
    exe = Path(sys.argv[1])
    prefix = Path(sys.argv[2])
    digest = sha256(exe)
    chunks = []
    ok = True
    for name, args, expected in LINES:
        text = run_line(exe, args)
        raw = Path(str(prefix) + f"_{name}.txt")
        raw.write_text(text)
        ident = ""
        for line in text.splitlines():
            if line.startswith("id name "):
                ident = line[len("id name ") :]
        Path(str(prefix) + f"_{name}.txt.meta").write_text(
            "\n".join(
                [
                    f"exe: {exe}",
                    f"sha256: {digest}",
                    f"id name: {ident}",
                    "options sent:",
                    "(none)",
                    f"commands: uci / {' '.join(args)} / quit",
                    "",
                ]
            )
        )
        got = nodes_of(text, name)
        flag = "OK" if got == expected else "MISS"
        if got != expected:
            ok = False
        chunks.append(f"===== {name} expected {expected} got {got} {flag} =====\n{text}")
        print(f"{name} {got} {flag}", flush=True)
    Path(str(prefix) + "_HONESTY.txt").write_text("\n".join(chunks))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
