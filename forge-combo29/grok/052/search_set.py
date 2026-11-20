#!/usr/bin/env python3
"""Depth search of a FEN/EPD list. One engine process. S14, then Threads, Hash, then each position."""
import argparse
import hashlib
import pathlib
import re
import subprocess
import time

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

STOP_PHRASES = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fen_of(line: str) -> str:
    parts = line.strip().split()
    if not parts or parts[0].startswith("#"):
        return ""
    if len(parts) >= 6 and parts[1] in ("w", "b") and parts[4].isdigit() and parts[5].isdigit():
        return " ".join(parts[:6])
    if len(parts) >= 4 and parts[1] in ("w", "b"):
        return " ".join(parts[:4]) + " 0 1"
    return line.strip()


class Engine:
    def __init__(self, exe: str):
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.log: list[str] = []

    def send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()
        self.log.append(">> " + line + "\n")

    def read_until(self, done, timeout: float) -> list[str]:
        assert self.proc.stdout is not None
        lines: list[str] = []
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            line = self.proc.stdout.readline()
            if line == "":
                raise SystemExit("engine closed stdout\n" + "".join(self.log[-30:]))
            self.log.append(line)
            lines.append(line)
            low = line.lower()
            for phrase in STOP_PHRASES:
                if phrase.lower() in low:
                    raise SystemExit(f"STOP {phrase}: {line}")
            if done(line):
                return lines
        raise SystemExit("timeout waiting for engine\n" + "".join(lines[-20:]))

    def close(self) -> str:
        try:
            self.send("quit")
        except BrokenPipeError:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        err = ""
        if self.proc.stderr is not None:
            err = self.proc.stderr.read()
        return err


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--fens", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--switch", choices=("omit", "false", "true"), default="omit")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    repo = pathlib.Path(pathlib.Path.home().joinpath("grok_repo.txt").read_text().strip())
    seat = pathlib.Path.home().joinpath("grok_seat.txt").read_text().strip()
    out_dir = repo / "forge-combo29" / "grok" / seat
    exe = pathlib.Path(args.exe).resolve()
    fens = [fen_of(line) for line in pathlib.Path(args.fens).read_text().splitlines()]
    fens = [fen for fen in fens if fen]
    if args.limit:
        fens = fens[: args.limit]

    options = list(S14)
    if args.switch != "omit":
        options.append(("IdeaS28", args.switch))

    engine = Engine(str(exe))
    engine.send("uci")
    uci_lines = engine.read_until(lambda line: line.startswith("uciok"), 30)
    id_match = re.search(r"^id name (.+)$", "".join(uci_lines), re.M)
    id_name = id_match.group(1).strip() if id_match else "MISSING"
    engine.send("isready")
    engine.read_until(lambda line: line.startswith("readyok"), 30)
    sent = []
    for name, value in options:
        line = f"setoption name {name} value {value}"
        sent.append(line)
        engine.send(line)
        engine.send("isready")
        engine.read_until(lambda item: item.startswith("readyok"), 30)

    rows = []
    total = 0
    for index, fen in enumerate(fens, start=1):
        engine.send("ucinewgame")
        engine.send("isready")
        engine.read_until(lambda line: line.startswith("readyok"), 30)
        engine.send("position fen " + fen)
        engine.send("isready")
        engine.read_until(lambda line: line.startswith("readyok"), 30)
        engine.send(f"go depth {args.depth}")
        go_lines = engine.read_until(lambda line: line.startswith("bestmove"), 180)
        nodes = None
        for line in go_lines:
            match = re.search(r"\bnodes (\d+)", line)
            if match and line.startswith("info "):
                nodes = int(match.group(1))
        if nodes is None:
            raise SystemExit(f"no nodes for position {index}\n" + "".join(go_lines))
        best = ""
        for line in go_lines:
            if line.startswith("bestmove"):
                best = line.split()[1]
        total += nodes
        rows.append(f"{index}\t{nodes}\t{best}\t{fen}")
        print(f"{index}\t{nodes}\t{total}", flush=True)

    err = engine.close()
    prefix = out_dir / args.out
    prefix.with_suffix(".txt").write_text("".join(engine.log))
    (out_dir / f"{args.out}.rows").write_text("\n".join(rows) + "\n")
    if err:
        (out_dir / f"{args.out}.err").write_text(err)
    meta = [
        f"exe={exe}",
        f"sha256={sha256(exe)}",
        f"id_name={id_name}",
        "options_sent:",
        *sent,
        f"depth={args.depth}",
        f"positions={len(fens)}",
        f"node_sum={total}",
        f"fens={args.fens}",
        "",
    ]
    (out_dir / f"{args.out}.meta").write_text("\n".join(meta))
    print(f"SUM {total}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
