#!/usr/bin/env python3
"""Honesty check on exe B. One fresh process per line. No setoption."""
import hashlib
import pathlib
import subprocess
import sys

EXE = pathlib.Path("/agent/repos/base/forge-combo29/build/forge")
OUT = pathlib.Path(__file__).resolve().parent
SHA = hashlib.sha256(EXE.read_bytes()).hexdigest()

CASES = [
    ("bench11", "bench 11", 312866),
    ("bench13", "bench 13", 862329),
    ("bench16", "bench 16", 3024920),
    ("perft5", "go perft 5", 4865609),
]


def run_case(name, command):
    script = f"uci\n{command}\nquit\n"
    proc = subprocess.run(
        [str(EXE)],
        input=script,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    raw = proc.stdout
    if proc.stderr:
        raw += "\n# stderr\n" + proc.stderr
    (OUT / f"HONESTY_B_{name}.txt").write_text(raw)
    id_name = ""
    for line in raw.splitlines():
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
            break
    nodes = None
    for line in raw.splitlines():
        if "nodes " in line:
            tail = line.split("nodes ", 1)[1].split()[0]
            if tail.isdigit():
                nodes = int(tail)
    meta = (
        f"exe={EXE}\n"
        f"sha256={SHA}\n"
        f"id_name={id_name}\n"
        f"options_sent=none\n"
        f"command={command}\n"
        f"exit={proc.returncode}\n"
        f"nodes={nodes}\n"
    )
    (OUT / f"HONESTY_B_{name}.meta").write_text(meta)
    return nodes


def main():
    failed = False
    summary = []
    for name, command, expected in CASES:
        nodes = run_case(name, command)
        ok = nodes == expected
        if not ok:
            failed = True
        line = f"{command} nodes {nodes} expected {expected} {'OK' if ok else 'MISMATCH'}"
        summary.append(line)
        print(line, flush=True)
    (OUT / "HONESTY_B.txt").write_text("\n".join(summary) + "\n")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
