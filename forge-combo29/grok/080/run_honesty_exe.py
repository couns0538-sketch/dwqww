#!/usr/bin/env python3
"""Honesty check. One fresh process per line. No setoption.

usage: run_honesty_exe.py EXE OUT_PREFIX
"""
import hashlib
import pathlib
import subprocess
import sys

CASES = [
    ("bench11", ["uci", "isready", "bench 11", "quit"], "312866"),
    ("bench13", ["uci", "isready", "bench 13", "quit"], "862329"),
    ("bench16", ["uci", "isready", "bench 16", "quit"], "3024920"),
    ("perft5", ["uci", "isready", "go perft 5", "quit"], "4865609"),
]
STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: run_honesty_exe.py EXE OUT_PREFIX")
    exe = pathlib.Path(sys.argv[1])
    prefix = pathlib.Path(sys.argv[2])
    if not exe.is_file():
        raise SystemExit(f"missing exe {exe}")
    digest = sha256(exe)
    id_name = ""
    lines = [f"exe={exe}", f"sha256={digest}"]
    expected = {name: want for name, _commands, want in CASES}
    for name, commands, _want in CASES:
        proc = subprocess.run(
            [str(exe)],
            input="\n".join(commands) + "\n",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=300,
            check=False,
        )
        text = proc.stdout
        for mark in STOP_MARKS:
            if mark in text:
                raise SystemExit(f"STOP {name}: saw {mark}")
        raw_path = pathlib.Path(f"{prefix}_{name}.txt")
        raw_path.write_text(text)
        for line in text.splitlines():
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
        meta = "\n".join(
            [
                f"exe={exe}",
                f"sha256={digest}",
                f"id_name={id_name}",
                "options:",
                "(none)",
                f"commands={commands}",
                f"returncode={proc.returncode}",
                "",
            ]
        )
        pathlib.Path(f"{prefix}_{name}.txt.meta").write_text(meta)
        nodes = ""
        for line in text.splitlines():
            parts = line.split()
            if "nodes" in parts:
                nodes = parts[parts.index("nodes") + 1]
        ok = nodes == expected[name]
        lines.append(f"{name} nodes {nodes} expected {expected[name]} {'OK' if ok else 'FAIL'}")
        print(lines[-1], flush=True)
        if not ok:
            raise SystemExit(f"honesty failed {name}")
    lines.insert(2, f"id_name={id_name}")
    lines.append("no setoption sent")
    pathlib.Path(f"{prefix}_summary.txt").write_text("\n".join(lines) + "\n")
    print("HONESTY ok", flush=True)


if __name__ == "__main__":
    main()
