#!/usr/bin/env python3
"""Depth-N node counts. One engine process. isready after every setoption and position.

Stops on unknown option, invalid value, invalid FEN, or illegal move.
S14 is sent once, in the required order, then Threads 1 and Hash 16.
Each position is ucinewgame + isready + position + isready + go.
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

BAD = ("unknown option", "invalid value", "invalid fen", "illegal move")


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    return list(enumerate(fens[offset:end], start=offset))


class Engine:
    def __init__(self, path):
        self.path = path
        self.proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.id_name = ""

    def send(self, line):
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, token):
        lines = []
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                sys.exit("engine closed stdout")
            line = line.rstrip("\r\n")
            lines.append(line)
            low = line.lower()
            if any(mark in low for mark in BAD):
                sys.exit("STOP " + line)
            if token in line:
                return lines

    def ready(self):
        self.send("isready")
        return self.read_until("readyok")

    def close(self):
        try:
            self.send("quit")
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--positions", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--count", type=int, default=-1)
    parser.add_argument("--option", action="append", default=[], help="Name=value after S14")
    args = parser.parse_args()

    extra = []
    for item in args.option:
        name, value = item.split("=", 1)
        extra.append((name, value))

    rows = load_fens(args.positions, args.offset, args.count)
    engine = Engine(args.exe)
    engine.send("uci")
    uci_lines = engine.read_until("uciok")
    for line in uci_lines:
        if line.startswith("id name "):
            engine.id_name = line
            break
    sent = []
    for name, value in S14 + [("Threads", "1"), ("Hash", "16")] + extra:
        command = f"setoption name {name} value {value}"
        engine.send(command)
        engine.ready()
        sent.append(command)

    raw_lines = []
    node_lines = []
    for index, fen in rows:
        engine.send("ucinewgame")
        engine.ready()
        engine.send(f"position fen {fen}")
        engine.ready()
        engine.send(f"go depth {args.depth}")
        go_lines = engine.read_until("bestmove")
        nodes = None
        last_info = ""
        for line in go_lines:
            if " nodes " in line and line.startswith("info "):
                parts = line.split()
                if "nodes" in parts:
                    nodes = int(parts[parts.index("nodes") + 1])
                    last_info = line
        if nodes is None:
            engine.close()
            sys.exit(f"no nodes for position {index}")
        raw_lines.append(f"# {index} {fen}")
        raw_lines.append(last_info)
        raw_lines.append(go_lines[-1])
        node_lines.append(f"{index} {nodes}")
        print(f"{index} {nodes}", flush=True)
    engine.close()

    out = args.out
    with open(out + ".txt", "w", encoding="utf-8") as handle:
        handle.write("\n".join(raw_lines) + "\n")
    with open(out + ".nodes", "w", encoding="utf-8") as handle:
        handle.write("\n".join(node_lines) + "\n")
    with open(out + ".meta", "w", encoding="utf-8") as handle:
        handle.write(f"exe={args.exe}\n")
        handle.write(f"sha256={sha256(args.exe)}\n")
        handle.write(f"id_name={engine.id_name}\n")
        handle.write(f"positions={args.positions}\n")
        handle.write(f"depth={args.depth}\n")
        handle.write(f"offset={args.offset}\n")
        handle.write(f"count={args.count}\n")
        for command in sent:
            handle.write(f"option={command}\n")


if __name__ == "__main__":
    main()
