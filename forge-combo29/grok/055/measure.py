#!/usr/bin/env python3
"""Fixed-depth node harness. Stops on unknown option, invalid value, invalid FEN, illegal move."""
import argparse
import hashlib
import queue
import subprocess
import sys
import threading
from pathlib import Path

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")
SAN = ("AddressSanitizer", "UndefinedBehaviorSanitizer", "runtime error:")


class Engine:
    def __init__(self, exe: str):
        self.exe = exe
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.stderr_lines: list[str] = []
        self.sanitizer: list[str] = []
        self.fail: str | None = None
        self.lines: queue.Queue[str | None] = queue.Queue()
        self._out = threading.Thread(target=self._read_out, daemon=True)
        self._err = threading.Thread(target=self._drain, daemon=True)
        self._out.start()
        self._err.start()

    def _read_out(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self.lines.put(line.rstrip("\n"))
        self.lines.put(None)

    def _drain(self) -> None:
        assert self.proc.stderr is not None
        for line in self.proc.stderr:
            self.stderr_lines.append(line)
            if any(mark in line for mark in SAN):
                self.sanitizer.append(line)

    def send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, done, timeout: float) -> list[str]:
        lines: list[str] = []
        while True:
            try:
                line = self.lines.get(timeout=timeout)
            except queue.Empty:
                raise TimeoutError(f"no engine line within {timeout}s; last={lines[-3:]}") from None
            if line is None:
                raise EOFError(f"engine closed stdout; last={lines[-3:]}")
            lines.append(line)
            if any(mark in line for mark in BAD):
                self.fail = line
                raise RuntimeError(line)
            if done(line):
                return lines

    def close(self) -> None:
        try:
            self.send("quit")
        except BrokenPipeError:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_fens(path: Path, limit: int) -> list[str]:
    fens: list[str] = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        fens.append(line)
        if limit and len(fens) >= limit:
            break
    return fens


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--fens", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--meta", required=True)
    parser.add_argument("--stderr", required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--set", dest="sets", nargs=2, action="append", default=[])
    args = parser.parse_args()

    fens = load_fens(Path(args.fens), args.limit)
    engine = Engine(args.exe)
    id_name = ""
    try:
        engine.send("uci")
        uci_lines = engine.read_until(lambda line: line == "uciok", args.timeout)
        for line in uci_lines:
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
        for name, value in args.sets:
            engine.send(f"setoption name {name} value {value}")
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok", args.timeout)
        rows: list[str] = []
        total = 0
        for index, fen in enumerate(fens):
            engine.send("ucinewgame")
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok", args.timeout)
            engine.send(f"position fen {fen}")
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok", args.timeout)
            engine.send(f"go depth {args.depth}")
            played = engine.read_until(lambda line: line.startswith("bestmove "), args.timeout)
            nodes = None
            best = played[-1].split()[1]
            for line in played:
                if " nodes " in line:
                    nodes = int(line.split(" nodes ")[1].split()[0])
            if nodes is None:
                raise RuntimeError(f"no nodes for fen {index}")
            total += nodes
            rows.append(f"{index}\t{nodes}\t{best}\t{fen}")
        out = Path(args.out)
        body = [f"sum\t{total}", f"count\t{len(rows)}", *rows]
        out.write_text("\n".join(body) + "\n")
        print(f"sum {total} positions {len(rows)} out {out}")
    finally:
        engine.close()
        Path(args.stderr).write_text("".join(engine.stderr_lines))
        option_lines = [f"setoption name {name} value {value}" for name, value in args.sets]
        Path(args.meta).write_text(
            "\n".join(
                [
                    f"exe {args.exe}",
                    f"sha256 {sha256(args.exe)}",
                    f"id name {id_name}",
                    *option_lines,
                    f"sanitizer_lines {len(engine.sanitizer)}",
                    f"fail {engine.fail or ''}",
                ]
            )
            + "\n"
        )
        if engine.sanitizer:
            print("SANITIZER", file=sys.stderr)
            print("".join(engine.sanitizer), file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"HARNESS FAIL {exc}", file=sys.stderr)
        raise SystemExit(2)
