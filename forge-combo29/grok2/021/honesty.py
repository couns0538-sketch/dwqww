#!/usr/bin/env python3
"""Honesty check: one fresh engine process per command, no setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path

EXE = {
    "B": "/agent/repos/base/forge-combo29/build/forge",
    "P": "/agent/repos/work/forge-combo29/build/forge",
}
CMDS = [
    ("bench11", "bench 11", "312866"),
    ("bench13", "bench 13", "862329"),
    ("bench16", "bench 16", "3024920"),
    ("perft5", "go perft 5", "4865609"),
]
OUT = Path(__file__).resolve().parent


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_once(exe, command):
    proc = subprocess.run(
        [exe],
        input=command + "\nquit\n",
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    text = proc.stdout
    if proc.stderr:
        text += proc.stderr
    return text, proc.returncode


def id_name(exe):
    text, _ = run_once(exe, "uci")
    for line in text.splitlines():
        if line.startswith("id name "):
            return line[len("id name "):]
    return ""


def main():
    ids = {tag: id_name(path) for tag, path in EXE.items()}
    hashes = {tag: sha256(path) for tag, path in EXE.items()}
    fail = 0
    for tag, path in EXE.items():
        for key, command, expect in CMDS:
            text, rc = run_once(path, command)
            raw = OUT / f"honesty_{tag}_{key}.txt"
            raw.write_text(text, encoding="utf-8")
            meta = OUT / f"honesty_{tag}_{key}.meta"
            meta.write_text(
                "\n".join([
                    f"exe={path}",
                    f"sha256={hashes[tag]}",
                    f"id_name={ids[tag]}",
                    "options=",
                    f"command={command}",
                    f"returncode={rc}",
                    "",
                ]),
                encoding="utf-8",
            )
            nodes = ""
            lines = text.splitlines()
            if command.startswith("go perft"):
                for line in reversed(lines):
                    if line.startswith("nodes "):
                        nodes = line.split()[1]
                        break
            else:
                for line in lines:
                    if " nodes " in line:
                        nodes = line.split(" nodes ", 1)[1].split()[0]
            ok = nodes == expect
            if not ok:
                fail += 1
            print(f"{tag} {command}: nodes {nodes} expect {expect} {'OK' if ok else 'MISS'} rc {rc}")
    return fail


if __name__ == "__main__":
    sys.exit(main())
