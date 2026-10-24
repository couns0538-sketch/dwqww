#!/usr/bin/env python3
"""Portable, standard-library-only actual-UCI exchange capture."""
from __future__ import annotations

import argparse
import queue
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path


class Engine:
    def __init__(self, executable: Path, cpu: int | None = None):
        command = [str(executable.resolve())]
        if cpu is not None:
            taskset = shutil.which("taskset")
            if taskset is None:
                raise RuntimeError("--cpu requires taskset; omit --cpu for portable execution")
            command = [taskset, "-c", str(cpu), *command]
        self.origin = time.monotonic()
        self.raw: list[str] = []
        self.lines: list[str] = []
        self.pending: queue.Queue[str | None] = queue.Queue()
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        text=True, bufsize=1)
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def record(self, marker: str, line: str):
        self.raw.append(f"{time.monotonic() - self.origin:.6f} {marker} {line}")

    def _read(self):
        assert self.process.stdout is not None
        for line in self.process.stdout:
            line = line.rstrip("\r\n")
            self.lines.append(line)
            self.record("<", line)
            self.pending.put(line)
        self.pending.put(None)

    def send(self, command: str):
        assert self.process.stdin is not None
        self.record(">", command)
        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()

    def until(self, prefix: str, timeout: float = 20.0):
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AssertionError(f"response timeout waiting for {prefix!r}")
            try:
                line = self.pending.get(timeout=remaining)
            except queue.Empty as error:
                raise AssertionError(f"response timeout waiting for {prefix!r}") from error
            if line is None:
                raise AssertionError(f"engine exited before {prefix!r}")
            if line.startswith(prefix):
                return

    def close(self):
        if self.process.poll() is None:
            self.send("quit")
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
                raise AssertionError("engine did not exit after quit")
        self.reader.join(timeout=5)
        self.record("=", f"exit {self.process.returncode}")
        if self.reader.is_alive():
            raise AssertionError("output reader did not finish")
        if self.process.returncode != 0:
            raise AssertionError(f"engine exited {self.process.returncode}")


def capture(executable: Path, position: str, go: str, log: Path,
            options: list[str] | None = None, cpu: int | None = None) -> dict:
    engine = Engine(executable, cpu)
    try:
        engine.send("uci")
        engine.until("uciok")
        for option in ["Threads value 1", "Hash value 16", "OwnBook value false", *(options or [])]:
            engine.send("setoption name " + option)
        engine.send("ucinewgame")
        engine.send("isready")
        engine.until("readyok")
        engine.send("position " + position)
        engine.send("go " + go)
        engine.until("bestmove ")
    finally:
        try:
            engine.close()
        finally:
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text("\n".join(engine.raw) + "\n", encoding="utf-8")
    infos = []
    for line in engine.lines:
        if not line.startswith("info depth "):
            continue
        match = re.fullmatch(r"info depth (\d+) .*? score (cp|mate) (-?\d+) nodes (\d+) .*? pv(?: (.*))?", line)
        if match is None:
            raise AssertionError(f"unrecognized info record: {line!r}")
        infos.append({"depth": int(match[1]), "score_kind": match[2], "score": int(match[3]),
                      "nodes": int(match[4]), "pv": (match[5] or "").split(), "raw": line})
    best_lines = [line for line in engine.lines if line.startswith("bestmove ")]
    if len(best_lines) != 1:
        raise AssertionError(f"expected one bestmove, got {best_lines!r}")
    best = best_lines[0].split()
    summary = dict(infos[-1]) if infos else {"depth": 0, "score_kind": None, "score": None,
                                                   "nodes": None, "pv": [], "raw": None}
    summary.update(best=best[1], ponder=best[3] if len(best) == 4 and best[2] == "ponder" else None,
                   infos=infos, exit=engine.process.returncode)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--position", default="startpos")
    parser.add_argument("--go", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--option", action="append", default=[])
    parser.add_argument("--cpu", type=int)
    args = parser.parse_args()
    result = capture(args.engine, args.position, args.go, args.out, args.option, args.cpu)
    import json
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
