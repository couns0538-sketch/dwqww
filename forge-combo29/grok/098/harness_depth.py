#!/usr/bin/env python3
"""Depth search harness. One engine process. Stops on a bad engine line.

Reads a FEN file (one position per line, first six fields). Sends Hash, Threads,
the S14 options, then any extra options, before every go. ucinewgame and isready
before every go. After every setoption and every position, reads until readyok.
"""
import hashlib
import os
import select
import subprocess
import sys

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")
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


def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(2)


def load_fens(path):
    fens = []
    with open(path) as handle:
        for line in handle:
            parts = line.split()
            if not parts:
                continue
            if len(parts) < 6:
                die(f"short fen line: {line.rstrip()}")
            fens.append(" ".join(parts[:6]))
    if not fens:
        die(f"no positions in {path}")
    return fens


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_line(proc, pending, timeout):
    while b"\n" not in pending[0]:
        ready, _, _ = select.select([proc.stdout], [], [], timeout)
        if not ready:
            return None
        chunk = os.read(proc.stdout.fileno(), 1 << 16)
        if chunk == b"":
            return None
        pending[0] += chunk
    line, pending[0] = pending[0].split(b"\n", 1)
    return line.decode("utf-8", "replace") + "\n"


def read_until(proc, pending, raw, predicate, timeout):
    while True:
        line = read_line(proc, pending, timeout)
        if line is None:
            proc.kill()
            die(f"timeout or eof waiting for engine, pid {proc.pid}")
        raw.write(line)
        raw.flush()
        lower = line.lower()
        for phrase in BAD:
            if phrase.lower() in lower:
                proc.kill()
                die(f"stopped on {phrase}: {line.rstrip()}")
        if predicate(line):
            return line


def send(proc, text):
    proc.stdin.write((text + "\n").encode())
    proc.stdin.flush()


def main():
    if len(sys.argv) < 6:
        die("usage: harness_depth.py EXE FENS DEPTH TAG OUTDIR [Name Value]...")
    exe, fens_path, depth_text, tag, outdir = sys.argv[1:6]
    extra = sys.argv[6:]
    if len(extra) % 2 != 0:
        die("options must be Name Value pairs")
    depth = int(depth_text)
    fens = load_fens(fens_path)
    os.makedirs(outdir, exist_ok=True)
    raw_path = os.path.join(outdir, tag + ".raw.txt")
    meta_path = os.path.join(outdir, tag + ".meta")
    exe_real = os.path.realpath(exe)
    digest = sha256(exe_real)
    options = [("Hash", "16"), ("Threads", "1")] + S14
    for i in range(0, len(extra), 2):
        options.append((extra[i], extra[i + 1]))
    option_lines = [f"setoption name {name} value {value}" for name, value in options]
    pending = [b""]
    with open(raw_path, "w") as raw:
        proc = subprocess.Popen(
            [exe_real],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        started = os.readlink(f"/proc/{proc.pid}/exe")
        if started != exe_real:
            proc.kill()
            die(f"started exe {started} != {exe_real}")
        send(proc, "uci")
        id_name = ""
        def take_uci(line):
            nonlocal id_name
            if line.startswith("id name "):
                id_name = line[len("id name "):].rstrip("\n")
            return line.strip() == "uciok"
        read_until(proc, pending, raw, take_uci, 30)
        send(proc, "isready")
        read_until(proc, pending, raw, lambda line: line.strip() == "readyok", 30)
        for fen in fens:
            send(proc, "ucinewgame")
            send(proc, "isready")
            read_until(proc, pending, raw, lambda line: line.strip() == "readyok", 30)
            for line in option_lines:
                send(proc, line)
                send(proc, "isready")
                read_until(proc, pending, raw, lambda ready: ready.strip() == "readyok", 30)
            send(proc, f"position fen {fen}")
            send(proc, "isready")
            read_until(proc, pending, raw, lambda line: line.strip() == "readyok", 30)
            send(proc, f"go depth {depth}")
            read_until(proc, pending, raw, lambda line: line.startswith("bestmove "), 180)
        send(proc, "quit")
        proc.wait(timeout=30)
    with open(meta_path, "w") as meta:
        meta.write(f"exe={exe_real}\n")
        meta.write(f"started={started}\n")
        meta.write(f"sha256={digest}\n")
        meta.write(f"id_name={id_name}\n")
        meta.write(f"positions={fens_path}\n")
        meta.write(f"position_count={len(fens)}\n")
        meta.write(f"depth={depth}\n")
        meta.write(f"tag={tag}\n")
        meta.write("options_sent:\n")
        for line in option_lines:
            meta.write(line + "\n")
    print(f"ok {tag} positions {len(fens)} raw {raw_path}")


if __name__ == "__main__":
    main()
