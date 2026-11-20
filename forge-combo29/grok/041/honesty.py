#!/usr/bin/env python3
"""Honesty check: one fresh engine process per line, no setoption.

Usage: honesty.py <exe> <out-dir>
Writes honesty_<name>.txt and honesty_<name>.meta.
"""
import hashlib
import pathlib
import subprocess
import sys

COMMANDS = (
    ("bench11", "bench 11"),
    ("bench13", "bench 13"),
    ("bench16", "bench 16"),
    ("perft5", "go perft 5"),
)


def main() -> None:
    exe = pathlib.Path(sys.argv[1]).resolve()
    out_dir = pathlib.Path(sys.argv[2]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(exe.read_bytes()).hexdigest()
    ident = subprocess.run(
        [str(exe)],
        input="uci\nquit\n",
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    id_name = ""
    for line in ident.stdout.splitlines():
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
            break
    (out_dir / "id_name.txt").write_text(ident.stdout)
    for name, command in COMMANDS:
        proc = subprocess.run(
            [str(exe)],
            input=command + "\nquit\n",
            text=True,
            capture_output=True,
            timeout=300,
            check=False,
        )
        (out_dir / f"honesty_{name}.txt").write_text(proc.stdout)
        if proc.stderr:
            (out_dir / f"honesty_{name}.err").write_text(proc.stderr)
        meta = (
            f"exe={exe}\n"
            f"sha256={sha}\n"
            f"id_name={id_name}\n"
            f"stdin={command}\\nquit\\n\n"
            f"setoption_lines=0\n"
            f"exit={proc.returncode}\n"
        )
        (out_dir / f"honesty_{name}.meta").write_text(meta)
        interesting = [
            line
            for line in proc.stdout.splitlines()
            if line.startswith("info string bench") or line.startswith("nodes ")
        ]
        print(f"{name} exit={proc.returncode}")
        for line in interesting[-3:]:
            print(line)


if __name__ == "__main__":
    main()
