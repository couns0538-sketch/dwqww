"""Fable 2026-11-23, W5 of FINAL_PLAN_2311.md, version 2 after the reads of the server-plan debate: one
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
- EVERY ARGUMENT OF A CALL IS JUDGED BEFORE THE CALL'S FIRST BYTE (third version, Astra's read of the second:
  `command("go perft 1", secs=-1)` raised its error after the command had gone out, and the next command then
  read that probe's answer as its own): the limit, the cutoff, the line bound, the ending test and the
  command's text. Such a refused call sends nothing and leaves the engine as it was;
- a wait that does not reach its ending line (its time, the line bound, bad bytes, the engine's end, a game
  given up with `sgerror`, or a read_until() that a caller gave unusable arguments after sending something
  itself) RETIRES the object: every later call fails at once and sends nothing, send() included, and quit()
  on it ends the process without writing to it. The left-over lines of a cut answer can therefore never be
  read as the answer to a later command, and a retired engine is never given new work;
- a line that arrived while nobody was waiting is never taken into the next answer: the next command is
  refused before it is sent, and the object is retired;
- a refusal that was read before the engine ended is what the error says (the engine prints
  `info string ERROR NNUE v3: ...` and ends with exit code 2);
- an engine that has ended is reported at once by every later call, with its exit code (waited for no longer
  than that call's own time); a last line without its line end is an error, never a finished answer;
- a command given with a cutoff that has passed sends nothing at all;
- a transcript line that cannot be written, and an ending test that raises inside an answer, retire the object
  too (fourth version): no failure after a command went out leaves the object usable;
- after kill() or quit() the reader thread has ended, both pipes are closed and the object is retired.

The calls: ready(), command() (ended by the next `readyok`), run() (ended by a line of the command's own:
`go` by `bestmove`, `selfgame` by `sgend`), uci_options(). send() and read_until() are their two halves, for a
caller that has to send without waiting (`stop`); a caller that can use run() should.
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
# an option line, by type (never by searching for " min " in a text default that may hold those words)
_OPTION_LINE = re.compile(r"option name (?P<name>\S.*?) type (?:check default (?P<check>true|false)"
                          r"|spin default (?P<spin>-?\d+) min (?P<min>-?\d+) max (?P<max>-?\d+)"
                          r"|string default (?P<string>.*)|(?P<button>button))")


class EngineError(RuntimeError):
    """The engine is gone, did not answer in time, wrote something it must not, or refused something."""


class EngineRefused(EngineError):
    pass


class EngineTimeout(EngineError):
    """A wait ran into its limit or into the day's cutoff. The engine may still be searching: the caller ends it."""


class EngineLogError(EngineError):
    """A line of the transcript could not be written (a full disk). The object is retired: a run whose
    transcript is broken is not continued, and a command that had gone out is never followed by another."""


class _Bad:
    def __init__(self, text):
        self.text = text


_NOTHING = object()
# the longest limit one wait may be given: a bound of this file's own, inside what every platform's wait can
# serve (threading.TIMEOUT_MAX is about 49 days on Windows; a longer wait raised OverflowError AFTER the bytes)
MAX_SECS = min(7 * 86400.0, threading.TIMEOUT_MAX)


def _number(x) -> bool:
    if not isinstance(x, (int, float)) or isinstance(x, bool):
        return False
    try:
        return math.isfinite(x)
    except OverflowError:                 # a whole number too large for a float (10**400) is not a usable time
        return False


def _label(line) -> str:
    return f"`{line[:60]}`" if isinstance(line, str) else "a command"


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
        self.gone = ""                       # set once: why this object is retired
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
        """One line into the transcript. A write that fails RETIRES the object, wherever it happens: before a
        command (then that command is not sent), between a command and its end mark, or inside an answer
        (fourth version, Astra's read of the third: the system's error passed through, the object stayed
        usable, and the next command ran on a board that the failed call had already changed)."""
        if self.log is None:
            return
        try:
            self.log.write(text + "\n")
        except (OSError, ValueError) as e:
            raise self._fail(EngineLogError, "the transcript", f"a line of it could not be written ({e})", "") from None

    def _exit_text(self, left: float) -> str:
        """The exit code, waited for no longer than the time the caller's wait has left (and 5 s at most)."""
        try:
            return f"exit code {self.p.wait(timeout=max(0.0, min(left, 5.0)))}"
        except subprocess.TimeoutExpired:
            return "its output closed, the process not yet ended"

    # ---------------------------------------------------------------- what is judged before any byte
    @staticmethod
    def _check_text(line) -> None:
        if not isinstance(line, str) or any(c < " " or c > "~" for c in line):
            raise EngineError("a command that is not a text, or holds a line break or another character outside "
                              f"printable ASCII (0x20 to 0x7e), is never sent: {str(line)[:60]!r}")
        if len(line) >= MAX_LINE:               # with its line end it would be longer than a line may be
            raise EngineError(f"a command of {len(line)} characters is never sent (a line is at most {MAX_LINE} "
                              f"bytes with its end): {line[:60]!r}")

    @staticmethod
    def _limits_fault(secs, cutoff, max_lines, done=_NOTHING) -> str:
        """'' when a wait may be made with these arguments; otherwise what is wrong with them."""
        if not (_number(secs) and 0 <= secs <= MAX_SECS):
            return f"its limit must be a finite number of seconds from 0 to {MAX_SECS:.0f} (got {str(secs)[:40]})"
        if cutoff is not None and not _number(cutoff):
            return f"its cutoff must be a finite steady-clock time or None (got {str(cutoff)[:40]})"
        if not (isinstance(max_lines, int) and not isinstance(max_lines, bool) and max_lines >= 1):
            return f"its line bound must be a whole number of at least 1 (got {str(max_lines)[:40]})"
        if done is not _NOTHING and not callable(done):
            return "its ending test must be callable"
        return ""

    def _before_send(self, what: str, line, secs, cutoff, max_lines=MAX_LINES, done=_NOTHING) -> None:
        """Everything that can refuse a call, BEFORE its first byte goes out: the arguments, the command's text,
        a retired object, a line nobody asked for (or the engine's end), a cutoff that has passed."""
        fault = self._limits_fault(secs, cutoff, max_lines, done)
        if fault:
            raise EngineError(f"{what}: {fault}; nothing was sent")
        self._check_text(line)
        if self.gone:
            raise EngineError(f"{what}: {self.gone}")
        try:
            item = self.q.get_nowait()
        except queue.Empty:
            item = _NOTHING
        if item is not _NOTHING:
            if item is None:
                text = f"the engine has ended ({self._exit_text(1.0)})"
            elif isinstance(item, _Bad):
                text = f"the engine wrote {item.text}"
            else:
                self._note(item)
                text = "the engine wrote a line that no command had asked for: " + ascii(item[:120])
            raise self._fail(EngineError, what, text + "; nothing was sent", "")
        if cutoff is not None and time.monotonic() >= cutoff:
            raise EngineTimeout(f"the cutoff had passed before {what} was sent; nothing was sent")

    def _fail(self, cls, what: str, text: str, first_bad: str):
        """The error of a call after which the engine's output can no longer be trusted to be in step with what
        was sent. This object is then retired (`gone`): the caller ends the process and starts another. A
        refusal that was already read is what the error says first."""
        if not self.gone:
            self.gone = text + "; this engine process is not used any further"
        if first_bad:
            return EngineRefused(f"{what}: {first_bad}; then: {text}")
        return cls(f"{what}: {text}")

    # ---------------------------------------------------------------- sending and waiting
    def _write(self, line: str) -> None:
        data = (line + "\n").encode("ascii")
        self._note(">>> " + line)
        self.sent.append(line)
        try:
            self.p.stdin.write(data)
            self.p.stdin.flush()
        except (OSError, ValueError) as e:
            raise self._fail(EngineError, _label(line), f"the engine was gone when it was sent ({e})", "") from None

    def send(self, line: str, cutoff=None) -> None:
        """One line to the engine, without a wait (for a caller that reads with read_until() itself). Refused
        before any byte: a text that is not plain, a retired object, a cutoff that is unusable or has passed."""
        self._check_text(line)
        if cutoff is not None and not _number(cutoff):
            raise EngineError(f"{_label(line)}: its cutoff must be a finite steady-clock time or None "
                              f"(got {str(cutoff)[:40]}); nothing was sent")
        if self.gone:
            raise EngineError(f"{_label(line)}: {self.gone}")
        if cutoff is not None and time.monotonic() >= cutoff:
            raise EngineTimeout(f"the cutoff had passed before {_label(line)} was sent; nothing was sent")
        self._write(line)

    def read_until(self, done, secs: float, what: str, refuse: bool = True, cutoff=None,
                   max_lines: int = MAX_LINES) -> list[str]:
        """Lines up to and with the first one for which done(line) is true.

        `secs` is a limit on the steady clock; `cutoff`, when given, is a time.monotonic() value that ends the
        wait earlier. The time left is looked at before EVERY line. Unless refuse is False (then the caller
        looks at the lines itself) every line is judged as it arrives:
        - a line of no expected kind raises EngineRefused AFTER the ending line has been read, so that the
          engine is not left in the middle of an answer and can be used again.
        An `sgerror` line raises EngineRefused AT ONCE, also after an earlier unexpected line and also with
        refuse False: the engine gives a game up WITHOUT an end line (Neon's read: after a first unexpected
        line the second version waited for its limit here).
        A wait that ends in any other way (its time, the line bound, bad bytes, the engine's end) retires this
        object. So does a call with unusable arguments: the caller of read_until() has sent something by
        itself, and that answer stays unread (ready(), command(), run() and uci_options() judge their
        arguments before they send, and never get here with a bad one)."""
        if self.gone:
            raise EngineError(f"{what}: {self.gone}")
        fault = self._limits_fault(secs, cutoff, max_lines, done)
        if fault:
            raise self._fail(EngineError, what, "a wait was asked for with unusable arguments (" + fault + ")", "")
        end = time.monotonic() + secs
        if cutoff is not None:
            end = min(end, cutoff)
        lines: list[str] = []
        first_bad = ""
        while True:
            left = end - time.monotonic()
            line = _NOTHING
            if left > 0:
                try:
                    line = self.q.get(timeout=left)
                except queue.Empty:
                    pass
            if line is _NOTHING:
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
            if line.startswith("sgerror"):       # ALWAYS at once: no end line follows it, whatever was read before
                raise self._fail(EngineRefused, what, "no end line follows a game that was given up",
                                 first_bad or "the engine gave the game up: " + line[:200])
            try:
                ended = done(line)
            except Exception as e:  # noqa: BLE001   the caller's own test failed in the middle of an answer
                raise self._fail(EngineError, what, f"the ending test raised {type(e).__name__} ({e})", first_bad) from None
            if ended:
                break
            if len(lines) >= max_lines:
                raise self._fail(EngineError, what, f"{len(lines)} lines and no end (the limit of one wait)", first_bad)
        if first_bad:
            raise EngineRefused(f"{what}: {first_bad}")
        return lines

    def run(self, line: str, done, secs: float, what: str = "", refuse: bool = True, cutoff=None,
            max_lines: int = MAX_LINES) -> list[str]:
        """A command that a line of its own ends (`go ...` by `bestmove`, `selfgame ...` by `sgend`): sent and
        waited for as one call. Returns the lines up to and with the ending one."""
        what = what if isinstance(what, str) and what else _label(line)
        self._before_send(what, line, secs, cutoff, max_lines, done)
        self._write(line)
        return self.read_until(done, secs, what, refuse, cutoff, max_lines)

    def ready(self, secs: float = 120.0, what: str = "isready", refuse: bool = True, cutoff=None) -> list[str]:
        return self.run("isready", lambda s: s == "readyok", secs, what, refuse, cutoff)[:-1]

    def command(self, line: str, secs: float = 120.0, refuse: bool = True, cutoff=None) -> list[str]:
        """A command that is finished when the engine answers the next isready (setoption, position, ucinewgame,
        eval, bench, go perft)."""
        what = _label(line)
        self._before_send(what, line, secs, cutoff)
        self._write(line)
        self._write("isready")               # the pair is one unit: a command is never left without its end mark
        return self.read_until(lambda s: s == "readyok", secs, what, refuse, cutoff)[:-1]

    def uci_options(self, secs: float = 60.0, cutoff=None) -> dict:
        """The engine's own option list, read by type: name -> {type, default} for check and string (a string's
        default is the whole rest of its line), {type, default, min, max} for spin, {type} for button."""
        out = {}
        for ln in self.run("uci", lambda s: s == "uciok", secs, "uci", cutoff=cutoff):
            m = _OPTION_LINE.fullmatch(ln)
            if not m:
                continue                     # not an option line (id, uciok); an odd option line was refused above
            if m["check"] is not None:
                out[m["name"]] = {"type": "check", "default": m["check"]}
            elif m["spin"] is not None:
                out[m["name"]] = {"type": "spin", "default": m["spin"], "min": m["min"], "max": m["max"]}
            elif m["string"] is not None:
                out[m["name"]] = {"type": "string", "default": m["string"]}
            else:
                out[m["name"]] = {"type": "button"}
        return out

    # ---------------------------------------------------------------- the end
    def _close(self) -> None:
        """The reader thread ended and both pipes closed. The output pipe is closed only once its reader has
        ended (closing it under a blocked read would wait for that read)."""
        self._stop = True
        if not self.gone:
            self.gone = "this engine object was ended (quit or kill)"
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
        """Returns the exit code, or None when the process had to be ended. A retired object gets no byte, not
        this one either: its process is ended."""
        if self.gone:
            self.kill()
            return None
        try:
            self._write("quit")
        except EngineError:
            pass
        try:
            self.p.stdin.close()
        except (OSError, ValueError):
            pass
        try:
            code = self.p.wait(timeout=secs if _number(secs) and 0 <= secs <= MAX_SECS else 30.0)
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
