#!/usr/bin/env python3
"""Depth-12 node run. One engine process, S14 once, then each FEN.

Usage: orun.py <exe> <fens> <out_prefix> <switch>
  switch is none, or Name=true / Name=false (sent after S14).
Raw engine stdout goes to <out_prefix>.txt and options to <out_prefix>.meta.
"""
import hashlib
import os
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
STOP = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe):
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        self.buf = b""
        self.out = []

    def send(self, line):
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def readline(self, timeout):
        while b"\n" not in self.buf:
            ready, _, _ = select.select([self.proc.stdout], [], [], timeout)
            if not ready:
                raise TimeoutError(f"no output for {timeout}s")
            chunk = os.read(self.proc.stdout.fileno(), 65536)
            if not chunk:
                raise EOFError("engine closed stdout")
            self.buf += chunk
        raw, self.buf = self.buf.split(b"\n", 1)
        text = raw.decode("utf-8", "replace").rstrip("\r")
        self.out.append(text)
        for bad in STOP:
            if bad in text:
                raise SystemExit(f"STOP: {text}")
        return text

    def until(self, pred, timeout):
        while True:
            line = self.readline(timeout)
            if pred(line):
                return line

    def close(self):
        try:
            if self.proc.poll() is None:
                self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()
            self.proc.wait(timeout=5)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main():
    if len(sys.argv) != 5:
        sys.exit("usage: orun.py <exe> <fens> <out_prefix> <switch>")
    exe, fens_path, prefix, switch = sys.argv[1:]
    options = [("Threads", "1"), ("Hash", "16")] + S14
    if switch != "none":
        if "=" not in switch:
            sys.exit("switch must be none or Name=true or Name=false")
        name, value = switch.split("=", 1)
        if value not in ("true", "false"):
            sys.exit("switch value must be true or false")
        options.append((name, value))
    fens = []
    with open(fens_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                fens.append(line)
    exe_sha = sha256_file(exe)
    eng = Engine(exe)
    id_name = ""
    try:
        eng.send("uci")
        while True:
            line = eng.until(lambda s: s == "uciok" or s.startswith("id name "), 60)
            if line.startswith("id name "):
                id_name = line[len("id name "):]
            if line == "uciok":
                break
        # until() returns on id name before uciok; keep reading.
        if id_name and eng.out[-1] != "uciok":
            eng.until(lambda s: s == "uciok", 60)
        for name, value in options:
            eng.send(f"setoption name {name} value {value}")
            eng.send("isready")
            eng.until(lambda s: s == "readyok", 60)
        for index, fen in enumerate(fens, start=1):
            eng.send("ucinewgame")
            eng.send("isready")
            eng.until(lambda s: s == "readyok", 60)
            eng.send(f"position fen {fen}")
            eng.send("isready")
            eng.until(lambda s: s == "readyok", 60)
            eng.send("go depth 12")
            eng.until(lambda s: s.startswith("bestmove "), 180)
            if index % 20 == 0:
                print(f"positions {index}", flush=True)
    finally:
        text = "\n".join(eng.out) + ("\n" if eng.out else "")
        with open(prefix + ".txt", "w", encoding="utf-8") as f:
            f.write(text)
        with open(prefix + ".meta", "w", encoding="utf-8") as f:
            f.write(f"exe: {exe}\n")
            f.write(f"sha256: {exe_sha}\n")
            f.write(f"id_name: {id_name}\n")
            f.write("options:\n")
            for name, value in options:
                f.write(f"setoption name {name} value {value}\n")
            f.write(f"fens: {fens_path}\n")
            f.write(f"fen_count: {len(fens)}\n")
        eng.close()
    print(f"wrote {prefix}.txt {prefix}.meta")


if __name__ == "__main__":
    main()
