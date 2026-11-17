#!/usr/bin/env python3
"""Minimal UCI driver for the forge time-manager audit.

Rules this module exists to enforce (from docs/forge-findings.md section 6/7):
  * every read has a timeout; a hang is reported as a hang, never as a slow move
    (trap 21: the book path and `go nodes 0` emit no `info depth` line at all);
  * wall time is measured around the `go` line only, so process start and
    `position` parsing are never folded into a move time;
  * `cmd > out; rc=$?` discipline: the caller reads this module's own return
    values rather than a pipeline's exit code (trap 22).
"""
from __future__ import annotations

import os
import queue
import subprocess
import threading
import time
from dataclasses import dataclass, field


@dataclass
class GoResult:
    go_line: str
    bestmove: str | None
    wall_ms: float
    info_lines: list[str] = field(default_factory=list)
    timed_out: bool = False
    depth_reached: int = 0
    nodes: int = 0
    book: bool = False

    @property
    def answered(self) -> bool:
        return self.bestmove is not None


class Engine:
    """One engine process, driven over pipes with a hard read deadline."""

    def __init__(self, exe: str, args: list[str] | None = None, startup_timeout: float = 30.0):
        self.exe = exe
        self.proc = subprocess.Popen(
            [exe] + (args or []),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self._q: queue.Queue[str | None] = queue.Queue()
        self._reader = threading.Thread(target=self._pump, daemon=True)
        self._reader.start()
        self.send("uci")
        if not self.wait_for("uciok", startup_timeout):
            self.close()
            raise RuntimeError("engine did not answer uci in time")

    def _pump(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self._q.put(line.rstrip("\r\n"))
        self._q.put(None)

    def send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def _readline(self, deadline: float) -> str | None:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        try:
            return self._q.get(timeout=remaining)
        except queue.Empty:
            return None

    def drain(self, settle: float = 0.05) -> list[str]:
        """Collect lines already buffered, without waiting for more."""
        out: list[str] = []
        while True:
            try:
                line = self._q.get(timeout=settle)
            except queue.Empty:
                return out
            if line is None:
                return out
            out.append(line)

    def wait_for(self, prefix: str, timeout: float) -> bool:
        deadline = time.monotonic() + timeout
        while True:
            line = self._readline(deadline)
            if line is None:
                return False
            if line.startswith(prefix):
                return True

    def set_option(self, name: str, value) -> None:
        self.send(f"setoption name {name} value {value}")

    def quit(self) -> None:
        try:
            self.send("quit")
        except (BrokenPipeError, ValueError):
            pass
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()

    def close(self) -> None:
        self.quit()
        time.sleep(0.01)

    def go(self, spec: str, timeout: float) -> GoResult:
        """Issue `go <spec>` and time it from immediately before the write to
        the `bestmove` line. Returns timed_out rather than raising on a hang."""
        self.drain()
        t0 = time.monotonic()
        self.send("go " + spec)
        info: list[str] = []
        depth = 0
        nodes = 0
        book = False
        deadline = t0 + timeout
        best: str | None = None
        while True:
            line = self._readline(deadline)
            if line is None:
                break
            if line.startswith("bestmove"):
                best = line.split()[1] if len(line.split()) > 1 else ""
                break
            if line.startswith("info"):
                info.append(line)
                if "book move" in line:
                    book = True
                for tok, idx in (("depth", 2), ("nodes", None)):
                    if tok in line.split():
                        parts = line.split()
                        j = parts.index(tok)
                        try:
                            val = int(parts[j + 1])
                        except (IndexError, ValueError):
                            continue
                        if tok == "depth":
                            depth = max(depth, val)
                        else:
                            nodes = max(nodes, val)
        wall = (time.monotonic() - t0) * 1000.0
        if best is None:
            # A search that never returned must not be left running.
            self.send("stop")
            deadline2 = time.monotonic() + 5.0
            while True:
                line = self._readline(deadline2)
                if line is None:
                    break
                if line.startswith("bestmove"):
                    best = line.split()[1] if len(line.split()) > 1 else ""
                    break
                if line.startswith("info"):
                    info.append(line)
        return GoResult(
            go_line="go " + spec,
            bestmove=best,
            wall_ms=wall,
            info_lines=info,
            timed_out=best is None,
            depth_reached=depth,
            nodes=nodes,
            book=book,
        )


def fen_after(fen: str) -> str:
    """`position fen ... moves ...` string helper."""
    return fen


def plan_clock(time_ms: int, increment_ms: int, moves_to_go: int, overhead: int = 10,
               soft_divisor: int = 22, inc_pct: int = 75, hard_pct: int = 60,
               hard_mult: int = 5) -> tuple[int, int, bool]:
    """Python mirror of include/forge/clock_plan.hpp:plan_clock_budget.

    Kept literal so the arithmetic in the report is the same arithmetic the
    engine runs, and so a mirror that disagrees with a measurement is visible
    as a mismatch rather than absorbed into prose.
    """
    overhead = max(0, overhead)
    time_ms = max(0, time_ms)
    increment_ms = max(0, increment_ms)
    if time_ms <= overhead:
        return (0, 0, True)
    available = time_ms - overhead
    if moves_to_go > 0:
        mtg = moves_to_go if moves_to_go < 50 else 50
        soft = available // (mtg + 1) + increment_ms * 3 // 4
        hard = min(available * 4 // 5, soft * 4)
    else:
        divisor = soft_divisor if soft_divisor > 0 else 1
        soft = available // divisor + increment_ms * inc_pct // 100
        hard = min(available * hard_pct // 100, soft * hard_mult)
    soft = max(1, min(soft, available))
    hard = max(1, min(hard, available))
    if soft > hard:
        soft = hard
    return (soft, hard, False)
