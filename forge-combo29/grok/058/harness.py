#!/usr/bin/env python3
"""UCI harness for seat 058. Stops on unknown option, invalid value, invalid FEN, illegal move.

Every setoption and every position is followed by isready, and every line up to readyok is read.
Honesty commands use a fresh process and send no setoption.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")

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


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Stop(Exception):
    pass


class Engine:
    def __init__(self, exe: str) -> None:
        self.exe = os.path.realpath(exe)
        self.proc = subprocess.Popen(
            [self.exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.log: list[str] = []
        self.id_name = ""
        self.options: list[str] = []

    def _line(self) -> str:
        assert self.proc.stdout is not None
        raw = self.proc.stdout.readline()
        if raw == "":
            raise Stop("engine closed stdout")
        line = raw.rstrip("\n")
        self.log.append(line)
        lowered = line.lower()
        for token in BAD:
            if token.lower() in lowered:
                raise Stop(line)
        if line.startswith("id name"):
            self.id_name = line
        return line

    def read_until(self, predicate, limit: int = 200000) -> str:
        for _ in range(limit):
            line = self._line()
            if predicate(line):
                return line
        raise Stop("read limit")

    def send(self, command: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(command + "\n")
        self.proc.stdin.flush()

    def ready(self) -> None:
        self.send("isready")
        self.read_until(lambda line: line.strip() == "readyok")

    def handshake(self) -> None:
        self.send("uci")
        self.read_until(lambda line: line.strip() == "uciok")
        self.ready()

    def setoption(self, name: str, value: str) -> None:
        command = f"setoption name {name} value {value}"
        self.options.append(command)
        self.send(command)
        self.ready()

    def quit(self) -> None:
        try:
            if self.proc.poll() is None:
                self.send("quit")
                self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()


def write_meta(path: str, engine: Engine) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(f"exe={engine.exe}\n")
        handle.write(f"sha256={sha256_file(engine.exe)}\n")
        handle.write(f"id_name={engine.id_name}\n")
        handle.write("options:\n")
        for option in engine.options:
            handle.write(option + "\n")


def write_log(path: str, engine: Engine) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(engine.log))
        if engine.log:
            handle.write("\n")


def load_fens(path: str) -> list[str]:
    fens = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text or text.startswith("#"):
                continue
            fens.append(text.split(";")[0].strip())
    return fens


def parse_nodes(line: str) -> int | None:
    parts = line.split()
    for index, part in enumerate(parts):
        if part == "nodes" and index + 1 < len(parts):
            token = parts[index + 1]
            if token.isdigit():
                return int(token)
    return None


def honesty_one(exe: str, command: str, raw_path: str) -> None:
    engine = Engine(exe)
    try:
        engine.handshake()
        engine.send(command)
        if command.startswith("bench"):
            engine.read_until(lambda line: " nodes " in f" {line} " or line.startswith("nodes "))
        else:
            engine.read_until(lambda line: line.startswith("nodes "))
        engine.quit()
    finally:
        write_log(raw_path, engine)
        write_meta(raw_path[:-4] + ".meta" if raw_path.endswith(".txt") else raw_path + ".meta", engine)
        if engine.proc.poll() is None:
            engine.proc.kill()


def run_honesty(exe: str, out_dir: str) -> None:
    jobs = [
        ("bench 11", "honesty_b_bench11.txt", 312866),
        ("bench 13", "honesty_b_bench13.txt", 862329),
        ("bench 16", "honesty_b_bench16.txt", 3024920),
        ("go perft 5", "honesty_b_perft5.txt", 4865609),
    ]
    rows = []
    for command, name, expected in jobs:
        raw = os.path.join(out_dir, name)
        honesty_one(exe, command, raw)
        nodes = None
        with open(raw, encoding="utf-8") as handle:
            for line in handle:
                found = parse_nodes(line.rstrip("\n"))
                if found is not None:
                    nodes = found
        status = "ok" if nodes == expected else "MISS"
        rows.append((command, nodes, expected, status, name))
        print(f"{command} nodes {nodes} expected {expected} {status}", flush=True)
    summary = os.path.join(out_dir, "HONESTY_B.txt")
    with open(summary, "w", encoding="utf-8") as handle:
        handle.write("command\tnodes\texpected\tstatus\traw\n")
        for command, nodes, expected, status, name in rows:
            handle.write(f"{command}\t{nodes}\t{expected}\t{status}\t{name}\n")
    print(f"wrote {summary}", flush=True)


def apply_s14(engine: Engine, extra: list[tuple[str, str]]) -> None:
    for name, value in S14:
        engine.setoption(name, value)
    engine.setoption("Threads", "1")
    engine.setoption("Hash", "16")
    for name, value in extra:
        engine.setoption(name, value)


def run_depth(exe: str, fen_path: str, depth: int, extra: list[tuple[str, str]], raw_path: str, rows_path: str) -> None:
    fens = load_fens(fen_path)
    engine = Engine(exe)
    rows: list[tuple[int, int, str]] = []
    try:
        engine.handshake()
        apply_s14(engine, extra)
        for index, fen in enumerate(fens, start=1):
            engine.send("ucinewgame")
            engine.ready()
            engine.send("position fen " + fen)
            engine.ready()
            engine.send(f"go depth {depth}")
            engine.read_until(lambda line: line.startswith("bestmove "))
            nodes = None
            best = ""
            for line in reversed(engine.log):
                if best == "" and line.startswith("bestmove "):
                    parts = line.split()
                    best = parts[1] if len(parts) > 1 else ""
                if nodes is None and " nodes " in f" {line} ":
                    nodes = parse_nodes(line)
                if nodes is not None and best:
                    break
            if nodes is None:
                raise Stop(f"no nodes for position {index}")
            rows.append((index, nodes, best))
            if index % 50 == 0:
                print(f"{os.path.basename(raw_path)} {index}/{len(fens)}", flush=True)
        engine.quit()
    finally:
        write_log(raw_path, engine)
        write_meta(raw_path[:-4] + ".meta" if raw_path.endswith(".txt") else raw_path + ".meta", engine)
        with open(rows_path, "w", encoding="utf-8") as handle:
            handle.write("index\tnodes\tbestmove\n")
            for index, nodes, best in rows:
                handle.write(f"{index}\t{nodes}\t{best}\n")
        if engine.proc.poll() is None:
            engine.proc.kill()
    total = sum(nodes for _, nodes, _ in rows)
    print(f"{rows_path} positions {len(rows)} sum {total}", flush=True)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: harness.py honesty|depth ...", file=sys.stderr)
        return 2
    mode = sys.argv[1]
    if mode == "honesty":
        run_honesty(sys.argv[2], sys.argv[3])
        return 0
    if mode == "depth":
        # depth EXE FENS DEPTH RAW ROWS [Name=Value ...]
        exe, fens, depth, raw, rows = sys.argv[2:7]
        extra = []
        for item in sys.argv[7:]:
            name, value = item.split("=", 1)
            extra.append((name, value))
        run_depth(exe, fens, int(depth), extra, raw, rows)
        return 0
    print("unknown mode", mode, file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Stop as error:
        print("STOP", error, file=sys.stderr)
        raise SystemExit(1)
