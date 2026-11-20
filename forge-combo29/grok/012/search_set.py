#!/usr/bin/env python3
"""Depth search of a FEN/EPD list. One engine process. S14, then Threads, Hash, then extra options.

Stops on unknown option, invalid value, invalid FEN, or illegal move.
Writes the raw engine transcript, one row per position, and a .meta file.
"""
import hashlib
import subprocess
import sys
import time
from pathlib import Path

STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")
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


def load_fens(path: Path) -> list[str]:
    fens = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 6:
            fens.append(" ".join(parts[:6]))
        elif len(parts) >= 4:
            fens.append(" ".join(parts[:4]) + " 0 1")
        else:
            raise SystemExit(f"bad position line: {line}")
    return fens


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def id_name(exe: str) -> str:
    proc = subprocess.run([exe], input="uci\nquit\n", text=True, capture_output=True, check=False)
    for line in proc.stdout.splitlines():
        if line.startswith("id name "):
            return line[len("id name "):]
    raise SystemExit("no id name")


class Engine:
    def __init__(self, exe: str):
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

    def read_until(self, done, timeout: float) -> str:
        assert self.proc.stdout is not None
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            line = self.proc.stdout.readline()
            if line == "":
                raise SystemExit("engine closed stdout\n" + "\n".join(self.log[-30:]))
            line = line.rstrip("\r\n")
            self.log.append(line)
            for mark in STOP_MARKS:
                if mark in line:
                    raise SystemExit(f"STOP {mark}: {line}")
            if done(line):
                return line
        raise SystemExit("timeout\n" + "\n".join(self.log[-30:]))

    def ready(self) -> None:
        self.send("isready")
        self.read_until(lambda line: line == "readyok", 60)

    def close(self) -> None:
        try:
            self.send("quit")
            self.proc.wait(timeout=15)
        except Exception:
            self.proc.kill()


def parse_last_info(lines: list[str]) -> tuple[str, str, str]:
    nodes = score = best = ""
    for line in lines:
        if line.startswith("info depth ") and " nodes " in line and " score " in line:
            parts = line.split()
            if "nodes" in parts:
                nodes = parts[parts.index("nodes") + 1]
            if "score" in parts:
                kind = parts[parts.index("score") + 1]
                value = parts[parts.index("score") + 2]
                score = kind + " " + value
        if line.startswith("bestmove "):
            best = line.split()[1]
    if not nodes or not best:
        raise SystemExit("missing nodes or bestmove\n" + "\n".join(lines[-20:]))
    return nodes, score, best


def main() -> None:
    if len(sys.argv) < 5:
        raise SystemExit("usage: search_set.py EXE POSITIONS DEPTH OUT_PREFIX [Name Value ...]")
    exe, positions, depth_text, out_prefix = sys.argv[1:5]
    depth = int(depth_text)
    extras = sys.argv[5:]
    if len(extras) % 2 != 0:
        raise SystemExit("extra options must be Name Value pairs")
    extra_pairs = list(zip(extras[0::2], extras[1::2]))
    fens = load_fens(Path(positions))
    exe_path = str(Path(exe).resolve())
    options = S14 + extra_pairs
    meta_lines = [
        f"exe={exe_path}",
        f"sha256={sha256(Path(exe_path))}",
        f"id_name={id_name(exe_path)}",
        f"positions={Path(positions).resolve()}",
        f"count={len(fens)}",
        f"depth={depth}",
        "options_sent:",
    ]
    meta_lines.extend(f"setoption name {name} value {value}" for name, value in options)
    nm = subprocess.run(["nm", "-C", exe_path], capture_output=True, text=True, check=False)
    asan_count = sum(1 for line in nm.stdout.splitlines() if "__asan_" in line)
    meta_lines.append(f"nm_command=nm -C {exe_path} | grep -c __asan_")
    meta_lines.append(f"nm_asan_count={asan_count}")
    Path(out_prefix + ".meta").write_text("\n".join(meta_lines) + "\n")

    engine = Engine(exe_path)
    try:
        for name, value in options:
            engine.send(f"setoption name {name} value {value}")
            engine.ready()
        rows = []
        for index, fen in enumerate(fens, start=1):
            mark = len(engine.log)
            engine.send("ucinewgame")
            engine.ready()
            engine.send(f"position fen {fen}")
            engine.ready()
            engine.send(f"go depth {depth}")
            engine.read_until(lambda line: line.startswith("bestmove "), 180)
            nodes, score, best = parse_last_info(engine.log[mark:])
            rows.append(f"{index}\t{nodes}\t{score}\t{best}\t{fen}")
            if index % 25 == 0:
                print(f"done {index}/{len(fens)}", file=sys.stderr, flush=True)
    finally:
        Path(out_prefix + ".raw.txt").write_text("\n".join(engine.log) + "\n")
        engine.close()
    Path(out_prefix + ".rows.txt").write_text("\n".join(rows) + "\n")
    print(f"WROTE {len(rows)} {out_prefix}")


if __name__ == "__main__":
    main()
