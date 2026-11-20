#!/usr/bin/env python3
"""Same runner for the sanitizer build and the scratch build that must trip it.
S14 plus IdeaA4 true. isready after every setoption and position.
"""
import hashlib
import os
import subprocess
import sys
from pathlib import Path

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")
SAN = ("AddressSanitizer", "UndefinedBehaviorSanitizer", "runtime error:")


def load_fens(path: Path):
    fens = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        fens.append(" ".join(parts[:6]) if len(parts) >= 6 else " ".join(parts))
    return fens


def main():
    exe, fen_path, depth_s, out_prefix, opt_path = sys.argv[1:6]
    depth = int(depth_s)
    fens = load_fens(Path(fen_path))
    options = [line.strip() for line in Path(opt_path).read_text().splitlines() if line.strip()]
    prefix = Path(out_prefix)
    raw = Path(str(prefix) + ".raw")
    meta_path = Path(str(prefix) + ".meta")
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    nm = subprocess.run(["nm", "-C", exe], capture_output=True, text=True, check=False)
    asan_count = sum(1 for line in nm.stdout.splitlines() if "__asan_" in line)
    env = os.environ.copy()
    env["ASAN_OPTIONS"] = "detect_leaks=0:halt_on_error=1:abort_on_error=0"
    env["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
    )
    lines = []
    sanitizer_lines = []

    def send(line):
        lines.append(">> " + line)
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(done):
        while True:
            line = proc.stdout.readline()
            if line == "":
                return None
            line = line.rstrip("\r\n")
            lines.append(line)
            if any(mark in line for mark in SAN):
                sanitizer_lines.append(line)
            low = line.lower()
            for bad in BAD:
                if bad.lower() in low:
                    raise SystemExit(f"STOP {bad}: {line}")
            if done(line):
                return line

    def ready():
        send("isready")
        got = read_until(lambda line: line == "readyok")
        if got is None:
            return False
        return True

    id_name = ""
    try:
        send("uci")
        if read_until(lambda line: line == "uciok") is None:
            raise SystemExit("no uciok")
        id_name = next(line for line in lines if line.startswith("id name "))
        for opt in options:
            send("setoption name " + opt)
            if not ready():
                break
        done = 0
        for fen in fens:
            if sanitizer_lines:
                break
            send("ucinewgame")
            if not ready():
                break
            send("position fen " + fen)
            if not ready():
                break
            send(f"go depth {depth}")
            while True:
                line = read_until(lambda item: item.startswith("bestmove ") or " nodes " in item)
                if line is None or line.startswith("bestmove "):
                    break
            if sanitizer_lines or proc.poll() is not None:
                break
            done += 1
    finally:
        if proc.poll() is None:
            try:
                send("quit")
            except (BrokenPipeError, OSError):
                pass
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        raw.write_text("\n".join(lines) + "\n")
        meta = [
            f"exe {exe}",
            f"sha256 {sha}",
            id_name,
            f"depth {depth}",
            f"positions_file {fen_path}",
            f"positions_requested {len(fens)}",
            "options:",
            *[f"setoption name {opt}" for opt in options],
            f"nm_asan_count {asan_count}",
            f"sanitizer_lines {len(sanitizer_lines)}",
            *[f"sanitizer {line}" for line in sanitizer_lines[:8]],
        ]
        meta_path.write_text("\n".join(meta) + "\n")
        print(f"nm_asan_count {asan_count}")
        print(f"sanitizer_lines {len(sanitizer_lines)}")
        for line in sanitizer_lines[:6]:
            print(line)
        print(f"positions_finished {done if 'done' in dir() else 0}")


if __name__ == "__main__":
    main()
