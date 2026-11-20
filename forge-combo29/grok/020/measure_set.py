#!/usr/bin/env python3
"""Depth search of a FEN/EPD list. One engine process. Stops on protocol errors.

Writes <prefix>.raw.txt, <prefix>.nodes.tsv, <prefix>.meta next to this script
unless --out is a directory.
"""
import argparse
import hashlib
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
    line = line.strip()
    if not line or line.startswith("#"):
        return ""
    # EPD: the first four fields are the position; keep a full FEN when present.
    parts = line.split()
    if len(parts) >= 6 and parts[4].isdigit() and parts[5].isdigit():
        return " ".join(parts[:6])
    if len(parts) >= 4:
        return " ".join(parts[:4]) + " 0 1"
    return line


class Session:
    def __init__(self, exe: str):
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.lines: list[str] = []

    def send(self, line: str) -> None:
        self.lines.append(">> " + line)
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, done) -> str:
        assert self.proc.stdout is not None
        while True:
            raw = self.proc.stdout.readline()
            if raw == "":
                raise SystemExit("engine closed stdout early")
            line = raw.rstrip("\r\n")
            self.lines.append(line)
            low = line.lower()
            for bit in STOP_BITS:
                if bit.lower() in low:
                    raise SystemExit("STOP " + line)
            if done(line):
                return line

    def close(self) -> None:
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--fens", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--extra", action="append", default=[], help="name=value after S14")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    exe = Path(args.exe).resolve()
    fens = [fen_of(line) for line in Path(args.fens).read_text().splitlines()]
    fens = [fen for fen in fens if fen]
    if args.limit:
        fens = fens[: args.limit]
    out_dir = Path(__file__).resolve().parent
    prefix = out_dir / args.prefix

    sha = hashlib.sha256(exe.read_bytes()).hexdigest()
    eng = Session(str(exe))
    id_name = ""
    try:
        eng.send("uci")
        while True:
            line = eng.read_until(lambda s: s == "uciok" or s.startswith("id name "))
            if line.startswith("id name ") and not id_name:
                id_name = line[len("id name ") :]
            if line == "uciok":
                break
        options = [("Threads", "1"), ("Hash", "16")] + list(S14)
        for item in args.extra:
            if "=" not in item:
                raise SystemExit("extra must be name=value")
            name, value = item.split("=", 1)
            options.append((name, value))
        option_lines = []
        for name, value in options:
            sent = f"setoption name {name} value {value}"
            option_lines.append(sent)
            eng.send(sent)
            eng.send("isready")
            eng.read_until(lambda s: s == "readyok")

        rows = []
        for index, fen in enumerate(fens, start=1):
            eng.send("ucinewgame")
            eng.send("isready")
            eng.read_until(lambda s: s == "readyok")
            eng.send("position fen " + fen)
            eng.send("isready")
            eng.read_until(lambda s: s == "readyok")
            eng.send(f"go depth {args.depth}")
            last_nodes = None
            last_depth = None
            while True:
                line = eng.read_until(lambda s: s.startswith("bestmove ") or s.startswith("info depth "))
                if line.startswith("info depth "):
                    parts = line.split()
                    if "nodes" in parts and "depth" in parts:
                        last_depth = int(parts[parts.index("depth") + 1])
                        last_nodes = int(parts[parts.index("nodes") + 1])
                    continue
                best = line.split()[1] if len(line.split()) > 1 else ""
                break
            if last_nodes is None:
                raise SystemExit(f"no nodes for position {index}")
            rows.append((index, last_nodes, last_depth, best, fen))
            print(f"{index} {last_nodes} d{last_depth} {best}", flush=True)
    finally:
        eng.close()

    prefix.with_suffix("").parent.mkdir(parents=True, exist_ok=True)
    raw_path = Path(str(prefix) + ".raw.txt")
    tsv_path = Path(str(prefix) + ".nodes.tsv")
    meta_path = Path(str(prefix) + ".meta")
    raw_path.write_text("\n".join(eng.lines) + "\n")
    tsv = ["index\tnodes\tdepth\tbestmove\tfen"]
    for index, nodes, depth, best, fen in rows:
        tsv.append(f"{index}\t{nodes}\t{depth}\t{best}\t{fen}")
    tsv_path.write_text("\n".join(tsv) + "\n")
    meta = [
        f"exe {exe}",
        f"sha256 {sha}",
        f"id_name {id_name}",
        f"depth {args.depth}",
        f"positions {len(rows)}",
        "options:",
    ]
    meta.extend(option_lines)
    meta_path.write_text("\n".join(meta) + "\n")
    total = sum(nodes for _i, nodes, _d, _b, _f in rows)
    print(f"SUM {total} positions {len(rows)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
