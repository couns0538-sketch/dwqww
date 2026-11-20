#!/usr/bin/env python3
"""Honesty check. One fresh engine process per command. No setoption."""

import hashlib
import subprocess
import sys
from pathlib import Path

COMMANDS = (
    ("bench11", "bench 11\nquit\n"),
    ("bench13", "bench 13\nquit\n"),
    ("bench16", "bench 16\nquit\n"),
    ("perft5", "go perft 5\nquit\n"),
    ("uci", "uci\nquit\n"),
)

EXPECTED = {
    "bench11": 312866,
    "bench13": 862329,
    "bench16": 3024920,
    "perft5": 4865609,
}


def nodes_of(name: str, text: str) -> int | None:
    if name.startswith("bench"):
        for line in text.splitlines():
            parts = line.split()
            if "nodes" in parts:
                return int(parts[parts.index("nodes") + 1])
        return None
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0] == "nodes":
            return int(parts[1])
    return None


def id_name(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("id name "):
            return line[len("id name ") :].strip()
    return ""


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: honesty.py <exe> <out-prefix> <label>", file=sys.stderr)
        return 2
    exe = Path(sys.argv[1]).resolve()
    prefix = Path(sys.argv[2])
    label = sys.argv[3]
    digest = hashlib.sha256(exe.read_bytes()).hexdigest()
    prefix.parent.mkdir(parents=True, exist_ok=True)
    failed = False
    summary = [f"label {label}", f"exe {exe}", f"sha256 {digest}"]
    id_line = ""
    for name, command in COMMANDS:
        proc = subprocess.run(
            [str(exe)],
            input=command,
            text=True,
            capture_output=True,
            timeout=180,
            check=False,
        )
        raw_path = prefix.parent / f"{prefix.name}_{name}.txt"
        raw_path.write_text(proc.stdout)
        err_path = prefix.parent / f"{prefix.name}_{name}.err"
        err_path.write_text(proc.stderr)
        if name == "uci":
            id_line = id_name(proc.stdout)
            summary.append(f"id name {id_line}")
            summary.append(f"uci_exit {proc.returncode}")
            continue
        got = nodes_of(name, proc.stdout)
        want = EXPECTED[name]
        ok = got == want and proc.returncode == 0
        if not ok:
            failed = True
        summary.append(f"{name} nodes {got} expected {want} exit {proc.returncode} {'OK' if ok else 'FAIL'}")
    summary.append("options sent: none")
    summary.append("setoption before command: no")
    text = "\n".join(summary) + "\n"
    out = prefix.parent / f"{label}.txt"
    out.write_text(text)
    meta = prefix.parent / f"{label}.meta"
    meta.write_text(
        "\n".join(
            [
                f"exe {exe}",
                f"sha256 {digest}",
                f"id name {id_line}",
                "options sent: none",
                f"summary {out}",
            ]
        )
        + "\n"
    )
    sys.stdout.write(text)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
