"""Fable 2026-11-23, W5 of FINAL_PLAN_2311.md: one engine process, spoken to line by line. Standard library only.

The rules it keeps (N15 and N17 of the plan):
- every line the engine writes is read; a line that says an option, a position or a game was NOT taken raises
  EngineRefused (the engine itself only prints one line and plays on with a default);
- nothing is sent while a search or a game runs: the caller waits for the line that ends it.
"""
import queue
import re
import subprocess
import threading
import time
from pathlib import Path

# the plan's N15 (1): the lines that must stop a start or throw a game away
REFUSAL = re.compile(r"unknown option|invalid value|No such option|ERROR|cannot load|invalid FEN|illegal move|^sgerror ")


class EngineError(RuntimeError):
    """The engine is gone, did not answer in time, or refused something."""


class EngineRefused(EngineError):
    pass


class Engine:
    def __init__(self, exe, log=None):
        exe = Path(exe).resolve()
        self.log = log                      # a text file object or None: every line in both directions
        self.p = subprocess.Popen([str(exe)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
                                  bufsize=1, cwd=str(exe.parent))
        self.q: "queue.Queue[str | None]" = queue.Queue()
        self.sent: list = []                 # every line sent, in order
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        try:
            for line in self.p.stdout:
                self.q.put(line.rstrip("\r\n"))
        finally:
            self.q.put(None)

    def _note(self, text):
        if self.log is not None:
            self.log.write(text + "\n")

    def send(self, line: str) -> None:
        self._note(">>> " + line)
        self.sent.append(line)
        try:
            self.p.stdin.write(line + "\n")
            self.p.stdin.flush()
        except (OSError, ValueError) as e:
            raise EngineError(f"the engine was gone when `{line[:60]}` was sent ({e})") from None

    def read_until(self, done, secs: float, what: str, refuse: bool = True) -> list[str]:
        """Lines up to and with the first one for which done(line) is true. A refusal line raises (after the
        ending line has been read, so that the engine is not left in the middle of an answer) unless refuse is
        False; then the caller looks at the lines itself."""
        end = time.time() + secs
        lines: list[str] = []
        while True:
            try:
                line = self.q.get(timeout=max(0.05, end - time.time()))
            except queue.Empty:
                raise EngineError(f"no answer to {what} within {secs:.0f} s") from None
            if line is None:
                raise EngineError(f"the engine ended while {what} was awaited (exit code {self.p.poll()})")
            self._note(line)
            lines.append(line)
            if done(line):
                break
        if refuse:
            bad = [ln for ln in lines if REFUSAL.search(ln)]
            if bad:
                raise EngineRefused(f"{what}: {bad[0][:200]}")
        return lines

    def ready(self, secs: float = 120.0, what: str = "isready", refuse: bool = True) -> list[str]:
        self.send("isready")
        return self.read_until(lambda s: s == "readyok", secs, what, refuse)[:-1]

    def command(self, line: str, secs: float = 120.0, refuse: bool = True) -> list[str]:
        """A command that is finished when the engine answers the next isready (setoption, position, ucinewgame,
        eval, bench, go perft)."""
        self.send(line)
        return self.ready(secs, f"`{line[:60]}`", refuse)

    def uci_options(self, secs: float = 60.0) -> dict:
        """The engine's own option list: name -> {type, default, min, max}."""
        self.send("uci")
        out = {}
        for ln in self.read_until(lambda s: s == "uciok", secs, "uci"):
            m = re.match(r"option name (.+?) type (\S+)(.*)$", ln)
            if not m:
                continue
            d = {"type": m[2]}
            for key in ("default", "min", "max"):
                k = re.search(rf" {key} (\S*)", m[3])
                if k:
                    d[key] = k[1]
            out[m[1]] = d
        return out

    def quit(self, secs: float = 30.0):
        """Returns the exit code, or None when it had to be ended."""
        try:
            self.send("quit")
            self.p.stdin.close()
        except (EngineError, OSError):
            pass
        try:
            return self.p.wait(timeout=secs)
        except subprocess.TimeoutExpired:
            self.kill()
            return None

    def kill(self) -> None:
        if self.p.poll() is None:
            try:
                self.p.kill()
            except OSError:
                pass
        try:
            self.p.wait(timeout=30)
        except subprocess.TimeoutExpired:
            pass
