#!/usr/bin/env python3
"""Depth-search harness. One engine process. isready after every setoption and position.

Stops on unknown option, invalid value, invalid FEN, or illegal move.
Writes the raw transcript, one nodes row per position, and a .meta file.
"""
import argparse
import hashlib
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

STOP_MARKERS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def fen_of(line):
    parts = line.split()
    if len(parts) >= 6:
        return " ".join(parts[:6])
    return line.strip()


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Engine:
    def __init__(self, exe, raw_path):
        self.raw = open(raw_path, "w", encoding="utf-8")
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

    def send(self, line):
        self.raw.write(">> " + line + "\n")
        self.raw.flush()
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, done):
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                raise SystemExit("engine closed stdout")
            line = line.rstrip("\n")
            self.raw.write(line + "\n")
            self.raw.flush()
            for marker in STOP_MARKERS:
                if marker in line:
                    raise SystemExit("STOP " + line)
            if done(line):
                return line

    def close(self):
        try:
            self.send("quit")
        except BrokenPipeError:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        self.raw.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--positions", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--stem", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--idea", choices=("absent", "false", "true"), default="absent")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    positions = []
    with open(args.positions, encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                positions.append(fen_of(line))
    if args.limit > 0:
        positions = positions[: args.limit]

    options = [("Threads", "1"), ("Hash", "16")] + S14
    if args.idea != "absent":
        options.append(("IdeaB8", args.idea))

    raw_path = args.out + "/" + args.stem + ".txt"
    rows_path = args.out + "/" + args.stem + ".nodes"
    meta_path = args.out + "/" + args.stem + ".meta"
    engine = Engine(args.exe, raw_path)
    id_name = ""
    try:
        engine.send("uci")
        while True:
            line = engine.read_until(lambda item: item == "uciok" or item.startswith("id name "))
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
                continue
            break
        for name, value in options:
            engine.send(f"setoption name {name} value {value}")
            engine.send("isready")
            engine.read_until(lambda item: item == "readyok")
        with open(rows_path, "w", encoding="utf-8") as rows:
            for index, fen in enumerate(positions, start=1):
                engine.send("ucinewgame")
                engine.send("isready")
                engine.read_until(lambda item: item == "readyok")
                engine.send("position fen " + fen)
                engine.send("isready")
                engine.read_until(lambda item: item == "readyok")
                engine.send(f"go depth {args.depth}")
                nodes = None
                while True:
                    line = engine.read_until(lambda item: item.startswith("bestmove ") or " nodes " in item)
                    if line.startswith("bestmove "):
                        break
                    for token, value in zip(line.split(), line.split()[1:]):
                        if token == "nodes":
                            nodes = int(value)
                if nodes is None:
                    raise SystemExit("no nodes before bestmove for " + fen)
                rows.write(f"{index}\t{nodes}\t{fen}\n")
                rows.flush()
                if index % 25 == 0:
                    print(f"{args.stem} {index}/{len(positions)}", file=sys.stderr, flush=True)
    finally:
        engine.close()

    with open(meta_path, "w", encoding="utf-8") as meta:
        meta.write(f"exe {args.exe}\n")
        meta.write(f"sha256 {sha256_file(args.exe)}\n")
        meta.write(f"id_name {id_name}\n")
        meta.write(f"positions {args.positions}\n")
        meta.write(f"positions_sha256 {sha256_file(args.positions)}\n")
        meta.write(f"depth {args.depth}\n")
        meta.write(f"idea {args.idea}\n")
        meta.write("options\n")
        for name, value in options:
            meta.write(f"setoption name {name} value {value}\n")
    print(args.stem, "done", len(positions), file=sys.stderr)


if __name__ == "__main__":
    main()
