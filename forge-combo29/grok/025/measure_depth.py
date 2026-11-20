#!/usr/bin/env python3
"""Depth search over a FEN/EPD list. Raw engine lines go to <stem>.txt."""
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


def load_fens(path: Path) -> list[str]:
    fens = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # EPD may carry opcodes after the 6 FEN fields.
        parts = line.split()
        if len(parts) >= 6:
            fens.append(" ".join(parts[:6]))
        else:
            fens.append(line)
    return fens


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
        self.log: list[str] = []

    def send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.log.append("> " + line)
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, done) -> list[str]:
        assert self.proc.stdout is not None
        got: list[str] = []
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                self.log.append("< EOF")
                raise RuntimeError("engine closed stdout")
            line = line.rstrip("\r\n")
            self.log.append("< " + line)
            got.append(line)
            for bad in BAD:
                if bad in line:
                    raise RuntimeError(line)
            if done(line):
                return got

    def close(self) -> None:
        if self.proc.poll() is None:
            try:
                self.send("quit")
            except BrokenPipeError:
                pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def nodes_of(lines: list[str]) -> int:
    found = None
    for line in lines:
        if line.startswith("info ") and " nodes " in line and "currmove" not in line:
            parts = line.split()
            try:
                found = int(parts[parts.index("nodes") + 1])
            except (ValueError, IndexError):
                continue
    if found is None:
        raise RuntimeError("no nodes on info line")
    return found


def bestmove_of(lines: list[str]) -> str:
    for line in lines:
        if line.startswith("bestmove "):
            return line.split()[1]
    raise RuntimeError("no bestmove")


def main() -> int:
    if len(sys.argv) != 6:
        print("usage: measure_depth.py EXE FENS DEPTH STEM EXTRA_OPTIONS", file=sys.stderr)
        print("EXTRA_OPTIONS is a comma list name=value or -", file=sys.stderr)
        return 2
    exe = Path(sys.argv[1]).resolve()
    fens = load_fens(Path(sys.argv[2]))
    depth = int(sys.argv[3])
    stem = Path(sys.argv[4])
    extra_text = sys.argv[5]
    extra: list[tuple[str, str]] = []
    if extra_text != "-":
        for item in extra_text.split(","):
            name, value = item.split("=", 1)
            extra.append((name, value))
    options = S14 + extra
    engine = Engine(exe)
    try:
        engine.send("uci")
        uci_lines = engine.read_until(lambda line: line == "uciok")
        id_name = ""
        for line in uci_lines:
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
        engine.send("isready")
        engine.read_until(lambda line: line == "readyok")
        rows = []
        for index, fen in enumerate(fens, start=1):
            for name, value in options:
                engine.send(f"setoption name {name} value {value}")
                engine.send("isready")
                engine.read_until(lambda line: line == "readyok")
            engine.send("ucinewgame")
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok")
            engine.send(f"position fen {fen}")
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok")
            engine.send(f"go depth {depth}")
            played = engine.read_until(lambda line: line.startswith("bestmove "))
            nodes = nodes_of(played)
            move = bestmove_of(played)
            rows.append((index, nodes, move, fen))
            print(f"{index} {nodes} {move}", flush=True)
    finally:
        engine.close()
    stem.parent.mkdir(parents=True, exist_ok=True)
    stem.with_suffix(".txt").write_text("\n".join(engine.log) + "\n")
    parsed = stem.with_suffix(".rows")
    parsed.write_text("".join(f"{i}\t{n}\t{m}\t{fen}\n" for i, n, m, fen in rows))
    total = sum(n for _, n, _, _ in rows)
    meta = [
        f"exe {exe}",
        f"sha256 {sha256(exe)}",
        f"id_name {id_name}",
        "options",
    ]
    meta.extend(f"setoption name {name} value {value}" for name, value in options)
    meta.append(f"depth {depth}")
    meta.append(f"positions {len(rows)}")
    meta.append(f"nodes_sum {total}")
    if rows:
        meta.append("first3 " + " ".join(str(rows[i][1]) for i in range(min(3, len(rows)))))
    stem.with_suffix(".meta").write_text("\n".join(meta) + "\n")
    print(f"SUM {total} N {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
