#!/usr/bin/env python3
"""Honesty check: a fresh engine process for each line, no setoption.

  python3 honesty.py <exe> <tag> <outdir>

Writes <tag>_bench11.txt, <tag>_bench13.txt, <tag>_bench16.txt, <tag>_perft5.txt
and <tag>.meta. Prints the node count parsed from each raw file.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

STOP = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def run(exe, lines, timeout):
    proc = subprocess.run(
        [exe],
        input="\n".join(lines) + "\n",
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    text = proc.stdout
    if proc.stderr:
        text += proc.stderr
    return proc.returncode, text


def forbid(text, label):
    for phrase in STOP:
        if phrase in text:
            sys.exit(f"STOP {label}: saw {phrase!r}")


def bench_nodes(text):
    for line in text.splitlines():
        if line.startswith("info string bench ") and " nodes " in line:
            return int(line.split(" nodes ", 1)[1].split()[0])
    sys.exit("STOP: no bench nodes line")


def perft_nodes(text):
    last = None
    for line in text.splitlines():
        if line.startswith("nodes "):
            last = int(line.split()[1])
    if last is None:
        sys.exit("STOP: no perft nodes line")
    return last


def main():
    if len(sys.argv) != 4:
        sys.exit("usage: honesty.py <exe> <tag> <outdir>")
    exe = str(Path(sys.argv[1]).resolve())
    tag = sys.argv[2]
    out = Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    code, ident = run(exe, ["uci", "quit"], 60)
    forbid(ident, "uci")
    id_name = next((ln[8:] for ln in ident.splitlines() if ln.startswith("id name ")), "?")
    jobs = [
        ("bench11", ["bench 11", "quit"], 180, bench_nodes),
        ("bench13", ["bench 13", "quit"], 180, bench_nodes),
        ("bench16", ["bench 16", "quit"], 300, bench_nodes),
        ("perft5", ["go perft 5", "quit"], 180, perft_nodes),
    ]
    counts = []
    for name, lines, timeout, parse in jobs:
        code, text = run(exe, lines, timeout)
        forbid(text, name)
        path = out / f"{tag}_{name}.txt"
        path.write_text(text, encoding="utf-8")
        nodes = parse(text)
        counts.append((name, nodes, code))
        print(f"{tag} {name} nodes {nodes} rc {code}")
    meta = out / f"{tag}.meta"
    meta.write_text(
        "\n".join(
            [
                f"exe: {exe}",
                f"sha256: {sha}",
                f"id_name: {id_name}",
                "options:",
                "(none — no setoption)",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (out / f"{tag}_uci.txt").write_text(ident, encoding="utf-8")


if __name__ == "__main__":
    main()
