#!/usr/bin/env python3
"""Fixed-depth node sums. S14, Threads 1, Hash 16, ucinewgame before every go."""
import argparse
import hashlib
import pathlib
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
    ("Threads", "1"),
    ("Hash", "16"),
]
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, path: str):
        self.path = path
        self.proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.log = []

    def send(self, line: str) -> None:
        self.log.append(">> " + line)
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, ready) -> list:
        assert self.proc.stdout is not None
        got = []
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                raise SystemExit("engine closed\n" + "\n".join(self.log[-30:]))
            line = line.rstrip("\r\n")
            self.log.append(line)
            got.append(line)
            for bad in BAD:
                if bad in line:
                    raise SystemExit(f"STOP {line}")
            if ready(line):
                return got

    def close(self) -> None:
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def fen_of(line: str) -> str:
    parts = line.split()
    if len(parts) < 4:
        raise SystemExit(f"short position line: {line}")
    if len(parts) >= 6:
        return " ".join(parts[:6])
    return line.strip()


def last_info(lines: list) -> tuple:
    info = None
    for line in lines:
        if line.startswith("info depth "):
            info = line
    if info is None:
        raise SystemExit("no info depth line\n" + "\n".join(lines[-20:]))
    parts = info.split()
    nodes = None
    score = None
    depth = None
    i = 0
    while i < len(parts):
        if parts[i] == "depth" and i + 1 < len(parts):
            depth = int(parts[i + 1])
        elif parts[i] == "nodes" and i + 1 < len(parts):
            nodes = int(parts[i + 1])
        elif parts[i] == "score" and i + 2 < len(parts):
            score = parts[i + 1] + " " + parts[i + 2]
        i += 1
    best = ""
    for line in lines:
        if line.startswith("bestmove "):
            best = line.split()[1]
    if nodes is None or depth is None or score is None or not best:
        raise SystemExit(f"unparsed info: {info}")
    return depth, nodes, score, best


def sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--positions", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--switch", choices=("omit", "false", "true"), default="omit")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    fens = [fen_of(line) for line in pathlib.Path(args.positions).read_text().splitlines() if line.strip()]
    if args.limit:
        fens = fens[: args.limit]
    engine = Engine(args.exe)
    raw_path = out / f"{args.label}.raw"
    try:
        engine.send("uci")
        uci_lines = engine.read_until(lambda line: line == "uciok")
        name = ""
        for line in uci_lines:
            if line.startswith("id name "):
                name = line[len("id name ") :]
        sent = []
        for opt, value in S14:
            command = f"setoption name {opt} value {value}"
            sent.append(command)
            engine.send(command)
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok")
        if args.switch != "omit":
            command = f"setoption name IdeaS37 value {args.switch}"
            sent.append(command)
            engine.send(command)
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok")
        rows = []
        for index, fen in enumerate(fens, start=1):
            engine.send("ucinewgame")
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok")
            engine.send(f"position fen {fen}")
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok")
            engine.send(f"go depth {args.depth}")
            got = engine.read_until(lambda line: line.startswith("bestmove "))
            depth, nodes, score, best = last_info(got)
            rows.append(f"{index} {nodes} {depth} {score} {best}")
            if index % 50 == 0 or index == len(fens):
                print(f"{args.label} {index}/{len(fens)}", file=sys.stderr)
        rows_path = out / f"{args.label}.rows"
        meta_path = out / f"{args.label}.meta"
        raw_path.write_text("\n".join(engine.log) + "\n")
        rows_path.write_text("\n".join(rows) + "\n")
        meta_path.write_text(
            f"exe={args.exe}\nsha256={sha256(args.exe)}\nid_name={name}\n"
            + "option_lines_sent=\n"
            + "\n".join(sent)
            + f"\ndepth={args.depth}\npositions={args.positions}\ncount={len(fens)}\nswitch={args.switch}\n"
        )
        total = sum(int(row.split()[1]) for row in rows)
        first = " ".join(row.split()[1] for row in rows[:3])
        print(f"{args.label} sum {total} first {first} n {len(rows)}")
    except BaseException:
        raw_path.write_text("\n".join(engine.log) + "\n")
        raise
    finally:
        engine.close()


if __name__ == "__main__":
    main()
