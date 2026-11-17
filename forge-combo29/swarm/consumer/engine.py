"""Bounded UCI process driver.

Everything here is deliberately ignorant of chess: it spawns the engine, writes
commands, and reads lines off stdout with a hard deadline.  It never uses
select()+readline on a buffered pipe (trap 2); a background thread drains the
raw fd with os.read and the main thread waits on a condition with a timeout.
"""

from __future__ import annotations

import os
import queue
import subprocess
import threading
import time


class EngineTimeout(Exception):
    pass


class EngineDied(Exception):
    pass


class Wire:
    """One line as it arrived, with the monotonic time it became readable."""

    __slots__ = ("text", "t")

    def __init__(self, text: str, t: float) -> None:
        self.text = text
        self.t = t

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"Wire({self.text!r}, {self.t:.3f})"


class Engine:
    def __init__(self, path: str, *, stderr: bool = False) -> None:
        self.path = path
        self.proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE if stderr else subprocess.DEVNULL,
            bufsize=0,
        )
        self._buf = b""
        self._lines: "queue.Queue[Wire]" = queue.Queue()
        self._eof = threading.Event()
        self._lock = threading.Lock()
        self.stderr_text = ""
        self._rd = threading.Thread(target=self._drain, daemon=True)
        self._rd.start()
        if stderr:
            self._er = threading.Thread(target=self._drain_err, daemon=True)
            self._er.start()
        self.transcript: list[Wire] = []

    # -- io -----------------------------------------------------------------
    def _drain(self) -> None:
        fd = self.proc.stdout.fileno()
        try:
            while True:
                chunk = os.read(fd, 65536)
                if not chunk:
                    break
                now = time.monotonic()
                self._buf += chunk
                while b"\n" in self._buf:
                    raw, self._buf = self._buf.split(b"\n", 1)
                    text = raw.decode("utf-8", "replace").rstrip("\r")
                    self._lines.put(Wire(text, now))
        finally:
            if self._buf:
                self._lines.put(Wire(self._buf.decode("utf-8", "replace"), time.monotonic()))
            self._eof.set()

    def _drain_err(self) -> None:
        try:
            self.stderr_text = self.proc.stderr.read().decode("utf-8", "replace")
        except Exception:  # pragma: no cover
            pass

    def send(self, line: str) -> None:
        if self.proc.poll() is not None:
            raise EngineDied(f"engine exited rc={self.proc.returncode}")
        with self._lock:
            self.proc.stdin.write((line + "\n").encode())
            self.proc.stdin.flush()

    def poll_line(self, timeout: float):
        """Return the next Wire, or None if no line arrives inside `timeout`."""
        deadline = time.monotonic() + timeout
        while True:
            left = deadline - time.monotonic()
            if left <= 0:
                return None
            try:
                w = self._lines.get(timeout=left)
            except queue.Empty:
                return None
            self.transcript.append(w)
            return w

    def read_until(self, pred, timeout: float) -> list[Wire]:
        """Collect lines until pred(wire) is true.  Raises EngineTimeout / EngineDied.

        The timeout is a hard wall-clock bound for the whole call, not per line:
        a chatty engine cannot extend it.
        """
        deadline = time.monotonic() + timeout
        got: list[Wire] = []
        while True:
            left = deadline - time.monotonic()
            if left <= 0:
                raise EngineTimeout(f"no match within {timeout:.3f}s; got {len(got)} lines")
            w = self.poll_line(left)
            if w is None:
                if self._eof.is_set() and self._lines.empty():
                    raise EngineDied("stdout closed before predicate matched")
                raise EngineTimeout(f"no match within {timeout:.3f}s; got {len(got)} lines")
            got.append(w)
            if pred(w):
                return got

    def drain_now(self, quiet_for: float = 0.05) -> list[Wire]:
        """Pull whatever is already buffered, without waiting for more."""
        out: list[Wire] = []
        while True:
            w = self.poll_line(quiet_for)
            if w is None:
                return out
            out.append(w)

    def drain_idle(self, quiet_for: float = 0.25, cap: float = 5.0) -> list[Wire]:
        """Collect lines until nothing new arrives for `quiet_for` seconds."""
        out: list[Wire] = []
        start = time.monotonic()
        while time.monotonic() - start < cap:
            w = self.poll_line(quiet_for)
            if w is None:
                break
            out.append(w)
        return out

    # -- lifecycle ----------------------------------------------------------
    def quit(self, timeout: float = 5.0) -> int:
        try:
            self.send("quit")
        except EngineDied:
            pass
        try:
            self.proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=5)
        return self.proc.returncode

    def kill(self) -> None:
        if self.proc.poll() is None:
            self.proc.kill()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:  # pragma: no cover
            pass

    def __enter__(self) -> "Engine":
        return self

    def __exit__(self, *exc) -> None:
        self.kill()
