#!/usr/bin/env python3
"""Fixed-depth node sum. S14, Threads 1, Hash 16, ucinewgame before every go."""
import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

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

STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_fens(path: Path) -> list[str]:
    fens = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 6:
            fens.append(" ".join(parts[:6]))
        elif len(parts) == 4:
            fens.append(line + " 0 1")
        else:
            raise SystemExit(f"bad fen line: {line}")
    return fens


class Engine:
    def __init__(self, exe: Path):
        self.exe = exe
        self.proc = subprocess.Popen(
            [str(exe)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.lines: list[str] = []

    def send(self, text: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(text + "\n")
        self.proc.stdin.flush()

    def read_until(self, predicate) -> str:
        assert self.proc.stdout is not None
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                raise RuntimeError("engine eof")
            self.lines.append(line)
            for mark in STOP_MARKS:
                if mark in line:
                    raise RuntimeError(line.rstrip("\n"))
            if predicate(line):
                return line

    def close(self) -> None:
        if self.proc.poll() is None:
            try:
                self.send("quit")
            except BrokenPipeError:
                pass
            self.proc.wait(timeout=30)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--positions", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--extra", action="append", default=[], help="name=value set after S14")
    parser.add_argument("--expect-sum", type=int)
    parser.add_argument("--expect-first", default="")
    args = parser.parse_args()

    exe = Path(args.exe).resolve()
    out_dir = Path(__file__).resolve().parent
    fens = load_fens(Path(args.positions))
    extras = []
    for item in args.extra:
        name, value = item.split("=", 1)
        extras.append((name, value))
    expect_first = [int(part) for part in args.expect_first.split(",")] if args.expect_first else []

    id_name = ""
    engine = Engine(exe)
    option_lines = []
    nodes: list[int] = []
    moves: list[str] = []
    try:
        engine.send("uci")
        while True:
            line = engine.read_until(lambda item: item.startswith("uciok") or item.startswith("id name "))
            if line.startswith("id name "):
                id_name = line[len("id name ") :].rstrip("\r\n")
            if line.startswith("uciok"):
                break
        for name, value in S14 + extras:
            command = f"setoption name {name} value {value}"
            option_lines.append(command)
            engine.send(command)
            engine.send("isready")
            engine.read_until(lambda item: item.startswith("readyok"))
        for index, fen in enumerate(fens):
            engine.lines.append(f"# POS {index}\n")
            engine.send("ucinewgame")
            engine.send("isready")
            engine.read_until(lambda item: item.startswith("readyok"))
            engine.send(f"position fen {fen}")
            engine.send("isready")
            engine.read_until(lambda item: item.startswith("readyok"))
            engine.send(f"go depth {args.depth}")
            last_nodes = None
            best = ""
            while True:
                line = engine.read_until(lambda item: item.startswith("info depth ") or item.startswith("bestmove "))
                if line.startswith("info depth "):
                    parts = line.split()
                    last_nodes = int(parts[parts.index("nodes") + 1])
                if line.startswith("bestmove "):
                    best = line.split()[1]
                    break
            if last_nodes is None:
                raise RuntimeError(f"no info nodes for position {index}")
            nodes.append(last_nodes)
            moves.append(best)
            if expect_first and index + 1 == len(expect_first) and nodes != expect_first:
                raise RuntimeError(f"first nodes {nodes} expected {expect_first}")
            if (index + 1) % 50 == 0 or index + 1 == len(fens):
                print(f"{args.tag} {index + 1}/{len(fens)} sum {sum(nodes)}", flush=True)
    finally:
        raw = "".join(engine.lines)
        engine.close()

    raw_path = out_dir / f"{args.tag}.out"
    tsv_path = out_dir / f"{args.tag}.tsv"
    meta_path = out_dir / f"{args.tag}.meta"
    raw_path.write_text(raw)
    tsv_path.write_text("".join(f"{i}\t{nodes[i]}\t{moves[i]}\n" for i in range(len(nodes))))
    meta_path.write_text(
        f"exe={exe}\nsha256={sha256(exe)}\nid_name={id_name}\noptions:\n" + "\n".join(option_lines) + "\n"
    )
    total = sum(nodes)
    print(f"{args.tag} SUM {total} N {len(nodes)}", flush=True)
    if expect_first:
        got = nodes[: len(expect_first)]
        print(f"{args.tag} FIRST {got} expected {expect_first}", flush=True)
        if got != expect_first:
            print(f"{args.tag} FIRST MISMATCH", flush=True)
            return 1
    if args.expect_sum is not None:
        print(f"{args.tag} EXPECT {args.expect_sum}", flush=True)
        if total != args.expect_sum:
            print(f"{args.tag} SUM MISMATCH", flush=True)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
