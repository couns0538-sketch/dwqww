#!/usr/bin/env python3
"""Honesty check. One fresh process per line. No setoption.

usage: honesty_exe.py EXE TAG
"""
import hashlib
import pathlib
import subprocess
import sys

CASES = [
    ("bench11", ["uci", "bench 11", "quit"], "312866"),
    ("bench13", ["uci", "bench 13", "quit"], "862329"),
    ("bench16", ["uci", "bench 16", "quit"], "3024920"),
    ("perft5", ["uci", "go perft 5", "quit"], "4865609"),
]


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def id_name(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("id name "):
            return line[len("id name ") :]
    return ""


def main() -> int:
    exe = pathlib.Path(sys.argv[1])
    tag = sys.argv[2]
    out = pathlib.Path(__file__).resolve().parent
    digest = sha256(exe)
    lines = []
    failed = False
    for name, commands, expect in CASES:
        proc = subprocess.run(
            [str(exe)],
            input="\n".join(commands) + "\n",
            text=True,
            capture_output=True,
            timeout=300,
            check=False,
        )
        raw = proc.stdout
        (out / f"honesty_{tag}_{name}.txt").write_text(raw)
        (out / f"honesty_{tag}_{name}.err").write_text(proc.stderr)
        meta = (
            f"exe {exe}\n"
            f"sha256 {digest}\n"
            f"id name {id_name(raw)}\n"
            "options\n"
            "(none)\n"
            "commands\n"
            + "\n".join(commands)
            + "\n"
        )
        (out / f"honesty_{tag}_{name}.meta").write_text(meta)
        got = ""
        for line in raw.splitlines():
            parts = line.replace(":", " ").split()
            if "nodes" in parts:
                got = parts[parts.index("nodes") + 1]
        ok = got == expect and proc.returncode == 0
        if not ok:
            failed = True
        lines.append(f"{name} nodes {got} expect {expect} {'OK' if ok else 'FAIL'}")
        print(lines[-1], flush=True)
    (out / f"HONESTY_{tag}.txt").write_text(
        "\n".join([f"exe {exe}", f"sha256 {digest}", *lines]) + "\n"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
