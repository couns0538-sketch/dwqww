#!/usr/bin/env python3
"""Depth-search harness.

Sends S14, then Threads and Hash, then any extra options. After every setoption
and every position it sends isready and reads every line up to readyok.
Stops on unknown option, invalid value, invalid FEN, or illegal move.
One fresh engine process per invocation. ucinewgame + isready before every go.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import os
import pathlib
import select
import subprocess
import sys

S14 = [
    "setoption name LmrQuietBase value 93",
    "setoption name LmrQuietDivisor value 205",
    "setoption name LmrNoisyBase value 13",
    "setoption name LmrNoisyDivisor value 333",
    "setoption name LmrHistoryDivisor value 5643",
    "setoption name NullMoveBase value 5",
    "setoption name LmpBase value 8",
    "setoption name HistoryPruneMultiplier value 2220",
    "setoption name HistoryBonusQuadratic value 24",
    "setoption name HistoryBonusLinear value 54",
    "setoption name HistoryBonusMax value 2212",
    "setoption name SingularDepth value 6",
    "setoption name IirDepth value 2",
    "setoption name NonPawnCorrection value true",
]
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class StopHarness(Exception):
    pass


class Engine:
    def __init__(self, exe: str) -> None:
        self.exe = exe
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        self.stdout_buf = b""
        self.stderr_chunks: list[bytes] = []

    def send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def read_line(self, timeout: float) -> str:
        assert self.proc.stdout is not None and self.proc.stderr is not None
        while b"\n" not in self.stdout_buf:
            ready, _, _ = select.select([self.proc.stdout, self.proc.stderr], [], [], timeout)
            if not ready:
                err = b"".join(self.stderr_chunks).decode("utf-8", "replace")
                raise StopHarness(f"timeout waiting for engine output; stderr_tail={err[-2000:]!r}")
            if self.proc.stderr in ready:
                chunk = os.read(self.proc.stderr.fileno(), 65536)
                if chunk:
                    self.stderr_chunks.append(chunk)
            if self.proc.stdout in ready:
                chunk = os.read(self.proc.stdout.fileno(), 65536)
                if chunk == b"" and self.proc.poll() is not None and b"\n" not in self.stdout_buf:
                    err = b"".join(self.stderr_chunks).decode("utf-8", "replace")
                    raise StopHarness(f"engine exited code {self.proc.returncode}; stderr_tail={err[-2000:]!r}")
                self.stdout_buf += chunk
        line, self.stdout_buf = self.stdout_buf.split(b"\n", 1)
        text = line.decode("utf-8", "replace").rstrip("\r")
        for bad in BAD:
            if bad in text:
                raise StopHarness(f"stop phrase {bad!r} in line: {text}")
        return text

    def read_until(self, marker: str, timeout: float) -> list[str]:
        lines: list[str] = []
        while True:
            line = self.read_line(timeout)
            lines.append(line)
            if line == marker or line.startswith(marker + " "):
                return lines

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
        else:
            self.proc.wait(timeout=5)

    def stderr_text(self) -> str:
        if self.proc.stderr is not None:
            try:
                flags = fcntl.fcntl(self.proc.stderr.fileno(), fcntl.F_GETFL)
                fcntl.fcntl(self.proc.stderr.fileno(), fcntl.F_SETFL, flags | os.O_NONBLOCK)
                while True:
                    rest = os.read(self.proc.stderr.fileno(), 65536)
                    if not rest:
                        break
                    self.stderr_chunks.append(rest)
            except OSError:
                pass
        return b"".join(self.stderr_chunks).decode("utf-8", "replace")


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def id_name(exe: str) -> str:
    proc = subprocess.run(
        [exe],
        input="uci\nquit\n",
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    for line in proc.stdout.splitlines():
        if line.startswith("id name "):
            return line[len("id name ") :]
    raise StopHarness("no id name from exe")


def load_fens(path: pathlib.Path, limit: int) -> list[str]:
    fens = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        fens.append(line)
        if limit and len(fens) >= limit:
            break
    return fens


def last_nodes(lines: list[str]) -> tuple[str, str, str]:
    nodes = ""
    score = ""
    depth = ""
    for line in lines:
        if not line.startswith("info depth "):
            continue
        parts = line.split()
        if "nodes" in parts:
            nodes = parts[parts.index("nodes") + 1]
        if "score" in parts:
            i = parts.index("score")
            score = " ".join(parts[i + 1 : i + 3]) if i + 2 < len(parts) else parts[i + 1]
        if "depth" in parts:
            depth = parts[parts.index("depth") + 1]
    best = ""
    for line in lines:
        if line.startswith("bestmove "):
            best = line.split()[1]
    return nodes, best, f"depth={depth} score={score}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--fens", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--extra", action="append", default=[])
    parser.add_argument("--go-timeout", type=float, default=120.0)
    args = parser.parse_args()

    folder = pathlib.Path(__file__).resolve().parent
    fens = load_fens(pathlib.Path(args.fens), args.limit)
    exe = str(pathlib.Path(args.exe).resolve())
    digest = sha256_file(exe)
    name = id_name(exe)
    options = list(S14) + ["setoption name Threads value 1", "setoption name Hash value 16"] + list(args.extra)

    engine = Engine(exe)
    transcript: list[str] = []
    rows: list[str] = []
    try:
        engine.send("uci")
        transcript.append(">> uci")
        for line in engine.read_until("uciok", 30):
            transcript.append(line)
        engine.send("isready")
        transcript.append(">> isready")
        for line in engine.read_until("readyok", 30):
            transcript.append(line)
        for fen_index, fen in enumerate(fens):
            engine.send("ucinewgame")
            transcript.append(">> ucinewgame")
            engine.send("isready")
            transcript.append(">> isready")
            for line in engine.read_until("readyok", 30):
                transcript.append(line)
            for option in options:
                engine.send(option)
                transcript.append(">> " + option)
                engine.send("isready")
                transcript.append(">> isready")
                for line in engine.read_until("readyok", 30):
                    transcript.append(line)
            engine.send("position fen " + fen)
            transcript.append(">> position fen " + fen)
            engine.send("isready")
            transcript.append(">> isready")
            for line in engine.read_until("readyok", 30):
                transcript.append(line)
            go = f"go depth {args.depth}"
            engine.send(go)
            transcript.append(">> " + go)
            got = engine.read_until("bestmove", args.go_timeout)
            transcript.extend(got)
            nodes, best, detail = last_nodes(got)
            if not nodes.isdigit():
                raise StopHarness(f"no nodes for fen {fen_index}: {got[-5:]!r}")
            rows.append(f"{fen_index} {nodes} {best} {detail} {fen}")
            if (fen_index + 1) % 25 == 0 or fen_index + 1 == len(fens):
                print(f"{args.label} {fen_index + 1}/{len(fens)}", file=sys.stderr, flush=True)
    finally:
        err = ""
        try:
            engine.close()
            err = engine.stderr_text()
        except Exception as exc:
            err = f"close failed: {exc}"
        (folder / f"{args.label}.txt").write_text("\n".join(transcript) + "\n")
        (folder / f"{args.label}.rows").write_text("\n".join(rows) + ("\n" if rows else ""))
        (folder / f"{args.label}.err").write_text(err)
        meta = [
            f"exe={exe}",
            f"sha256={digest}",
            f"id_name={name}",
            "id_name_source=separate uci/quit of the same exe path",
            f"depth={args.depth}",
            f"fens={args.fens}",
            f"positions={len(fens)}",
            "options_sent:",
            *options,
        ]
        (folder / f"{args.label}.meta").write_text("\n".join(meta) + "\n")
    total = sum(int(row.split()[1]) for row in rows)
    print(f"{args.label} positions {len(rows)} nodes {total}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except StopHarness as exc:
        print(f"HARNESS_STOP {exc}", file=sys.stderr)
        raise SystemExit(2)
