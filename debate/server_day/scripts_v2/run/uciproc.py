"""Fable 2026-11-23, W5 of FINAL_PLAN_2311.md, version 2 after the first read of the server-plan debate: one
engine process, spoken to line by line. Standard library only.

The rules it keeps (N15 and N17 of the plan; SETUP_PLAN.md rows 6 and 11):
- every line the engine writes is read (its error output too: both go into one pipe that a thread of its own
  empties, so the engine can never block on a full pipe);
- a line that is not one of the kinds a clean run prints raises EngineRefused (run/engine_lines.py, an ALLOW
  list: the engine itself only prints one line and plays on with a default);
- nothing is sent while a search or a game runs: the caller waits for the line that ends it;
- every wait has a limit on a STEADY clock that is checked before every single line, also while lines keep
  arriving, and that the day's cutoff can shorten (the first read's finding 10: version 1 looked at its limit
  only when no line came, so an engine that printed for ever was never timed out);
- the engine's bytes are bounded and plain: a line longer than MAX_LINE bytes, more than `max_lines` lines in
  one wait, or a byte outside ASCII is an EngineError, never a growing buffer or a replaced character;
- an engine that has ended is reported at once by every later wait, with its exit code;
- after kill() or quit() the reader thread has ended and both pipes are closed.
"""
import queue
import re
import subprocess
import threading
import time
from pathlib import Path

import engine_lines

MAX_LINE = 65536       # bytes in one line; the longest line of a clean game (its end line with every move) is under 4,000
MAX_LINES = 100000     # lines in one wait; a game of 300 plies with every depth line printed is under 10,000
QUEUE_LINES = 200000   # lines held while nobody waits; beyond it the engine is left to block and the next wait times out


class EngineError(RuntimeError):
    """The engine is gone, did not answer in time, wrote something it must not, or refused something."""


class EngineRefused(EngineError):
    pass


class EngineTimeout(EngineError):
    """A wait ran into its limit or into the day's cutoff. The engine may still be searching: the caller ends it."""


class _Bad:
    def __init__(self, text):
        self.text = text


class Engine:
    def __init__(self, exe, log=None):
        exe = Path(exe).resolve()
        self.log = log                      # a text file object or None: every line in both directions
        try:
            self.p = subprocess.Popen([str(exe)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT, cwd=str(exe.parent))
        except OSError as e:
            raise EngineError(f"the engine could not be started ({e})") from None
        self.q: "queue.Queue" = queue.Queue(maxsize=QUEUE_LINES)
        self.sent: list = []                 # every line sent, in order
        self.gone = ""                       # set once: why no further line will ever come
        self._stop = False
        self._t = threading.Thread(target=self._reader, daemon=True)
        self._t.start()

    # ---------------------------------------------------------------- the reader thread
    def _put(self, item) -> None:
        while not self._stop:
            try:
                self.q.put(item, timeout=0.2)
                return
            except queue.Full:
                continue

    def _reader(self):
        try:
            while True:
                raw = self.p.stdout.readline(MAX_LINE + 1)
                if not raw:
                    break
                if len(raw) > MAX_LINE and not raw.endswith(b"\n"):
                    self._put(_Bad(f"a line of more than {MAX_LINE} bytes"))
                    break
                try:
                    line = raw.decode("ascii")
                except UnicodeDecodeError:
                    self._put(_Bad("a byte outside ASCII in the line " + ascii(raw[:120])))
                    break
                self._put(line.rstrip("\r\n"))
        except (OSError, ValueError):
            pass
        finally:
            self._put(None)

    def _note(self, text):
        if self.log is not None:
            self.log.write(text + "\n")

    def _exit_text(self) -> str:
        try:
            return f"exit code {self.p.wait(timeout=5)}"
        except subprocess.TimeoutExpired:
            return "its output closed, the process not yet ended"

    # ---------------------------------------------------------------- sending and waiting
    def send(self, line: str) -> None:
        if "\n" in line or "\r" in line:
            raise EngineError(f"a command with a line break inside is never sent: {line[:60]!r}")
        try:
            data = (line + "\n").encode("ascii")
        except UnicodeEncodeError:
            raise EngineError(f"a command with a character outside ASCII is never sent: {line[:60]!r}") from None
        self._note(">>> " + line)
        self.sent.append(line)
        try:
            self.p.stdin.write(data)
            self.p.stdin.flush()
        except (OSError, ValueError) as e:
            raise EngineError(f"the engine was gone when `{line[:60]}` was sent ({e})") from None

    def read_until(self, done, secs: float, what: str, refuse: bool = True, cutoff=None,
                   max_lines: int = MAX_LINES) -> list[str]:
        """Lines up to and with the first one for which done(line) is true.

        `secs` is a limit on the steady clock; `cutoff`, when given, is a time.monotonic() value that ends the
        wait earlier. The time left is looked at before EVERY line. A line of no expected kind raises
        EngineRefused (after the ending line has been read, so that the engine is not left in the middle of an
        answer) unless refuse is False; then the caller looks at the lines itself."""
        end = time.monotonic() + secs
        if cutoff is not None:
            end = min(end, cutoff)
        lines: list[str] = []
        while True:
            if self.gone:
                raise EngineError(f"{what}: {self.gone}")
            left = end - time.monotonic()
            if left <= 0:
                raise EngineTimeout(f"no end of {what} within its time ({secs:.0f} s or the cutoff); {len(lines)} lines came")
            try:
                line = self.q.get(timeout=left)
            except queue.Empty:
                raise EngineTimeout(f"no end of {what} within its time ({secs:.0f} s or the cutoff); {len(lines)} lines came") from None
            if line is None:
                self.gone = f"the engine has ended ({self._exit_text()})"
                continue
            if isinstance(line, _Bad):
                self.gone = f"the engine wrote {line.text}; it is not read any further"
                continue
            self._note(line)
            lines.append(line)
            if done(line):
                break
            if len(lines) >= max_lines:
                raise EngineError(f"{what}: {len(lines)} lines and no end (the limit of one wait)")
        if refuse:
            for ln in lines:
                why = engine_lines.why_not(ln)
                if why:
                    raise EngineRefused(f"{what}: {why}")
        return lines

    def ready(self, secs: float = 120.0, what: str = "isready", refuse: bool = True, cutoff=None) -> list[str]:
        self.send("isready")
        return self.read_until(lambda s: s == "readyok", secs, what, refuse, cutoff)[:-1]

    def command(self, line: str, secs: float = 120.0, refuse: bool = True, cutoff=None) -> list[str]:
        """A command that is finished when the engine answers the next isready (setoption, position, ucinewgame,
        eval, bench, go perft)."""
        self.send(line)
        return self.ready(secs, f"`{line[:60]}`", refuse, cutoff)

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

    # ---------------------------------------------------------------- the end
    def _close(self) -> None:
        """The reader thread ended and both pipes closed. The output pipe is closed only once its reader has
        ended (closing it under a blocked read would wait for that read)."""
        self._stop = True
        try:
            self.p.stdin.close()
        except (OSError, ValueError):
            pass
        self._t.join(timeout=5)
        if not self._t.is_alive():
            try:
                self.p.stdout.close()
            except (OSError, ValueError):
                pass

    def quit(self, secs: float = 30.0):
        """Returns the exit code, or None when it had to be ended."""
        try:
            self.send("quit")
        except EngineError:
            pass
        try:
            self.p.stdin.close()
        except (OSError, ValueError):
            pass
        try:
            code = self.p.wait(timeout=secs)
        except subprocess.TimeoutExpired:
            self.kill()
            return None
        self._close()
        return code

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
        self._close()
