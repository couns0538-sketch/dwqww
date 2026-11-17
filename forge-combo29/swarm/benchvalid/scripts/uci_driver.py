#!/usr/bin/env python3
"""A UCI driver that never queues a command behind a live search.

The brief's rule 1: `printf '...\ngo depth 8\nquit\\n' | ./forge` makes the engine
abort and FABRICATE a bestmove with zero info lines. Every scripted command here is
written, then the driver READS until `bestmove` (or `readyok`, for isready) before the
next write. `quit` is only ever sent when no search is running.

Measured in this seat: the naive pipe form returns `bestmove a2a3` for the kiwipete FEN
at depth 13 with ZERO `info depth` lines, where this driver returns `e2a6` with 13 of
them. scripts/naive_pipe_control.py reproduces that difference on demand.
"""
from __future__ import annotations

import queue
import subprocess
import threading
import time


class Engine:
    def __init__(self, exe: str, startup_timeout: float = 30.0):
        self.proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True, bufsize=1)
        self.lines: queue.Queue[str | None] = queue.Queue()
        self._t = threading.Thread(target=self._pump, daemon=True)
        self._t.start()
        self.startup_timeout = startup_timeout

    def _pump(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self.lines.put(line.rstrip("\n"))
        self.lines.put(None)

    def send(self, cmd: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(cmd + "\n")
        self.proc.stdin.flush()

    def read_until(self, predicate, timeout: float) -> tuple[list[str], bool]:
        """Collect lines until predicate(line) is true. Returns (lines, saw_terminal)."""
        collected: list[str] = []
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return collected, False
            try:
                line = self.lines.get(timeout=remaining)
            except queue.Empty:
                return collected, False
            if line is None:
                return collected, False
            collected.append(line)
            if predicate(line):
                return collected, True

    def uci(self) -> list[str]:
        self.send("uci")
        out, _ = self.read_until(lambda l: l.strip() == "uciok", self.startup_timeout)
        return out

    def isready(self) -> list[str]:
        self.send("isready")
        out, _ = self.read_until(lambda l: l.strip() == "readyok", self.startup_timeout)
        return out

    def setoption(self, name: str, value) -> None:
        self.send(f"setoption name {name} value {value}")
        self.isready()

    def bench(self, depth: int, timeout: float = 900.0) -> dict:
        self.send(f"bench {depth}")
        out, ok = self.read_until(lambda l: l.startswith("info string bench"), timeout)
        nodes = None
        for line in out:
            if line.startswith("info string bench"):
                f = line.split()
                nodes = int(f[f.index("nodes") + 1])
        return {"nodes": nodes, "saw_line": ok, "raw": [l for l in out if "bench" in l]}

    def search(self, position_cmd: str, go_cmd: str, timeout: float = 300.0) -> dict:
        self.send(position_cmd)
        self.isready()
        self.send(go_cmd)
        out, ok = self.read_until(lambda l: l.startswith("bestmove"), timeout)
        best = None
        infos = []
        book_lines = []
        for line in out:
            if line.startswith("bestmove"):
                best = line.split()[1]
            elif line.startswith("info depth"):
                infos.append(line)
            elif line.startswith("info string book move"):
                book_lines.append(line)
        last = infos[-1] if infos else None
        nodes = None
        depth_reached = None
        if last:
            f = last.split()
            if "nodes" in f:
                nodes = int(f[f.index("nodes") + 1])
            if "depth" in f:
                depth_reached = int(f[f.index("depth") + 1])
        return {"bestmove": best, "nodes": nodes, "depth": depth_reached,
                "info_depth_lines": len(infos), "saw_bestmove": ok, "last_info": last,
                "book_move_line": book_lines[0] if book_lines else None}

    def close(self) -> None:
        try:
            self.send("quit")
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()
