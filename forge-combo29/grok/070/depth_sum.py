#!/usr/bin/env python3
"""Fixed-depth node harness. One engine process. S14, then any extra options.

After every setoption and every position command, sends isready and reads
every line up to readyok. Stops on unknown option, invalid value, invalid
FEN, or illegal move. Writes the full transcript and a .meta file.
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

STOP_MARKS = ("unknown option", "invalid value", "invalid fen", "illegal move")


def load_positions(path):
    rows = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text or text.startswith("#"):
                continue
            rows.append(text.split(";")[0].strip())
    return rows


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Session:
    def __init__(self, exe):
        self.exe = exe
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.lines = []

    def send(self, line):
        self.lines.append(">> " + line)
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, done):
        while True:
            raw = self.proc.stdout.readline()
            if raw == "":
                raise SystemExit("engine closed stdout")
            line = raw.rstrip("\n")
            self.lines.append(line)
            low = line.lower()
            for mark in STOP_MARKS:
                if mark in low:
                    raise SystemExit("STOP " + line)
            if done(line):
                return line

    def isready(self):
        self.send("isready")
        self.read_until(lambda line: line == "readyok")

    def setoption(self, name, value):
        self.send(f"setoption name {name} value {value}")
        self.isready()

    def close(self):
        try:
            self.send("quit")
        except BrokenPipeError:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--positions", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--extra", action="append", default=[])
    args = parser.parse_args()

    positions = load_positions(args.positions)
    if args.limit > 0:
        positions = positions[: args.limit]
    extras = []
    for item in args.extra:
        name, value = item.split("=", 1)
        extras.append((name, value))

    session = Session(args.exe)
    id_name = ""
    try:
        session.send("uci")
        uciok = session.read_until(lambda line: line == "uciok")
        for line in session.lines:
            if line.startswith("id name "):
                id_name = line
        if uciok != "uciok":
            raise SystemExit("missing uciok")
        session.isready()
        session.setoption("Threads", "1")
        session.setoption("Hash", "16")
        for name, value in S14:
            session.setoption(name, value)
        for name, value in extras:
            session.setoption(name, value)
        for fen in positions:
            session.send("ucinewgame")
            session.isready()
            session.send("position fen " + fen)
            session.isready()
            session.send(f"go depth {args.depth}")
            session.read_until(lambda line: line.startswith("bestmove "))
    finally:
        session.close()
        with open(args.out + ".raw.txt", "w", encoding="utf-8") as handle:
            handle.write("\n".join(session.lines))
            handle.write("\n")
        with open(args.out + ".meta", "w", encoding="utf-8") as handle:
            handle.write(f"exe={args.exe}\n")
            handle.write(f"sha256={sha256(args.exe)}\n")
            handle.write(f"id_name={id_name}\n")
            handle.write("options_sent=Threads 1\n")
            handle.write("options_sent=Hash 16\n")
            for name, value in S14:
                handle.write(f"options_sent={name} {value}\n")
            for name, value in extras:
                handle.write(f"options_sent={name} {value}\n")
            handle.write(f"positions={args.positions}\n")
            handle.write(f"depth={args.depth}\n")
            handle.write(f"count={len(positions)}\n")
    print(f"wrote {args.out}.raw.txt positions {len(positions)}", file=sys.stderr)


if __name__ == "__main__":
    main()
