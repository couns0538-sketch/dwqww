"""Minimal UCI driver for the book-games audit.

Design rules, each one a bug this file exists to prevent:

* Every `position` is followed by `isready` and the reply window is scanned for
  `invalid FEN` / `illegal move`. A refused FEN leaves the previous board in
  place, so a harness that skips the scan silently measures the wrong position.
* Nothing waits on an `info depth` line. Book replies carry none, so the only
  wait is for `bestmove`, under a wall-clock timeout. A timeout is a result, not
  an exception to swallow.
* Book detection is the literal `info string book move ` prefix, never the
  absence of a depth line.
* `stop` is always sent for infinite/ponder searches before waiting further.
"""

from __future__ import annotations

import queue
import subprocess
import threading
import time
from dataclasses import dataclass, field

BOOK_PREFIX = "info string book move "


class EngineError(RuntimeError):
    pass


@dataclass
class Reply:
    lines: list[str] = field(default_factory=list)
    timed_out: bool = False

    def text(self) -> str:
        return "\n".join(self.lines)

    def bestmove(self) -> str | None:
        for line in self.lines:
            if line.startswith("bestmove"):
                parts = line.split()
                return parts[1] if len(parts) > 1 else None
        return None

    def book_move(self) -> str | None:
        for line in self.lines:
            if line.startswith(BOOK_PREFIX):
                return line[len(BOOK_PREFIX):].strip().split()[0]
        return None

    def depth_lines(self) -> list[str]:
        return [ln for ln in self.lines if ln.startswith("info depth")]

    def last_score_cp(self) -> int | None:
        """Score of the last depth line, in centipawns, from the mover's view.

        Mate scores are returned as +/- (MATE_CP - plies) so they sort above any
        material score without being mistaken for one.
        """
        for line in reversed(self.lines):
            if not line.startswith("info depth"):
                continue
            parts = line.split()
            if "score" not in parts:
                continue
            idx = parts.index("score")
            if idx + 2 >= len(parts):
                continue
            kind, value = parts[idx + 1], parts[idx + 2]
            if kind == "cp":
                return int(value)
            if kind == "mate":
                plies = abs(int(value))
                return (MATE_CP - plies) if int(value) > 0 else -(MATE_CP - plies)
        return None


MATE_CP = 100_000


class Engine:
    """One engine process. Never shared between threads."""

    def __init__(self, binary: str):
        self.binary = binary
        self.proc = subprocess.Popen(
            [binary],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self._q: queue.Queue[str | None] = queue.Queue()
        threading.Thread(target=self._pump, daemon=True).start()

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

    def handshake(self) -> str:
        self.send("uci")
        reply = self.read_until(lambda ln: ln.strip() == "uciok", 10.0)
        if reply.timed_out:
            raise EngineError("no uciok")
        return reply.text()

    def setoption(self, name: str, value: str) -> None:
        self.send(f"setoption name {name} value {value}")
        self.send("isready")
        reply = self.read_until(lambda ln: ln.strip() == "readyok", 10.0)
        if reply.timed_out:
            raise EngineError(f"no readyok after setoption {name}")

    def newgame(self) -> None:
        self.send("ucinewgame")
        self.send("isready")
        if self.read_until(lambda ln: ln.strip() == "readyok", 30.0).timed_out:
            raise EngineError("no readyok after ucinewgame")

    def position(self, body: str) -> Reply:
        self.send(f"position {body}")
        self.send("isready")
        return self.read_until(lambda ln: ln.strip() == "readyok", 10.0)

    def position_checked(self, body: str) -> None:
        reply = self.position(body)
        if reply.timed_out:
            raise EngineError("position reply timed out")
        text = reply.text()
        if "invalid FEN" in text or "illegal move" in text:
            raise EngineError(f"position rejected: {text!r}")

    def go(self, body: str, timeout: float) -> Reply:
        self.send(f"go {body}".strip())
        reply = self.read_until(lambda ln: ln.startswith("bestmove"), timeout)
        if reply.timed_out:
            # Leave the process usable: an unterminated search must be stopped.
            self.send("stop")
            self.read_until(lambda ln: ln.startswith("bestmove"), 5.0)
        return reply

    def quit(self) -> None:
        try:
            self.send("quit")
            self.proc.wait(timeout=5)
        except (BrokenPipeError, ValueError, subprocess.TimeoutExpired):
            self.proc.kill()
