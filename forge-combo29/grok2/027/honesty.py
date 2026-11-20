#!/usr/bin/env python3
"""honesty.py EXE OUTDIR TAG
Fresh process per line. No setoption. Raw stdout saved beside a .meta file.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

EXE = Path(sys.argv[1]).resolve()
OUTDIR = Path(sys.argv[2])
TAG = sys.argv[3]
OUTDIR.mkdir(parents=True, exist_ok=True)

COMMANDS = [
    ("bench11", "bench 11\nquit\n"),
    ("bench13", "bench 13\nquit\n"),
    ("bench16", "bench 16\nquit\n"),
    ("perft5", "go perft 5\nquit\n"),
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


exe_sha = sha256(EXE)
for label, script in COMMANDS:
    stdin = "uci\n" + script
    proc = subprocess.run(
        [str(EXE)],
        input=stdin.encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=300,
        check=False,
    )
    text = proc.stdout.decode("utf-8", "replace")
    name = ""
    for line in text.splitlines():
        if line.startswith("id name "):
            name = line
            break
    if not name:
        sys.exit(f"STOP: no id name in {TAG} {label}")
    if "setoption" in stdin:
        sys.exit("STOP: honesty sent a setoption")
    raw = OUTDIR / f"honesty_{TAG}_{label}.txt"
    meta = OUTDIR / f"honesty_{TAG}_{label}.meta"
    raw.write_text(text, encoding="utf-8")
    meta.write_text(
        "\n".join(
            [
                f"exe {EXE}",
                f"sha256 {exe_sha}",
                name,
                "options none",
                "stdin " + stdin.replace("\n", " | "),
                f"returncode {proc.returncode}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"{TAG} {label} rc={proc.returncode} bytes={len(text)}")
