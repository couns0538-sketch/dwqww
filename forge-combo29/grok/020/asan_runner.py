#!/usr/bin/env python3
"""Same UCI runner for the sanitizer build and for the scratch build.

S14, then any --extra name=value, then each FEN at --depth.
A dead engine is recorded; the raw log is still written.
"""
import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path

STOP_BITS = ("unknown option", "invalid value", "invalid FEN", "illegal move")
S14 = [
    ("LmrQuietBase", "93"),
    ("LmrQuietDivisor", "205"),
    ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"),
    ("LmrHistoryDivisor", "5643"),
    ("NullMoveBase", "5"),
    ("LmpBase", "8"),
    ("HistoryPruneMultiplier", "2220"),
    ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"),
    ("HistoryBonusMax", "2212"),
    ("SingularDepth", "6"),
    ("IirDepth", "2"),
    ("NonPawnCorrection", "true"),
]


def fen_of(line: str) -> str:
    parts = line.split()
    if len(parts) >= 6 and parts[4].isdigit() and parts[5].isdigit():
        return " ".join(parts[:6])
    if len(parts) >= 4:
        return " ".join(parts[:4]) + " 0 1"
    return line.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--fens", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--extra", action="append", default=[])
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    exe = Path(args.exe).resolve()
    fens = []
    for line in Path(args.fens).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fens.append(fen_of(line))
    if args.limit:
        fens = fens[: args.limit]
    out = Path(__file__).resolve().parent
    sha = hashlib.sha256(exe.read_bytes()).hexdigest()
    nm = subprocess.run(["nm", "-C", str(exe)], capture_output=True, text=True, check=False)
    asan_count = sum(1 for line in nm.stdout.splitlines() if "__asan_" in line)
    env = os.environ.copy()
    env.setdefault("ASAN_OPTIONS", "detect_leaks=0:halt_on_error=1:abort_on_error=1")
    env.setdefault("UBSAN_OPTIONS", "halt_on_error=1:print_stacktrace=1")
    proc = subprocess.Popen(
        [str(exe)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )
    lines: list[str] = []

    def send(text: str) -> None:
        lines.append(">> " + text)
        assert proc.stdin is not None
        proc.stdin.write(text + "\n")
        proc.stdin.flush()

    def read_until(done) -> str | None:
        assert proc.stdout is not None
        while True:
            raw = proc.stdout.readline()
            if raw == "":
                return None
            line = raw.rstrip("\r\n")
            lines.append(line)
            low = line.lower()
            for bit in STOP_BITS:
                if bit.lower() in low:
                    lines.append("STOP " + line)
                    return "STOP"
            if done(line):
                return line

    id_name = ""
    stopped = ""
    try:
        send("uci")
        while True:
            line = read_until(lambda s: s == "uciok" or s.startswith("id name "))
            if line is None:
                stopped = "eof during uci"
                break
            if line == "STOP":
                stopped = "stop during uci"
                break
            if line.startswith("id name ") and not id_name:
                id_name = line[len("id name ") :]
            if line == "uciok":
                break
        options = [("Threads", "1"), ("Hash", "16")] + list(S14)
        for item in args.extra:
            name, value = item.split("=", 1)
            options.append((name, value))
        option_lines = [f"setoption name {name} value {value}" for name, value in options]
        if not stopped:
            for sent in option_lines:
                send(sent)
                send("isready")
                got = read_until(lambda s: s == "readyok")
                if got is None:
                    stopped = "eof during options"
                    break
                if got == "STOP":
                    stopped = "stop during options"
                    break
        done = 0
        if not stopped:
            for index, fen in enumerate(fens, start=1):
                send("ucinewgame")
                send("isready")
                if read_until(lambda s: s == "readyok") != "readyok":
                    stopped = f"eof at ucinewgame {index}"
                    break
                send("position fen " + fen)
                send("isready")
                got = read_until(lambda s: s == "readyok")
                if got != "readyok":
                    stopped = f"no readyok after position {index}"
                    break
                send(f"go depth {args.depth}")
                while True:
                    got = read_until(lambda s: s.startswith("bestmove ") or s.startswith("info depth "))
                    if got is None:
                        stopped = f"eof during go {index}"
                        break
                    if got == "STOP" or got.startswith("bestmove "):
                        if got == "STOP":
                            stopped = f"stop during go {index}"
                        break
                if stopped:
                    break
                done = index
                print(f"{index} done", flush=True)
    finally:
        try:
            if proc.poll() is None:
                send("quit")
        except Exception:
            pass
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
    raw_path = out / (args.prefix + ".raw.txt")
    meta_path = out / (args.prefix + ".meta")
    raw_path.write_text("\n".join(lines) + "\n")
    sanitizer_lines = [
        line for line in lines
        if "AddressSanitizer" in line or "UndefinedBehaviorSanitizer" in line or "runtime error:" in line
    ]
    meta = [
        f"exe {exe}",
        f"sha256 {sha}",
        f"id_name {id_name}",
        f"depth {args.depth}",
        f"positions_done {done}",
        f"positions_asked {len(fens)}",
        f"exit {proc.returncode}",
        f"stopped {stopped or 'no'}",
        f"nm_asan_symbol_lines {asan_count}",
        f"sanitizer_lines {len(sanitizer_lines)}",
        "options:",
        *option_lines,
    ]
    if sanitizer_lines:
        meta.append("sanitizer:")
        meta.extend(sanitizer_lines[:30])
    meta_path.write_text("\n".join(meta) + "\n")
    print(f"done {done}/{len(fens)} asan_symbols {asan_count} sanitizer_lines {len(sanitizer_lines)} stopped {stopped or 'no'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
