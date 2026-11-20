#!/usr/bin/env python3
"""Honesty check. One fresh process per line. No setoption. Usage: honesty_run.py EXE TAG"""
import hashlib
import pathlib
import subprocess
import sys

EXE = pathlib.Path(sys.argv[1]).resolve()
TAG = sys.argv[2]
OUT = pathlib.Path(__file__).resolve().parent
SHA = hashlib.sha256(EXE.read_bytes()).hexdigest()
CASES = [
    ("bench11", "bench 11", 312866),
    ("bench13", "bench 13", 862329),
    ("bench16", "bench 16", 3024920),
    ("perft5", "go perft 5", 4865609),
]


def run_case(name, command):
    proc = subprocess.run(
        [str(EXE)],
        input=f"uci\n{command}\nquit\n",
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    raw = proc.stdout
    if proc.stderr:
        raw += "\n# stderr\n" + proc.stderr
    (OUT / f"{TAG}_{name}.txt").write_text(raw)
    id_name = ""
    nodes = None
    for line in raw.splitlines():
        if line.startswith("id name ") and not id_name:
            id_name = line[len("id name ") :]
        if "nodes " in line:
            tail = line.split("nodes ", 1)[1].split()[0]
            if tail.isdigit():
                nodes = int(tail)
    (OUT / f"{TAG}_{name}.meta").write_text(
        f"exe={EXE}\nsha256={SHA}\nid_name={id_name}\noptions_sent=none\n"
        f"command={command}\nexit={proc.returncode}\nnodes={nodes}\n"
    )
    return nodes


def main():
    failed = False
    summary = []
    for name, command, expected in CASES:
        nodes = run_case(name, command)
        ok = nodes == expected
        failed = failed or not ok
        line = f"{command} nodes {nodes} expected {expected} {'OK' if ok else 'MISMATCH'}"
        summary.append(line)
        print(line, flush=True)
    (OUT / f"{TAG}.txt").write_text("\n".join(summary) + "\n")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
