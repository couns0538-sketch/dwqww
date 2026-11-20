#!/usr/bin/env python3
"""Fixed-depth node sum. One engine process. Stops on a bad UCI reply.

S14 is sent once, in the brief's order, then any extra setoption arguments.
ucinewgame and isready come before every go. isready is also sent after every
setoption and every position, and every line up to readyok is kept.
"""
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
]

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe: str):
        self.exe = exe
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.log: list[str] = []

    def send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, done) -> list[str]:
        assert self.proc.stdout is not None
        got: list[str] = []
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                self.log.extend(got)
                raise SystemExit("engine closed stdout")
            line = line.rstrip("\r\n")
            got.append(line)
            self.log.append(line)
            for bad in BAD:
                if bad in line:
                    raise SystemExit(f"STOP {bad}: {line}")
            if done(line):
                return got

    def close(self) -> None:
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()


def load_fens(path: Path) -> list[str]:
    fens = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 6:
            raise SystemExit(f"short FEN: {line}")
        fens.append(" ".join(parts[:6]))
    return fens


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--fens", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--setoption", action="append", default=[])
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    exe = str(Path(args.exe).resolve())
    fens = load_fens(Path(args.fens))
    if args.limit:
        fens = fens[: args.limit]
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    extra = []
    for item in args.setoption:
        if "=" not in item:
            raise SystemExit(f"bad setoption {item}")
        name, value = item.split("=", 1)
        extra.append((name, value))

    eng = Engine(exe)
    failed = None
    id_name = ""
    sent: list[str] = []
    rows: list[tuple[int, int, str, str]] = []
    try:
        eng.send("uci")
        ident = eng.read_until(lambda line: line == "uciok")
        for line in ident:
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
        options = [("Hash", "16"), ("Threads", "1"), *S14, *extra]
        for name, value in options:
            line = f"setoption name {name} value {value}"
            sent.append(line)
            eng.send(line)
            eng.send("isready")
            eng.read_until(lambda row: row == "readyok")
        for index, fen in enumerate(fens):
            eng.send("ucinewgame")
            eng.send("isready")
            eng.read_until(lambda row: row == "readyok")
            eng.send(f"position fen {fen}")
            eng.send("isready")
            eng.read_until(lambda row: row == "readyok")
            eng.send(f"go depth {args.depth}")
            lines = eng.read_until(lambda row: row.startswith("bestmove "))
            nodes = None
            for line in lines:
                if " nodes " in f" {line} ":
                    parts = line.split()
                    if "nodes" in parts:
                        nodes = int(parts[parts.index("nodes") + 1])
            if nodes is None:
                raise SystemExit(f"no nodes for fen {index}")
            best = lines[-1].split()[1]
            rows.append((index, nodes, best, fen))
            print(f"{index} {nodes} {best}", flush=True)
    except SystemExit as exc:
        failed = exc
    finally:
        eng.close()

    prefix = Path(args.prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    prefix.with_suffix(".log").write_text("\n".join(eng.log) + "\n")
    prefix.with_suffix(".nodes").write_text("".join(f"{nodes}\n" for _, nodes, _, _ in rows))
    prefix.with_suffix(".rows").write_text(
        "".join(f"{index}\t{nodes}\t{best}\t{fen}\n" for index, nodes, best, fen in rows)
    )
    meta = [
        f"exe={exe}",
        f"sha256={sha}",
        f"id_name={id_name}",
        f"depth={args.depth}",
        f"fens={args.fens}",
        f"positions={len(rows)}",
        f"node_sum={sum(nodes for _, nodes, _, _ in rows)}",
    ]
    meta.extend(f"option={line}" for line in sent)
    prefix.with_suffix(".meta").write_text("\n".join(meta) + "\n")
    print(f"SUM {sum(nodes for _, nodes, _, _ in rows)} N {len(rows)}", flush=True)
    if failed is not None:
        raise failed


if __name__ == "__main__":
    try:
        main()
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        raise
