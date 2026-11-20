#!/usr/bin/env python3
"""Honesty check: one fresh engine process per line, no setoption.

Writes HONESTY_<tag>.txt (all raw transcripts) and one .meta beside it.
Also writes HONESTY_<tag>_<name>.txt for each line.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

LINES = [
    ("bench11", "bench 11"),
    ("bench13", "bench 13"),
    ("bench16", "bench 16"),
    ("perft5", "go perft 5"),
]
STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_line(exe: Path, command: str) -> tuple[str, str]:
    proc = subprocess.Popen(
        [str(exe)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None
    proc.stdin.write("uci\n")
    proc.stdin.flush()
    lines: list[str] = []
    id_name = ""
    while True:
        line = proc.stdout.readline()
        if line == "":
            break
        lines.append(line)
        if line.startswith("id name "):
            id_name = line.strip()
        if line.strip() == "uciok":
            break
    proc.stdin.write(command + "\nquit\n")
    proc.stdin.flush()
    rest = proc.stdout.read()
    code = proc.wait(timeout=420)
    raw = "".join(lines) + rest
    if code != 0:
        raise SystemExit(f"engine exit {code} on {command}")
    for mark in STOP_MARKS:
        if mark in raw:
            raise SystemExit(f"STOP {mark} on {command}\n{raw}")
    return raw, id_name


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: honesty.py <exe> <out-dir> <tag>")
    exe = Path(sys.argv[1]).resolve()
    out_dir = Path(sys.argv[2]).resolve()
    tag = sys.argv[3]
    out_dir.mkdir(parents=True, exist_ok=True)
    digest = sha256(exe)
    parts: list[str] = []
    id_name = ""
    for name, command in LINES:
        raw, found = run_line(exe, command)
        if found:
            id_name = found
        (out_dir / f"HONESTY_{tag}_{name}.txt").write_text(raw)
        parts.append(f"===== {command} =====\n{raw}")
        hit = [line for line in raw.splitlines() if "nodes" in line]
        print(name, hit[-1] if hit else "NO NODES LINE")
    combined = "".join(parts)
    (out_dir / f"HONESTY_{tag}.txt").write_text(combined)
    meta = (
        f"exe={exe}\n"
        f"sha256={digest}\n"
        f"id_name={id_name}\n"
        "options_sent=none\n"
        "setoption_before_command=no\n"
        "fresh_process_per_line=yes\n"
    )
    (out_dir / f"HONESTY_{tag}.txt.meta").write_text(meta)
    for name, _command in LINES:
        (out_dir / f"HONESTY_{tag}_{name}.txt.meta").write_text(meta)


if __name__ == "__main__":
    main()
