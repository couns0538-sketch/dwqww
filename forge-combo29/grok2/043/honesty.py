#!/usr/bin/env python3
"""honesty.py EXE OUTDIR TAG

A fresh engine process for each line. No setoption is sent before the measured
command. After the command, uci is sent only so the .meta file can record id name
from the same process.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

COMMANDS = (
    ("bench11", "bench 11"),
    ("bench13", "bench 13"),
    ("bench16", "bench 16"),
    ("perft5", "go perft 5"),
)


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    if len(sys.argv) != 4:
        sys.exit("usage: honesty.py EXE OUTDIR TAG")
    exe = str(Path(sys.argv[1]).resolve())
    outdir = Path(sys.argv[2])
    tag = sys.argv[3]
    outdir.mkdir(parents=True, exist_ok=True)
    exe_sha = sha256_file(exe)
    for name, command in COMMANDS:
        proc = subprocess.run(
            [exe],
            input=command + "\nuci\nquit\n",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=300,
            check=False,
        )
        raw_path = outdir / f"{tag}_{name}.txt"
        meta_path = outdir / f"{tag}_{name}.meta"
        raw_path.write_text(proc.stdout, encoding="utf-8")
        if proc.stderr:
            (outdir / f"{tag}_{name}.err").write_text(proc.stderr, encoding="utf-8")
        id_name = ""
        for line in proc.stdout.splitlines():
            if line.startswith("id name "):
                id_name = line
                break
        meta_path.write_text(
            "\n".join(
                [
                    f"exe: {exe}",
                    f"sha256: {exe_sha}",
                    f"id name: {id_name}",
                    "options:",
                    "(none)",
                    f"command: {command}",
                    f"returncode: {proc.returncode}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        signature = [
            line
            for line in proc.stdout.splitlines()
            if line.startswith("info string bench ") or line.startswith("nodes ")
        ]
        print(f"{tag} {name} rc={proc.returncode} {signature[-1] if signature else 'NO SIGNATURE'}")


if __name__ == "__main__":
    main()
