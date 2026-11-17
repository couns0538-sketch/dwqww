"""Minimal UCI driver that never lets EOF reach a running search.

Findings §7 item 1/3a: piping a command list into the engine and closing stdin
aborts the search and fabricates a bestmove with zero `info depth` lines. This
module keeps the pipe open until the engine's own terminator arrives, then sends
`quit`.
"""

from __future__ import annotations

import os
import select
import subprocess
import time
from dataclasses import dataclass, field


@dataclass
class GoResult:
    lines: list[str] = field(default_factory=list)
    bestmove: str | None = None
    ponder: str | None = None
    terminated: bool = False
    timed_out: bool = False
    wall_s: float = 0.0

    @property
    def info_depths(self) -> list[str]:
        return [ln for ln in self.lines if ln.startswith("info depth")]

    @property
    def last_depth(self) -> int | None:
        best = None
        for ln in self.info_depths:
            tok = ln.split()
            try:
                best = int(tok[tok.index("depth") + 1])
            except (ValueError, IndexError):
                continue
        return best

    @property
    def last_score(self) -> tuple[str, int] | None:
        out = None
        for ln in self.info_depths:
            tok = ln.split()
            if "score" in tok:
                i = tok.index("score")
                kind = tok[i + 1]
                try:
                    out = (kind, int(tok[i + 2]))
                except (ValueError, IndexError):
                    continue
        return out

    @property
    def last_nodes(self) -> int | None:
        out = None
        for ln in self.info_depths:
            tok = ln.split()
            if "nodes" in tok:
                try:
                    out = int(tok[tok.index("nodes") + 1])
                except (ValueError, IndexError):
                    continue
        return out

    @property
    def last_pv(self) -> list[str]:
        for ln in reversed(self.info_depths):
            tok = ln.split()
            if "pv" in tok:
                return tok[tok.index("pv") + 1:]
        return []

    @property
    def last_snapshot(self) -> dict:
        """The final info depth line as a dict of its numeric fields."""
        for ln in reversed(self.info_depths):
            tok = ln.split()
            d: dict = {}
            for key in ("depth", "seldepth", "nodes", "nps", "hashfull", "time", "multipv"):
                if key in tok:
                    try:
                        d[key] = int(tok[tok.index(key) + 1])
                    except (ValueError, IndexError):
                        pass
            return d
        return {}


class Engine:
    def __init__(self, path: str, options: dict[str, str] | None = None):
        self.proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        self.fd = self.proc.stdout.fileno()
        self._buf = b""
        self.send("uci")
        self.expect("uciok")
        for k, v in (options or {}).items():
            self.send(f"setoption name {k} value {v}")
        self.send("isready")
        self.expect("readyok")

    def send(self, cmd: str) -> None:
        self.proc.stdin.write((cmd + "\n").encode())
        self.proc.stdin.flush()

    def _read_chunk(self, timeout: float) -> bytes:
        r, _, _ = select.select([self.fd], [], [], timeout)
        if not r:
            return b""
        return os.read(self.fd, 65536)

    def readline(self, timeout: float = 30.0) -> str | None:
        deadline = time.time() + timeout
        while b"\n" not in self._buf:
            left = deadline - time.time()
            if left <= 0:
                return None
            chunk = self._read_chunk(left)
            if not chunk:
                if self.proc.poll() is not None:
                    return None
                continue
            self._buf += chunk
        line, self._buf = self._buf.split(b"\n", 1)
        return line.decode("utf-8", "replace").rstrip("\r")

    def expect(self, token: str, timeout: float = 30.0) -> list[str]:
        out = []
        deadline = time.time() + timeout
        while True:
            left = max(0.0, deadline - time.time())
            ln = self.readline(timeout=left + 0.001)
            if ln is None:
                raise TimeoutError(f"no {token!r} within {timeout}s; got {out[-5:]}")
            out.append(ln)
            if token in ln:
                return out

    def go(self, cmd: str, timeout: float = 60.0, extra_wait: float = 0.0) -> GoResult:
        t0 = time.time()
        self.send(cmd)
        res = GoResult()
        deadline = t0 + timeout
        while True:
            left = deadline - time.time()
            if left <= 0:
                res.timed_out = True
                res.wall_s = time.time() - t0
                return res
            ln = self.readline(timeout=left)
            if ln is None:
                res.timed_out = True
                res.wall_s = time.time() - t0
                return res
            res.lines.append(ln)
            if ln.startswith("bestmove"):
                tok = ln.split()
                res.bestmove = tok[1] if len(tok) > 1 else None
                if "ponder" in tok:
                    res.ponder = tok[tok.index("ponder") + 1]
                res.terminated = True
                res.wall_s = time.time() - t0
                if extra_wait:
                    time.sleep(extra_wait)
                return res

    def sync(self) -> None:
        self.send("isready")
        self.expect("readyok")

    def newgame(self) -> None:
        """ucinewgame is a cold reset (findings §7 item 3); Clear Hash is not."""
        self.send("ucinewgame")
        self.sync()

    def setpos(self, fen: str | None = None, moves: str = "") -> None:
        if fen is None:
            cmd = "position startpos"
        else:
            cmd = f"position fen {fen}"
        if moves:
            cmd += f" moves {moves}"
        self.send(cmd)

    def close(self) -> None:
        try:
            self.send("quit")
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()

    def __enter__(self) -> "Engine":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
