"""Minimal UCI driver for the Forge book audit.

Design rules this file enforces (each one is a bug we would otherwise ship):

* The `info string invalid FEN` diagnostic is emitted in reply to `position`,
  before the next `readyok`. So every `position` is followed by an `isready`
  and the reply window is scanned for the diagnostic. A caller that skips this
  scan would silently measure the previous position.
* Nothing ever waits on an `info depth` line. The only wait is for `bestmove`,
  with a timeout.
* `go infinite` / `go ponder` always get an explicit `stop`.
"""

from __future__ import annotations

import queue
import subprocess
import threading
import time
from dataclasses import dataclass, field


class EngineError(RuntimeError):
    pass


@dataclass
class Reply:
    lines: list[str] = field(default_factory=list)
    timed_out: bool = False

    def text(self) -> str:
        return "\n".join(self.lines)

    def bestmove_lines(self) -> list[str]:
        return [ln for ln in self.lines if ln.startswith("bestmove")]

    def info_depth_lines(self) -> list[str]:
        return [ln for ln in self.lines if ln.startswith("info depth")]

    def info_string_lines(self) -> list[str]:
        return [ln for ln in self.lines if ln.startswith("info string")]


class Engine:
    """One engine process. Never shared between threads."""

    def __init__(self, binary: str, args: list[str] | None = None):
        self.binary = binary
        self.proc = subprocess.Popen(
            [binary] + (args or []),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self._q: queue.Queue[str | None] = queue.Queue()
        self._reader = threading.Thread(target=self._pump, daemon=True)
        self._reader.start()

    def _pump(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self._q.put(line.rstrip("\n"))
        self._q.put(None)

    def send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, predicate, timeout: float) -> Reply:
        reply = Reply()
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                reply.timed_out = True
                return reply
            try:
                item = self._q.get(timeout=remaining)
            except queue.Empty:
                reply.timed_out = True
                return reply
            if item is None:
                reply.timed_out = True
                return reply
            reply.lines.append(item)
            if predicate(item):
                return reply

    def read_for(self, seconds: float) -> Reply:
        """Collect lines for a fixed wall-clock window."""
        reply = Reply()
        deadline = time.monotonic() + seconds
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return reply
            try:
                item = self._q.get(timeout=remaining)
            except queue.Empty:
                return reply
            if item is None:
                return reply
            reply.lines.append(item)

    def handshake(self) -> str:
        self.send("uci")
        reply = self.read_until(lambda ln: ln.strip() == "uciok", 10.0)
        if reply.timed_out:
            raise EngineError("no uciok")
        return reply.text()

    def setoption(self, name: str, value: str) -> Reply:
        self.send(f"setoption name {name} value {value}")
        self.send("isready")
        return self.read_until(lambda ln: ln.strip() == "readyok", 10.0)

    def newgame(self) -> None:
        self.send("ucinewgame")
        self.send("isready")
        self.read_until(lambda ln: ln.strip() == "readyok", 10.0)

    def position(self, command: str) -> Reply:
        """Send a full `position ...` body and return the position reply window.

        The window ends at `readyok`, so it contains any `info string invalid
        FEN` / `illegal move` diagnostic the engine emitted for this command.
        """
        self.send(f"position {command}")
        self.send("isready")
        return self.read_until(lambda ln: ln.strip() == "readyok", 10.0)

    def position_checked(self, command: str) -> Reply:
        reply = self.position(command)
        if "invalid FEN" in reply.text() or "illegal move" in reply.text():
            raise EngineError(f"position rejected: {reply.text()!r}")
        return reply

    def go_and_wait(self, go_body: str, timeout: float, stop_after: float | None = None) -> Reply:
        """Run one `go` and wait for `bestmove`.

        For infinite/ponder searches pass `stop_after`; `stop` is sent then the
        wait continues under the same timeout budget.
        """
        deadline = time.monotonic() + timeout
        self.send(f"go {go_body}".strip())
        if stop_after is not None:
            time.sleep(stop_after)
            self.send("stop")
            deadline = time.monotonic() + timeout
        return self.read_until(lambda ln: ln.startswith("bestmove"), max(0.0, deadline - time.monotonic()))

    def quit(self) -> None:
        try:
            self.send("quit")
        except (BrokenPipeError, ValueError):
            pass
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def parse_bestmove(line: str) -> tuple[str | None, str | None]:
    parts = line.split()
    move = parts[1] if len(parts) > 1 else None
    ponder = None
    if "ponder" in parts:
        idx = parts.index("ponder")
        if idx + 1 < len(parts):
            ponder = parts[idx + 1]
    return move, ponder
