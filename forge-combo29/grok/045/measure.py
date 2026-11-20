#!/usr/bin/env python3
"""Depth search of a FEN list. One engine process.

Before every go: S14, Threads 1, Hash 16, then ucinewgame, then position.
isready after every setoption and every position. Stops on a bad engine line.
"""
import hashlib
import re
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
NODES_RE = re.compile(r"\bnodes (\d+)")


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
        if len(parts) < 6:
            raise SystemExit(f"short fen line: {line}")
        fens.append(" ".join(parts[:6]))
    return fens


class Engine:
    def __init__(self, exe: Path) -> None:
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
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()
        self.log.append(">> " + line + "\n")

    def read_until(self, token: str) -> list[str]:
        assert self.proc.stdout is not None
        got: list[str] = []
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                raise SystemExit("engine closed stdout\n" + "".join(self.log[-30:]))
            self.log.append(line)
            got.append(line)
            for mark in STOP_MARKS:
                if mark in line:
                    raise SystemExit(f"STOP {mark}: {line}")
            if line.strip() == token or line.startswith(token + " "):
                return got

    def close(self) -> None:
        if self.proc.poll() is None:
            try:
                self.send("quit")
            except BrokenPipeError:
                pass
        self.proc.wait(timeout=30)


def main() -> None:
    if len(sys.argv) != 6:
        raise SystemExit("usage: measure.py <exe> <fen-file> <depth> <out-prefix> <extra-setoption-lines-file-or-dash>")
    exe = Path(sys.argv[1]).resolve()
    fen_file = Path(sys.argv[2]).resolve()
    depth = int(sys.argv[3])
    prefix = Path(sys.argv[4]).resolve()
    extra_path = sys.argv[5]
    extras: list[str] = []
    if extra_path != "-":
        extras = [line.strip() for line in Path(extra_path).read_text().splitlines() if line.strip()]
    fens = load_fens(fen_file)
    engine = Engine(exe)
    id_name = ""
    rows: list[tuple[int, int, str]] = []
    failed: BaseException | None = None
    try:
        engine.send("uci")
        for line in engine.read_until("uciok"):
            if line.startswith("id name "):
                id_name = line.strip()
        rows = []
        for index, fen in enumerate(fens):
            for name, value in S14:
                engine.send(f"setoption name {name} value {value}")
                engine.send("isready")
                engine.read_until("readyok")
            for line in extras:
                engine.send(line)
                engine.send("isready")
                engine.read_until("readyok")
            engine.send("ucinewgame")
            engine.send("isready")
            engine.read_until("readyok")
            engine.send(f"position fen {fen}")
            engine.send("isready")
            engine.read_until("readyok")
            engine.send(f"go depth {depth}")
            chunk = engine.read_until("bestmove")
            nodes = None
            best = ""
            for line in chunk:
                found = NODES_RE.findall(line)
                if found and line.startswith("info "):
                    nodes = int(found[-1])
                if line.startswith("bestmove "):
                    best = line.split()[1]
            if nodes is None:
                raise SystemExit(f"no nodes for position {index}")
            rows.append((index, nodes, best))
            print(f"{index} {nodes} {best}", flush=True)
    except BaseException as exc:
        failed = exc
    finally:
        try:
            engine.close()
        except BaseException:
            pass
    prefix.parent.mkdir(parents=True, exist_ok=True)
    raw_path = prefix.with_suffix(".raw.txt")
    rows_path = prefix.with_suffix(".rows.txt")
    meta_path = prefix.with_suffix(".meta")
    raw_path.write_text("".join(engine.log))
    rows_path.write_text("".join(f"{index} {nodes} {best}\n" for index, nodes, best in rows))
    option_lines = [f"setoption name {name} value {value}" for name, value in S14] + extras
    meta_path.write_text(
        f"exe={exe}\n"
        f"sha256={sha256(exe)}\n"
        f"id_name={id_name}\n"
        f"fen_file={fen_file}\n"
        f"depth={depth}\n"
        f"positions={len(fens)}\n"
        "options_sent:\n" + "\n".join(option_lines) + "\n"
    )
    total = sum(nodes for _index, nodes, _best in rows)
    print(f"SUM {total} N {len(rows)}")
    if failed is not None:
        raise failed


if __name__ == "__main__":
    main()
