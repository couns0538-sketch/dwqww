#!/usr/bin/env python3
"""Honesty check: one fresh engine process per line, no setoption.

Usage: honesty_run.py <exe> <out-dir> <tag>
Writes HONESTY_<tag>.txt plus one raw file and one .meta per command.
"""
import hashlib
import subprocess
import sys
from pathlib import Path


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
    )
    for line in proc.stdout.splitlines():
        if line.startswith("id name "):
            return line[len("id name ") :]
    return ""


def main() -> int:
    exe = Path(sys.argv[1]).resolve()
    out = Path(sys.argv[2]).resolve()
    tag = sys.argv[3]
    out.mkdir(parents=True, exist_ok=True)
    digest = sha256(exe)
    name = id_name(exe)
    commands = [
        ("bench11", "bench 11"),
        ("bench13", "bench 13"),
        ("bench16", "bench 16"),
        ("perft5", "go perft 5"),
    ]
    combined = []
    for key, command in commands:
        proc = subprocess.run(
            [str(exe)],
            input=command + "\nquit\n",
            text=True,
            capture_output=True,
            timeout=300,
        )
        text = proc.stdout
        if proc.stderr:
            text += "\n# stderr\n" + proc.stderr
        raw = out / f"honesty_{tag}_{key}.txt"
        raw.write_text(text)
        meta = out / f"honesty_{tag}_{key}.meta"
        meta.write_text(
            "\n".join(
                [
                    f"exe {exe}",
                    f"sha256 {digest}",
                    f"id_name {name}",
                    "options",
                    f"command {command}",
                    f"exit {proc.returncode}",
                    "",
                ]
            )
        )
        combined.append(f"===== {command} exit {proc.returncode} =====")
        combined.append(text.rstrip("\n"))
        print(key, "exit", proc.returncode, flush=True)
    (out / f"HONESTY_{tag}.txt").write_text("\n".join(combined) + "\n")
    (out / f"HONESTY_{tag}.meta").write_text(
        "\n".join(
            [
                f"exe {exe}",
                f"sha256 {digest}",
                f"id_name {name}",
                "options",
                "commands bench 11 | bench 13 | bench 16 | go perft 5",
                "fresh_process each",
                "setoption none",
                "",
            ]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
