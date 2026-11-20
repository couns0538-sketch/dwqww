"""Line reader for a Forge process.

stdout is wrapped in a thread so a burst of lines is not stuck behind select().
"""
import queue
import subprocess
import threading
from pathlib import Path

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe: Path) -> None:
        self.process = subprocess.Popen(
            [str(exe)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.lines: list[str] = []
        self.queue: queue.Queue[str | None] = queue.Queue()
        self.thread = threading.Thread(target=self._read, daemon=True)
        self.thread.start()

    def _read(self) -> None:
        assert self.process.stdout is not None
        for line in self.process.stdout:
            self.queue.put(line)
        self.queue.put(None)

    def send(self, line: str) -> None:
        assert self.process.stdin is not None
        self.lines.append(">> " + line)
        self.process.stdin.write(line + "\n")
        self.process.stdin.flush()

    def readline(self, timeout: float) -> str:
        try:
            line = self.queue.get(timeout=timeout)
        except queue.Empty as exc:
            self.process.kill()
            raise TimeoutError("engine timed out") from exc
        if line is None:
            self.process.kill()
            raise EOFError("engine closed stdout")
        text = line.rstrip("\n")
        self.lines.append(text)
        for bad in BAD:
            if bad in text:
                self.process.kill()
                raise RuntimeError(text)
        return text

    def read_until(self, done, timeout: float) -> list[str]:
        got: list[str] = []
        while True:
            text = self.readline(timeout)
            got.append(text)
            if done(text):
                return got

    def ready(self) -> None:
        self.send("isready")
        self.read_until(lambda line: line == "readyok", 60)

    def close(self) -> None:
        try:
            self.send("quit")
        except BrokenPipeError:
            pass
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
