#!/usr/bin/env python3
"""Depth search of a FEN/EPD list. Stops on unknown option, invalid value, invalid FEN, illegal move."""
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

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_positions(path: Path):
    rows = []
    for line in path.read_text().splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        rows.append(text.split(";")[0].strip())
    return rows


class Engine:
    def __init__(self, exe: Path):
        self.proc = subprocess.Popen(
            [str(exe)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.lines = []

    def send(self, command: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(command + "\n")
        self.proc.stdin.flush()

    def read_until(self, predicate, limit: int = 200000) -> list[str]:
        assert self.proc.stdout is not None
        got = []
        while len(got) < limit:
            line = self.proc.stdout.readline()
            if line == "":
                raise SystemExit("engine closed stdout early")
            line = line.rstrip("\n")
            got.append(line)
            self.lines.append(line)
            lowered = line.lower()
            for bad in BAD:
                if bad.lower() in lowered:
                    raise SystemExit(f"STOP {bad}: {line}")
            if predicate(line):
                return got
        raise SystemExit("too many lines without the expected reply")

    def close(self) -> None:
        if self.proc.poll() is None:
            try:
                self.send("quit")
            except BrokenPipeError:
                pass
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()


def option_lines(extra: list[tuple[str, str]]) -> list[str]:
    return [f"setoption name {name} value {value}" for name, value in S14 + extra]


def id_name(exe: Path) -> str:
    completed = subprocess.run(
        [str(exe)],
        input="uci\nquit\n",
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    for line in completed.stdout.splitlines():
        if line.startswith("id name "):
            return line[len("id name "):]
    return ""


def nodes_of(chunk: list[str], depth: int) -> int:
    found = None
    for line in chunk:
        if f"depth {depth} " in line and " nodes " in line:
            found = int(line.split(" nodes ", 1)[1].split()[0])
        elif line.startswith("bestmove") and found is None:
            break
    if found is None:
        for line in chunk:
            if line.startswith("info depth ") and " nodes " in line:
                found = int(line.split(" nodes ", 1)[1].split()[0])
    if found is None:
        raise SystemExit("no nodes in search output:\n" + "\n".join(chunk[-20:]))
    return found


def bestmove_of(chunk: list[str]) -> str:
    for line in chunk:
        if line.startswith("bestmove "):
            return line.split()[1]
    return ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--positions", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--extra", action="append", default=[], help="name=value after S14")
    args = parser.parse_args()

    exe = Path(args.exe)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    extra = []
    for item in args.extra:
        name, value = item.split("=", 1)
        extra.append((name, value))
    positions = load_positions(Path(args.positions))
    if args.limit:
        positions = positions[: args.limit]
    digest = sha256(exe)
    name = id_name(exe)
    sent = option_lines(extra)
    meta = [f"exe={exe}", f"sha256={digest}", f"id_name={name}", f"depth={args.depth}", f"positions={len(positions)}"]
    meta.extend(f"option={line}" for line in sent)
    (out / f"{args.label}.meta").write_text("\n".join(meta) + "\n")

    raw_path = out / f"{args.label}.txt"
    nodes_path = out / f"{args.label}.nodes"
    engine = Engine(exe)
    node_rows = []
    try:
        def command_and_ready(command: str) -> None:
            engine.send(command)
            engine.send("isready")
            engine.read_until(lambda row: row == "readyok")

        for line in sent:
            command_and_ready(line)
        with raw_path.open("w") as raw:
            for index, fen in enumerate(positions):
                command_and_ready("ucinewgame")
                command_and_ready(f"position fen {fen}")
                engine.send(f"go depth {args.depth}")
                chunk = engine.read_until(lambda row: row.startswith("bestmove "))
                count = nodes_of(chunk, args.depth)
                move = bestmove_of(chunk)
                raw.write(f"# pos {index}\n")
                raw.write("\n".join(chunk) + "\n")
                node_rows.append(f"{index}\t{count}\t{move}")
                if (index + 1) % 25 == 0:
                    print(f"{args.label} {index + 1}/{len(positions)}", flush=True)
    finally:
        engine.close()
    nodes_path.write_text("\n".join(node_rows) + "\n")
    counts = [int(row.split("\t")[1]) for row in node_rows]
    first = " ".join(str(value) for value in counts[:3])
    print(f"SUM {args.label} {sum(counts)} N {len(counts)} FIRST {first}")


if __name__ == "__main__":
    main()
