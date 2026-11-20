#!/usr/bin/env python3
"""Honesty check. One fresh process per command. No setoption.

Usage: honesty.py <exe> <out_dir> <tag>
Writes <tag>_bench11.txt/.meta, bench13, bench16, perft5.
Prints the node count of each command.
"""
import hashlib
import pathlib
import sys

from engine_io import Session

COMMANDS = (
    ("bench11", "bench 11", "bench"),
    ("bench13", "bench 13", "bench"),
    ("bench16", "bench 16", "bench"),
    ("perft5", "go perft 5", "perft"),
)


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def id_name_of(lines: list[str]) -> str:
    for line in lines:
        if line.startswith("id name "):
            return line[len("id name "):].rstrip("\n")
    return ""


def node_of(lines: list[str], kind: str) -> str:
    if kind == "bench":
        for line in reversed(lines):
            if line.startswith("info string bench "):
                parts = line.split()
                return parts[parts.index("nodes") + 1]
        return ""
    for line in reversed(lines):
        if line.startswith("nodes "):
            return line.split()[1]
    return ""


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit("usage: honesty.py <exe> <out_dir> <tag>")
    exe = str(pathlib.Path(sys.argv[1]).resolve())
    out_dir = pathlib.Path(sys.argv[2])
    tag = sys.argv[3]
    out_dir.mkdir(parents=True, exist_ok=True)
    exe_sha = sha256_file(exe)
    for name, command, kind in COMMANDS:
        session = Session(exe)
        try:
            session.send("uci")
            session.read_until(lambda line: line.strip() == "uciok", 30)
            session.send(command)
            if kind == "bench":
                session.read_until(lambda line: line.startswith("info string bench "), 300)
            else:
                session.read_until(lambda line: line.startswith("nodes "), 180)
        finally:
            session.close()
        raw_path = out_dir / f"{tag}_{name}.txt"
        meta_path = out_dir / f"{tag}_{name}.meta"
        raw_path.write_text("".join(session.lines), encoding="utf-8")
        ident = id_name_of(session.lines)
        nodes = node_of(session.lines, kind)
        meta_path.write_text(
            "\n".join(
                [
                    f"exe={exe}",
                    f"sha256={exe_sha}",
                    f"id_name={ident}",
                    f"command={command}",
                    "options:",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        print(f"{tag} {command} nodes {nodes}")


if __name__ == "__main__":
    main()
