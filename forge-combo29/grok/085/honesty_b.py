#!/usr/bin/env python3
"""Honesty check: fresh process per line, no setoption. Writes raw logs, metas, HONESTY_B.txt."""
import hashlib
import subprocess
import sys
from pathlib import Path

EXPECTED = {
    "bench11": 312866,
    "bench13": 862329,
    "bench16": 3024920,
    "perft5": 4865609,
}
COMMANDS = [
    ("bench11", "bench 11"),
    ("bench13", "bench 13"),
    ("bench16", "bench 16"),
    ("perft5", "go perft 5"),
]


def id_name(exe: Path) -> str:
    proc = subprocess.run(
        [str(exe)], input="uci\nquit\n", text=True, capture_output=True, timeout=30, check=False
    )
    for line in proc.stdout.splitlines():
        if line.startswith("id name "):
            return line[len("id name ") :]
    return ""


def last_nodes(text: str) -> int | None:
    found = None
    for line in text.splitlines():
        if "nodes " not in line:
            continue
        tail = line.split("nodes ", 1)[1].split()
        if tail and tail[0].isdigit():
            found = int(tail[0])
    return found


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: honesty_b.py EXE OUTDIR", file=sys.stderr)
        return 2
    exe = Path(sys.argv[1]).resolve()
    outdir = Path(sys.argv[2]).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(exe.read_bytes()).hexdigest()
    name = id_name(exe)
    rows = []
    failed = False
    for stem, command in COMMANDS:
        proc = subprocess.run(
            [str(exe)],
            input=command + "\nquit\n",
            text=True,
            capture_output=True,
            timeout=180,
            check=False,
        )
        text = proc.stdout
        if proc.stderr:
            text += proc.stderr
        raw_path = outdir / f"HONESTY_B_{stem}.txt"
        raw_path.write_text(text)
        meta = (
            f"exe: {exe}\n"
            f"sha256: {sha}\n"
            f"id name: {name}\n"
            f"command: {command}\n"
            "options:\n"
        )
        (outdir / f"HONESTY_B_{stem}.txt.meta").write_text(meta)
        nodes = last_nodes(text)
        expect = EXPECTED[stem]
        ok = nodes == expect
        if not ok:
            failed = True
        rows.append((stem, command, nodes, expect, ok))
        print(f"{stem} nodes {nodes} expected {expect} {'OK' if ok else 'FAIL'}")
    lines = ["honesty exe B", f"exe: {exe}", f"sha256: {sha}", f"id name: {name}", ""]
    for stem, command, nodes, expect, ok in rows:
        lines.append(
            f"{command} -> nodes {nodes} expected {expect} {'OK' if ok else 'FAIL'} raw HONESTY_B_{stem}.txt"
        )
    lines.append("ALL OK" if not failed else "NOT OK")
    (outdir / "HONESTY_B.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
