"""Minimal UCI driver for the Forge grid.

Design constraints that come from the assignment:
  - fresh process per cell (never reuse a Searcher across cells)
  - fixed node budgets only; wall time is the measurement
  - wait for `bestmove` with a timeout, never close stdin early
  - `invalid FEN` is scanned in BOTH the position reply and the go output
"""

from __future__ import annotations

import queue
import subprocess
import threading
import time


class UciError(RuntimeError):
    pass


class Engine:
    """One engine process. Use as a context manager so the process always dies."""

    def __init__(self, path: str, startup_timeout: float = 30.0):
        self.path = path
        self.proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self._q: queue.Queue[str | None] = queue.Queue()
        self._closed = False
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()
        self.startup_timeout = startup_timeout

    def _read_loop(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self._q.put(line.rstrip("\n"))
        self._q.put(None)

    def send(self, line: str) -> None:
        if self._closed or self.proc.stdin is None:
            raise UciError("send on closed engine")
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, predicate, timeout: float, want: str) -> list[str]:
        """Collect lines until predicate(line) is true. EOF or timeout is an error."""
        out: list[str] = []
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise UciError(f"timeout waiting for {want}; got {len(out)} lines; tail={out[-6:]}")
            try:
                line = self._q.get(timeout=min(remaining, 0.25))
            except queue.Empty:
                continue
            if line is None:
                raise UciError(f"engine EOF while waiting for {want}; tail={out[-6:]}")
            out.append(line)
            if predicate(line):
                return out

    def handshake(self) -> None:
        self.send("uci")
        self.read_until(lambda l: l.strip() == "uciok", self.startup_timeout, "uciok")
        self.send("isready")
        self.read_until(lambda l: l.strip() == "readyok", self.startup_timeout, "readyok")

    def set_option(self, name: str, value: str) -> None:
        self.send(f"setoption name {name} value {value}")

    def sync(self, timeout: float = 60.0) -> list[str]:
        self.send("isready")
        return self.read_until(lambda l: l.strip() == "readyok", timeout, "readyok")

    def set_position(self, fen: str | None) -> list[str]:
        """Send `position` and its own isready; return the POSITION REPLY.

        The position reply is everything up to and including its readyok, so an
        `info string invalid FEN` emitted while applying the position is inside
        this list. It is NOT inside the go output when isready is used.
        """
        self.send("position startpos" if fen is None else f"position fen {fen}")
        self.send("isready")
        return self.read_until(lambda l: l.strip() == "readyok", 60.0, "position readyok")

    def go_nodes(self, nodes: int, timeout: float) -> tuple[list[str], float]:
        """Run `go nodes N`. Return (go output lines, wall ms to bestmove).

        The clock starts immediately before the write and stops on the bestmove
        line arriving, so it includes the engine's own final output flush.
        """
        t0 = time.monotonic()
        self.send(f"go nodes {nodes}")
        lines = self.read_until(
            lambda l: l.startswith("bestmove"), timeout, "bestmove"
        )
        elapsed_ms = (time.monotonic() - t0) * 1000.0
        return lines, elapsed_ms

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            if self.proc.poll() is None:
                self.proc.stdin.write("quit\n")  # type: ignore[union-attr]
                self.proc.stdin.flush()  # type: ignore[union-attr]
                self.proc.wait(timeout=10)
        except Exception:
            pass
        finally:
            if self.proc.poll() is None:
                self.proc.kill()
                self.proc.wait(timeout=10)

    def __enter__(self) -> "Engine":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


def parse_info(line: str) -> dict | None:
    """Parse one `info depth ...` line into a dict. Returns None for other lines."""
    if not line.startswith("info depth"):
        return None
    toks = line.split()
    out: dict = {"multipv": 1, "pv": []}
    i = 0
    while i < len(toks):
        t = toks[i]
        if t == "depth" and i + 1 < len(toks):
            out["depth"] = int(toks[i + 1]); i += 2
        elif t == "seldepth" and i + 1 < len(toks):
            out["seldepth"] = int(toks[i + 1]); i += 2
        elif t == "multipv" and i + 1 < len(toks):
            out["multipv"] = int(toks[i + 1]); i += 2
        elif t == "nodes" and i + 1 < len(toks):
            out["nodes"] = int(toks[i + 1]); i += 2
        elif t == "nps" and i + 1 < len(toks):
            out["nps"] = int(toks[i + 1]); i += 2
        elif t == "time" and i + 1 < len(toks):
            out["time"] = int(toks[i + 1]); i += 2
        elif t == "hashfull" and i + 1 < len(toks):
            out["hashfull"] = int(toks[i + 1]); i += 2
        elif t == "score":
            kind = toks[i + 1]
            out[f"score_{kind}"] = int(toks[i + 2]); i += 3
        elif t == "pv":
            out["pv"] = toks[i + 1:]
            break
        else:
            i += 1
    return out
