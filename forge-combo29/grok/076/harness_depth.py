#!/usr/bin/env python3
"""Fixed-depth UCI harness.

Usage:
  harness_depth.py EXE FENFILE DEPTH RAW META OPTIONS_FILE

Sends every line in OPTIONS_FILE, then for each FEN: ucinewgame, position, go depth.
After every setoption and every position, sends isready and reads through readyok.
Stops on unknown option, invalid value, invalid FEN, or illegal move.
RAW is the engine's stdout. META records the exe path, sha256, id name, and every
option line sent.
"""
import hashlib
import subprocess
import sys

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Engine:
    def __init__(self, exe, raw):
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.raw = raw

    def send(self, line):
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, done):
        lines = []
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                raise SystemExit("engine closed stdout before " + done)
            line = line.rstrip("\n")
            self.raw.write(line + "\n")
            self.raw.flush()
            lines.append(line)
            low = line.lower()
            for bad in BAD:
                if bad.lower() in low:
                    raise SystemExit("STOP " + bad + " :: " + line)
            if done(line):
                return lines

    def ready(self):
        self.send("isready")
        self.read_until(lambda line: line == "readyok")

    def close(self):
        self.send("quit")
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def main():
    if len(sys.argv) != 7:
        raise SystemExit("usage: harness_depth.py EXE FENFILE DEPTH RAW META OPTIONS_FILE")
    exe, fenfile, depth_text, raw_path, meta_path, options_path = sys.argv[1:]
    depth = int(depth_text)
    options = [line.strip() for line in open(options_path) if line.strip()]
    fens = []
    for line in open(fenfile):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fens.append(" ".join(line.split()[:6]))
    with open(raw_path, "w") as raw, open(meta_path, "w") as meta:
        meta.write("exe " + exe + "\n")
        meta.write("sha256 " + sha256(exe) + "\n")
        engine = Engine(exe, raw)
        engine.send("uci")
        uci_lines = engine.read_until(lambda line: line == "uciok")
        name = ""
        for line in uci_lines:
            if line.startswith("id name "):
                name = line[len("id name "):]
        meta.write("id_name " + name + "\n")
        engine.ready()
        for option in options:
            meta.write("option " + option + "\n")
            engine.send(option)
            engine.ready()
        for fen in fens:
            engine.send("ucinewgame")
            engine.ready()
            engine.send("position fen " + fen)
            engine.ready()
            engine.send("go depth " + str(depth))
            engine.read_until(lambda line: line.startswith("bestmove "))
        engine.close()
    print("positions", len(fens))


if __name__ == "__main__":
    main()
