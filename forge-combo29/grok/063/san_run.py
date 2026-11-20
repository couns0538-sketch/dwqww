#!/usr/bin/env python3
"""One runner for the sanitizer proof and for the deliberate heap over-read.

S14, then any extra options, then each position: ucinewgame, isready, position, isready, go.
The engine's stdout and stderr are one stream. A dead engine is recorded, not hidden.
"""
import argparse
import hashlib
import select
import subprocess
import sys

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


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def asan_count(exe):
    proc = subprocess.run(["nm", "-C", exe], capture_output=True, text=True)
    return sum(1 for line in proc.stdout.splitlines() if "__asan_" in line)


def load_fens(path, offset, count):
    fens = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 6 and parts[1] in ("w", "b"):
                fen = " ".join(parts[:6])
            elif len(parts) >= 4 and parts[1] in ("w", "b"):
                fen = " ".join(parts[:4]) + " 0 1"
            else:
                fen = line
            fens.append(fen)
    end = len(fens) if count < 0 else min(len(fens), offset + count)
    return fens[offset:end]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--positions", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--count", type=int, default=-1)
    parser.add_argument("--option", action="append", default=[])
    args = parser.parse_args()

    extra = []
    for item in args.option:
        name, value = item.split("=", 1)
        extra.append((name, value))
    fens = load_fens(args.positions, args.offset, args.count)
    proc = subprocess.Popen(
        [args.exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    log_lines = []

    def send(line):
        if proc.poll() is not None:
            return False
        try:
            proc.stdin.write(line + "\n")
            proc.stdin.flush()
            return True
        except BrokenPipeError:
            return False

    def read_until(tokens, idle=2.0):
        while True:
            ready, _, _ = select.select([proc.stdout], [], [], idle)
            if not ready:
                return False
            line = proc.stdout.readline()
            if line == "":
                return False
            line = line.rstrip("\r\n")
            log_lines.append(line)
            if any(token in line for token in tokens):
                return True

    def poke(line):
        if not send(line):
            return False
        return read_until(("readyok", "AddressSanitizer", "heap-buffer-overflow", "runtime error:"))

    send("uci")
    read_until(("uciok",))
    for name, value in S14 + [("Threads", "1"), ("Hash", "16")] + extra:
        send(f"setoption name {name} value {value}")
        if not poke("isready"):
            break
    for fen in fens:
        if proc.poll() is not None:
            break
        send("ucinewgame")
        poke("isready")
        send(f"position fen {fen}")
        if not poke("isready"):
            break
        if any("AddressSanitizer" in line or "heap-buffer-overflow" in line for line in log_lines):
            break
        send(f"go depth {args.depth}")
        if not read_until(("bestmove", "AddressSanitizer", "heap-buffer-overflow", "runtime error:"), idle=120.0):
            break
    send("quit")
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)
    while True:
        ready, _, _ = select.select([proc.stdout], [], [], 0.2)
        if not ready:
            break
        line = proc.stdout.readline()
        if line == "":
            break
        log_lines.append(line.rstrip("\r\n"))
    log = "\n".join(log_lines) + "\n"
    markers = (
        "AddressSanitizer",
        "runtime error:",
        "heap-buffer-overflow",
        "undefined-behavior",
    )
    hits = [line for line in log_lines if any(mark in line for mark in markers)]
    with open(args.out + ".txt", "w", encoding="utf-8") as handle:
        handle.write(log)
        if not log.endswith("\n"):
            handle.write("\n")
    with open(args.out + ".hits", "w", encoding="utf-8") as handle:
        handle.write(f"exit {proc.returncode}\n")
        handle.write(f"sanitizer_lines {len(hits)}\n")
        for line in hits:
            handle.write(line + "\n")
    nm_count = asan_count(args.exe)
    id_name = ""
    for line in log.splitlines():
        if line.startswith("id name "):
            id_name = line
            break
    with open(args.out + ".meta", "w", encoding="utf-8") as handle:
        handle.write(f"exe={args.exe}\n")
        handle.write(f"sha256={sha256(args.exe)}\n")
        handle.write(f"id_name={id_name}\n")
        handle.write(f"nm_asan_symbols={nm_count}\n")
        handle.write(f"positions={args.positions}\n")
        handle.write(f"depth={args.depth}\n")
        handle.write(f"offset={args.offset}\n")
        handle.write(f"count={args.count}\n")
        handle.write(f"exit={proc.returncode}\n")
        handle.write(f"sanitizer_lines={len(hits)}\n")
        for name, value in S14 + [("Threads", "1"), ("Hash", "16")] + extra:
            handle.write(f"option=setoption name {name} value {value}\n")
    print(f"nm_asan_symbols {nm_count}")
    print(f"exit {proc.returncode}")
    print(f"sanitizer_lines {len(hits)}")
    if hits:
        print(hits[0])
    if nm_count <= 0:
        sys.exit("asan symbols missing")


if __name__ == "__main__":
    main()
