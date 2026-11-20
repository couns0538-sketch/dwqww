#!/usr/bin/env python3
"""Line-oriented UCI session for the grok2 harnesses.

Reads every engine line. Stops on the refusal phrases the brief names.
"""
import queue
import subprocess
import threading

REFUSAL_MARKS = (
    "unknown option",
    "invalid value",
    "invalid FEN",
    "illegal move",
)


class HarnessStop(Exception):
    pass


class Session:
    def __init__(self, exe: str) -> None:
        self.exe = exe
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.lines: list[str] = []
        self._q: queue.Queue[str | None] = queue.Queue()
        self._reader = threading.Thread(target=self._read, daemon=True)
        self._reader.start()

    def _read(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self.lines.append(line)
            self._q.put(line)
        self._q.put(None)

    def send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, predicate, timeout: float) -> list[str]:
        import time

        end = time.monotonic() + timeout
        got: list[str] = []
        while True:
            remain = end - time.monotonic()
            if remain <= 0:
                tail = "".join(self.lines[-5:])
                raise TimeoutError(f"timeout; tail:\n{tail}")
            try:
                line = self._q.get(timeout=remain)
            except queue.Empty as exc:
                tail = "".join(self.lines[-5:])
                raise TimeoutError(f"timeout; tail:\n{tail}") from exc
            if line is None:
                tail = "".join(self.lines[-5:])
                raise RuntimeError(f"engine exited; tail:\n{tail}")
            for mark in REFUSAL_MARKS:
                if mark in line:
                    raise HarnessStop(line.rstrip("\n"))
            got.append(line)
            if predicate(line):
                return got

    def close(self) -> None:
        try:
            if self.proc.poll() is None:
                self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=5)
