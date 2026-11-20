#!/usr/bin/env python3
"""Honesty check. One fresh engine process per line. No setoption is sent.

Usage: honesty_check.py <exe> <outdir> <tag>
Writes <tag>_bench11.txt and .meta (and bench13, bench16, perft5) plus HONESTY_<tag>.txt.
"""
import hashlib
import select
import subprocess
import sys
from pathlib import Path

EXPECTED = {
    "bench11": ("bench 11", "312866"),
    "bench13": ("bench 13", "862329"),
    "bench16": ("bench 16", "3024920"),
    "perft5": ("go perft 5", "4865609"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def id_name(exe: Path) -> str:
    process = subprocess.Popen(
        [str(exe)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert process.stdin is not None and process.stdout is not None
    process.stdin.write("uci\nquit\n")
    process.stdin.flush()
    name = ""
    try:
        while True:
            ready, _, _ = select.select([process.stdout], [], [], 30)
            if not ready:
                break
            line = process.stdout.readline()
            if line == "":
                break
            if line.startswith("id name "):
                name = line[len("id name ") :].rstrip("\n")
            if line.startswith("uciok"):
                break
    finally:
        process.wait(timeout=10)
    return name


def run_command(exe: Path, command: str) -> list[str]:
    process = subprocess.Popen(
        [str(exe)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert process.stdin is not None and process.stdout is not None
    process.stdin.write(command + "\nquit\n")
    process.stdin.flush()
    lines: list[str] = []
    while True:
        ready, _, _ = select.select([process.stdout], [], [], 180)
        if not ready:
            process.kill()
            raise TimeoutError(f"timeout waiting for {command}")
        line = process.stdout.readline()
        if line == "":
            break
        text = line.rstrip("\n")
        lines.append(text)
        if "unknown option" in text or "invalid value" in text or "invalid FEN" in text or "illegal move" in text:
            process.kill()
            raise RuntimeError(text)
    process.wait(timeout=30)
    return lines


def node_count(lines: list[str], kind: str) -> str | None:
    if kind.startswith("bench"):
        for line in lines:
            marker = " nodes "
            if line.startswith("info string bench depth ") and marker in line:
                tail = line.split(marker, 1)[1]
                return tail.split()[0]
        return None
    for line in reversed(lines):
        if line.startswith("nodes "):
            parts = line.split()
            if len(parts) >= 2:
                return parts[1]
    return None


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: honesty_check.py <exe> <outdir> <tag>", file=sys.stderr)
        return 2
    exe = Path(sys.argv[1]).resolve()
    outdir = Path(sys.argv[2])
    tag = sys.argv[3]
    outdir.mkdir(parents=True, exist_ok=True)
    digest = sha256(exe)
    name = id_name(exe)
    summary = [f"exe {exe}", f"sha256 {digest}", f"id name {name}", "setoption lines: none"]
    ok = True
    for kind, (command, expect) in EXPECTED.items():
        lines = run_command(exe, command)
        got = node_count(lines, kind)
        raw_path = outdir / f"{tag}_{kind}.txt"
        meta_path = outdir / f"{tag}_{kind}.meta"
        raw_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        meta = (
            f"exe {exe}\n"
            f"sha256 {digest}\n"
            f"id name {name}\n"
            f"id name source: separate process of this exe sent only uci; measurement process sent only: {command}\n"
            f"command {command}\n"
            f"setoption lines: none\n"
            f"nodes {got}\n"
            f"expected {expect}\n"
        )
        meta_path.write_text(meta, encoding="utf-8")
        status = "OK" if got == expect else "MISS"
        if status != "OK":
            ok = False
        summary.append(f"{command} -> nodes {got} expected {expect} {status}")
    summary.append("PASS" if ok else "FAIL")
    report = outdir / f"HONESTY_{tag}.txt"
    report.write_text("\n".join(summary) + "\n", encoding="utf-8")
    print("\n".join(summary))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
