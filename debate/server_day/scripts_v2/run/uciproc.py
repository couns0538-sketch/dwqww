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
- the bytes are bounded and plain in BOTH directions: a line longer than MAX_LINE bytes, more than `max_lines`
  lines in one wait, or any byte outside 0x20..0x7e inside a line (a NUL, a CR in the middle, an escape) is an
  EngineError, never a growing buffer, a replaced character or a line that a later reader splits in two; the
  line end is one LF, with one CR before it where the system writes that;
- a wait that does not reach its ending line (its time, the line bound, bad bytes, the engine's end, a game
  given up with `sgerror`) leaves the object unusable: every later call fails at once and sends nothing, so
  the left-over lines of a cut answer can never be read as the answer to the next command;
- a refusal that was read before the engine ended is what the error says (the engine prints
  `info string ERROR NNUE v3: ...` and ends with exit code 2);
- an engine that has ended is reported at once by every later wait, with its exit code (waited for no longer
  than that wait's own time); a last line without its line end is an error, never a finished answer;
- a command given with a cutoff that has passed sends nothing at all;
- after kill() or quit() the reader thread has ended and both pipes are closed.
"""
import math
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
_PRINTABLE = bytes(range(0x20, 0x7f))   # the only bytes a line may hold, in both directions


class EngineError(RuntimeError):
    """The engine is gone, did not answer in time, wrote something it must not, or refused something."""


class EngineRefused(EngineError):
    pass


class EngineTimeout(EngineError):
    """A wait ran into its limit or into the day's cutoff. The engine may still be searching: the caller ends it."""


class _Bad:
    def __init__(self, text):
        self.text = text


_TIMED_OUT = object()


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
                if not raw.endswith(b"\n"):                 # no line end: too long, or cut off by the engine's end
                    self._put(_Bad(f"a line of more than {MAX_LINE} bytes" if len(raw) > MAX_LINE else
                                   "an unfinished last line (no line end): " + ascii(raw[:120])))
                    break
                body = raw[:-2] if raw.endswith(b"\r\n") else raw[:-1]     # ONE line end, nothing else stripped
                if body.translate(None, _PRINTABLE):
                    self._put(_Bad("a byte outside printable ASCII (0x20 to 0x7e) in the line " + ascii(raw[:120])))
                    break
                self._put(body.decode("ascii"))
        except (OSError, ValueError):
            pass
        finally:
            self._put(None)

    def _note(self, text):
        if self.log is not None:
            self.log.write(text + "\n")

    def _exit_text(self, left: float) -> str:
        """The exit code, waited for no longer than the time the caller's wait has left (and 5 s at most)."""
        try:
            return f"exit code {self.p.wait(timeout=max(0.0, min(left, 5.0)))}"
        except subprocess.TimeoutExpired:
            return "its output closed, the process not yet ended"

    def _before_send(self, cutoff, what: str) -> None:
        """Nothing is sent to an engine object that is no longer usable, and nothing once the day's cutoff has
        passed: both checks come BEFORE the first byte goes out."""
        if self.gone:
            raise EngineError(f"{what}: {self.gone}")
        if cutoff is not None and time.monotonic() >= cutoff:
            raise EngineTimeout(f"the cutoff had passed before {what} was sent; nothing was sent")

    def _fail(self, cls, what: str, text: str, first_bad: str):
        """The error of a wait that did not reach its ending line. The engine's answer is then cut somewhere
        unknown, so this object is not usable any more (`gone`): the caller ends the process and starts
        another. A refusal that was already read is what the error says first."""
        if not self.gone:
            self.gone = text + "; this engine process is not used any further"
        if first_bad:
            return EngineRefused(f"{what}: {first_bad}; then: {text}")
        return cls(f"{what}: {text}")

    # ---------------------------------------------------------------- sending and waiting
    def send(self, line: str) -> None:
        if any(c < " " or c > "~" for c in line):
            raise EngineError("a command with a line break or another character outside printable ASCII "
                              f"(0x20 to 0x7e) is never sent: {line[:60]!r}")
        data = (line + "\n").encode("ascii")
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
        wait earlier. The time left is looked at before EVERY line. Unless refuse is False (then the caller
        looks at the lines itself) every line is judged as it arrives:
        - a line of no expected kind raises EngineRefused AFTER the ending line has been read, so that the
          engine is not left in the middle of an answer and can be used again;
        - an `sgerror` line raises it at once: the engine gives a game up WITHOUT an end line.
        A wait that ends in any other way (its time, the line bound, bad bytes, the engine's end) leaves this
        object unusable: every later call fails at once, and the caller ends the process."""
        if not (math.isfinite(secs) and secs >= 0) or (cutoff is not None and not math.isfinite(cutoff)) or max_lines < 1:
            raise EngineError(f"{what}: a wait needs a finite limit, a finite cutoff and a line bound of at least 1 "
                              f"(got {secs!r}, {cutoff!r}, {max_lines!r})")
        if self.gone:
            raise EngineError(f"{what}: {self.gone}")
        end = time.monotonic() + secs
        if cutoff is not None:
            end = min(end, cutoff)
        lines: list[str] = []
        first_bad = ""
        while True:
            left = end - time.monotonic()
            line = _TIMED_OUT
            if left > 0:
                try:
                    line = self.q.get(timeout=left)
                except queue.Empty:
                    pass
            if line is _TIMED_OUT:
                raise self._fail(EngineTimeout, what, f"no end within its time ({secs:.0f} s or the cutoff); "
                                 f"{len(lines)} lines came", first_bad)
            if line is None:
                raise self._fail(EngineError, what, f"the engine has ended ({self._exit_text(end - time.monotonic())})",
                                 first_bad)
            if isinstance(line, _Bad):
                raise self._fail(EngineError, what, f"the engine wrote {line.text}", first_bad)
            self._note(line)
            lines.append(line)
            if refuse and not first_bad:
                first_bad = engine_lines.why_not(line)
                if first_bad and line.startswith("sgerror"):
                    raise self._fail(EngineRefused, what, "no end line follows a game that was given up", first_bad)
            if done(line):
                break
            if len(lines) >= max_lines:
                raise self._fail(EngineError, what, f"{len(lines)} lines and no end (the limit of one wait)", first_bad)
        if first_bad:
            raise EngineRefused(f"{what}: {first_bad}")
        return lines

    def ready(self, secs: float = 120.0, what: str = "isready", refuse: bool = True, cutoff=None) -> list[str]:
        self._before_send(cutoff, "`isready`")
        self.send("isready")
        return self.read_until(lambda s: s == "readyok", secs, what, refuse, cutoff)[:-1]

    def command(self, line: str, secs: float = 120.0, refuse: bool = True, cutoff=None) -> list[str]:
        """A command that is finished when the engine answers the next isready (setoption, position, ucinewgame,
        eval, bench, go perft)."""
        self._before_send(cutoff, f"`{line[:60]}`")
        self.send(line)
        self.send("isready")                 # the pair is one unit: a command is never left without its end mark
        return self.read_until(lambda s: s == "readyok", secs, f"`{line[:60]}`", refuse, cutoff)[:-1]

    def uci_options(self, secs: float = 60.0, cutoff=None) -> dict:
        """The engine's own option list: name -> {type, default, min, max}."""
        self._before_send(cutoff, "`uci`")
        self.send("uci")
        out = {}
        for ln in self.read_until(lambda s: s == "uciok", secs, "uci", cutoff=cutoff):
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
