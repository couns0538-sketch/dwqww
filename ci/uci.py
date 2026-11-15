"""A small UCI driver for the Fable/Opus checks (written 2026-11-15 by the Opus session; read by Fable before use).

One engine process. A reader thread puts every line the engine prints on stdout on a queue, with its arrival time;
the engine's stderr goes to its own file (that is where AddressSanitizer, UBSan and ThreadSanitizer write). Commands
are sent one at a time; wait_for() blocks until a line that starts with a given word arrives or a time limit passes.
Every line sent and received is kept in a transcript with its time, for the evidence files.

Nothing here judges a result; the suite scripts do that.
"""
from __future__ import annotations

import os
import queue
import subprocess
import threading
import time


class Engine:
    def __init__(self, exe: str, stderr_path: str, env: dict | None = None, cwd: str | None = None):
        self.exe = exe
        self.stderr_path = stderr_path
        self.err = open(stderr_path, "ab")
        self.t0 = time.time()
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.err,
                                  cwd=cwd, env=env if env is not None else dict(os.environ),
                                  text=True, encoding="utf-8", errors="replace", bufsize=1)
        self.q: queue.Queue = queue.Queue()
        self.transcript: list[str] = []
        self.eof = False
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    # ---- low level ------------------------------------------------------------------------------------------
    def _read(self) -> None:
        try:
            for line in self.p.stdout:
                self.q.put((time.time(), line.rstrip("\r\n")))
        finally:
            self.q.put((time.time(), None))           # end of output: the engine closed stdout or ended

    def _note(self, text: str) -> None:
        self.transcript.append(f"{time.time() - self.t0:10.3f} {text}")

    def send(self, line: str) -> bool:
        """Writes one command. False when the engine has gone (the pipe is closed)."""
        self._note(">> " + (line if len(line) <= 300 else line[:300] + f" ...[{len(line)} characters in all]"))
        try:
            self.p.stdin.write(line + "\n")
            self.p.stdin.flush()
            return True
        except (BrokenPipeError, OSError, ValueError):
            self._note("!! write failed: the engine is gone")
            return False

    def wait_for(self, word: str, timeout: float) -> tuple[bool, list[str]]:
        """Reads lines until one equals `word` or starts with `word` and a space. Returns (found, lines read).
        found is False after `timeout` seconds or when the engine's output ended."""
        lines: list[str] = []
        if self.eof:                                  # the output ended earlier: nothing more will come
            return False, lines
        end = time.time() + timeout
        while True:
            left = end - time.time()
            if left <= 0:
                self._note(f"!! no '{word}' within {timeout} s")
                return False, lines
            try:
                ts, line = self.q.get(timeout=left)
            except queue.Empty:
                self._note(f"!! no '{word}' within {timeout} s")
                return False, lines
            if line is None:
                self.eof = True
                self._note("!! engine output ended")
                return False, lines
            self.transcript.append(f"{ts - self.t0:10.3f} << " + (line if len(line) <= 300 else line[:300] + " ..."))
            lines.append(line)
            if line == word or line.startswith(word + " "):
                return True, lines

    def drain(self, seconds: float) -> list[str]:
        """Reads whatever arrives within `seconds` (used after a command that has no answer)."""
        lines: list[str] = []
        end = time.time() + seconds
        while time.time() < end:
            try:
                ts, line = self.q.get(timeout=max(0.0, end - time.time()))
            except queue.Empty:
                break
            if line is None:
                self.eof = True
                self._note("!! engine output ended")
                break
            self.transcript.append(f"{ts - self.t0:10.3f} << " + (line if len(line) <= 300 else line[:300] + " ..."))
            lines.append(line)
        return lines

    def pending(self) -> list[str]:
        """The lines that have already arrived, without waiting."""
        lines: list[str] = []
        while True:
            try:
                ts, line = self.q.get_nowait()
            except queue.Empty:
                return lines
            if line is None:
                self.eof = True
                self._note("!! engine output ended")
                return lines
            self.transcript.append(f"{ts - self.t0:10.3f} << " + (line if len(line) <= 300 else line[:300] + " ..."))
            lines.append(line)

    # ---- helpers ----------------------------------------------------------------------------------------------
    def alive(self) -> bool:
        return self.p.poll() is None

    def ready(self, timeout: float = 10.0) -> tuple[bool, float]:
        """isready -> readyok. Returns (answered, seconds)."""
        t = time.time()
        if not self.send("isready"):
            return False, 0.0
        ok, _ = self.wait_for("readyok", timeout)
        return ok, time.time() - t

    def start_uci(self, options: dict | None = None, timeout: float = 30.0) -> bool:
        if not self.send("uci"):
            return False
        ok, _ = self.wait_for("uciok", timeout)
        if not ok:
            return False
        for name, value in (options or {}).items():
            self.send(f"setoption name {name} value {value}")
        return self.ready(timeout)[0]

    def quit(self, timeout: float = 10.0) -> tuple[int | None, float]:
        """Sends quit and waits for the process to end. Returns (exit code or None if it had to be killed, seconds)."""
        t = time.time()
        self.send("quit")
        try:
            rc = self.p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self._note(f"!! the engine did not end within {timeout} s after quit; killed")
            self.p.kill()
            self.p.wait()
            rc = None
        self.err.flush()
        return rc, time.time() - t

    def kill(self) -> None:
        if self.alive():
            self.p.kill()
            self.p.wait()

    def close(self) -> int | None:
        """Ends the process if it still runs and closes the stderr file. Returns the exit code."""
        if self.alive():
            self.quit()
        try:
            self.err.close()
        except OSError:
            pass
        return self.p.returncode


def stderr_size(path: str) -> int:
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def cut(text: str, limit: int = 400) -> str:
    return text if len(text) <= limit else text[:limit] + f" ...[{len(text)} characters in all]"
