#!/usr/bin/env python3
"""honesty.py EXE OUTDIR TAG
Fresh engine process for each line. No setoption.
Writes OUTDIR/honesty_TAG_<job>.txt and a sibling .meta.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

JOBS = (
    ("bench11", "bench 11"),
    ("bench13", "bench 13"),
    ("bench16", "bench 16"),
    ("perft5", "go perft 5"),
)


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
            return line[len("id name ") :]
    return "?"


def main() -> None:
    exe = str(Path(sys.argv[1]).resolve())
    outdir = Path(sys.argv[2])
    tag = sys.argv[3]
    outdir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    name = id_name(exe)
    for job, command in JOBS:
        proc = subprocess.run(
            [exe],
            input=command + "\nquit\n",
            text=True,
            capture_output=True,
            timeout=300,
            check=False,
        )
        text = proc.stdout
        if proc.stderr:
            text += "\n# STDERR\n" + proc.stderr
        raw_path = outdir / f"honesty_{tag}_{job}.txt"
        meta_path = outdir / f"honesty_{tag}_{job}.meta"
        raw_path.write_text(text, encoding="utf-8")
        meta = "\n".join(
            [
                f"exe {exe}",
                f"sha256 {digest}",
                f"id name {name}",
                "options (none)",
                f"stdin {command}",
                "stdin quit",
                f"returncode {proc.returncode}",
            ]
        )
        meta_path.write_text(meta + "\n", encoding="utf-8")
        print(f"WROTE {raw_path}")
        for line in text.splitlines():
            if "nodes" in line:
                print(line)


if __name__ == "__main__":
    main()
