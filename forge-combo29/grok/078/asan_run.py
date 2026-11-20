#!/usr/bin/env python3
"""Same search runner for the sanitizer build and the deliberate-bug build.

Protocol matches depth_nodes.py: S14, then Threads 1, Hash 16, then extras,
then ucinewgame / position / go for each FEN. Stdout and stderr are both saved.
"""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from depth_nodes import S14, STOP_MARKS, load_fens, sha256


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--fens", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--extra", action="append", default=[])
    args = parser.parse_args()

    exe = Path(args.exe)
    fens = load_fens(Path(args.fens))
    if args.limit:
        fens = fens[: args.limit]
    options = list(S14) + [item.split("=", 1) for item in args.extra]
    env = os.environ.copy()
    env.setdefault("ASAN_OPTIONS", "detect_leaks=0")
    env.setdefault("UBSAN_OPTIONS", "halt_on_error=1:print_stacktrace=1")

    proc = subprocess.Popen(
        [str(exe)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        env=env,
    )
    assert proc.stdin is not None and proc.stdout is not None
    raw: list[str] = []

    def send(line: str) -> None:
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def bad(line: str) -> bool:
        return any(mark in line for mark in STOP_MARKS)

    send("uci")
    id_name = ""
    while True:
        line = proc.stdout.readline()
        if line == "":
            break
        raw.append(line)
        if line.startswith("id name "):
            id_name = line.strip()
        if bad(line) or line.startswith("uciok"):
            if line.startswith("uciok"):
                break
            break
    send("isready")
    while True:
        line = proc.stdout.readline()
        if line == "":
            break
        raw.append(line)
        if bad(line) or line.startswith("readyok"):
            break
    for name, value in options:
        send(f"setoption name {name} value {value}")
        send("isready")
        while True:
            line = proc.stdout.readline()
            if line == "":
                break
            raw.append(line)
            if bad(line) or line.startswith("readyok"):
                break
    for index, fen in enumerate(fens):
        raw.append(f"# POS {index}\n")
        send("ucinewgame")
        send("isready")
        while True:
            line = proc.stdout.readline()
            if line == "":
                break
            raw.append(line)
            if bad(line) or line.startswith("readyok"):
                break
        if line == "":
            break
        send("position fen " + fen)
        send("isready")
        while True:
            line = proc.stdout.readline()
            if line == "":
                break
            raw.append(line)
            if bad(line) or line.startswith("readyok"):
                break
        if line == "":
            break
        send(f"go depth {args.depth}")
        while True:
            line = proc.stdout.readline()
            if line == "":
                break
            raw.append(line)
            if bad(line) or line.startswith("bestmove "):
                break
        if line == "":
            break
        if (index + 1) % 25 == 0 or index + 1 == len(fens):
            print(f"done {index + 1}/{len(fens)}", flush=True)
    try:
        send("quit")
    except BrokenPipeError:
        pass
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=10)
    err = proc.stderr.read() if proc.stderr is not None else ""
    out = Path(args.out)
    Path(str(out) + ".raw").write_text("".join(raw))
    Path(str(out) + ".err").write_text(err)
    option_lines = "\n".join(f"setoption name {name} value {value}" for name, value in options)
    nm = subprocess.run(["nm", "-C", str(exe)], check=False, capture_output=True, text=True)
    asan_count = sum(1 for line in nm.stdout.splitlines() if "__asan_" in line)
    Path(str(out) + ".meta").write_text(
        f"exe: {exe}\n"
        f"sha256: {sha256(exe)}\n"
        f"id_name: {id_name}\n"
        f"fens: {args.fens}\n"
        f"depth: {args.depth}\n"
        f"count: {len(fens)}\n"
        f"exit: {proc.returncode}\n"
        f"nm_asan_count: {asan_count}\n"
        f"ASAN_OPTIONS: {env.get('ASAN_OPTIONS', '')}\n"
        f"UBSAN_OPTIONS: {env.get('UBSAN_OPTIONS', '')}\n"
        "options:\n"
        f"{option_lines}\n"
    )
    err_lines = [line for line in err.splitlines() if "Sanitizer" in line or "runtime error" in line]
    print(f"exit {proc.returncode}")
    print(f"nm_asan_count {asan_count}")
    print(f"sanitizer_lines {len(err_lines)}")
    for line in err_lines[:8]:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
