#!/usr/bin/env python3
"""Honesty check. Fresh engine process per command. No setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
EXES = {
    "B": Path("/agent/repos/base/build/forge"),
    "P": Path("/agent/repos/work/build/forge"),
}
CHECKS = [
    ("bench11", "bench 11", 312866, "bench"),
    ("bench13", "bench 13", 862329, "bench"),
    ("bench16", "bench 16", 3024920, "bench"),
    ("perft5", "go perft 5", 4865609, "perft"),
]


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
    return "MISSING"


def nodes_of(text: str, kind: str):
    if kind == "bench":
        for line in text.splitlines():
            if "bench depth" in line and " nodes " in line:
                parts = line.split()
                return int(parts[parts.index("nodes") + 1]), line
        return None, ""
    last = None
    last_line = ""
    for line in text.splitlines():
        if line.startswith("nodes "):
            last = int(line.split()[1])
            last_line = line
    return last, last_line


def main() -> int:
    ids = {tag: id_name(exe) for tag, exe in EXES.items()}
    hashes = {tag: sha256(exe) for tag, exe in EXES.items()}
    fail = 0
    for tag, exe in EXES.items():
        for name, cmd, expect, kind in CHECKS:
            proc = subprocess.run(
                [str(exe)],
                input=cmd + "\nquit\n",
                text=True,
                capture_output=True,
                timeout=180,
            )
            raw = OUT / f"honesty_{tag}_{name}.txt"
            raw.write_text(proc.stdout, encoding="utf-8")
            if proc.stderr:
                (OUT / f"honesty_{tag}_{name}.err").write_text(proc.stderr, encoding="utf-8")
            got, line = nodes_of(proc.stdout, kind)
            meta = OUT / f"honesty_{tag}_{name}.meta"
            meta.write_text(
                "\n".join(
                    [
                        f"exe {exe}",
                        f"sha256 {hashes[tag]}",
                        f"id name {ids[tag]}",
                        "options none",
                        f"command {cmd}",
                        f"returncode {proc.returncode}",
                        f"nodes {got}",
                        f"expect {expect}",
                        f"line {line}",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            ok = got == expect
            if not ok:
                fail += 1
            print(f"{tag} {cmd}: nodes {got} expect {expect} {'OK' if ok else 'MISS'} rc {proc.returncode}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
