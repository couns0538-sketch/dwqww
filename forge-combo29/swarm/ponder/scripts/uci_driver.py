"""Bounded UCI driver for the forge engine.

Every wait has a deadline. Nothing here can block forever: on deadline the
process is SIGKILLed and the caller gets an explicit CAPPED verdict rather than
a hang (see forge-findings.md 7.1: EOF during a search fabricates a bestmove,
so stdin is never closed while a search runs).

Lines are timestamped on arrival by a reader thread. `select()` on a buffered
pipe is not a timeout, so no select() is used.
"""

import os
import signal
import subprocess
import sys
import threading
import time


class Line:
    __slots__ = ("t", "text")

    def __init__(self, t, text):
        self.t = t
        self.text = text

    def __repr__(self):
        return f"<{self.t:.6f} {self.text!r}>"


class Engine:
    def __init__(self, exe, env=None, cwd=None):
        self.exe = exe
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
            cwd=cwd,
        )
        self.lines = []
        self._cv = threading.Condition()
        self._closed = False
        self._killed = False
        self._reader = threading.Thread(target=self._read, daemon=True)
        self._reader.start()

    def _read(self):
        try:
            for raw in self.proc.stdout:
                line = raw.rstrip("\n")
                with self._cv:
                    self.lines.append(Line(time.monotonic(), line))
                    self._cv.notify_all()
        except Exception:
            pass
        finally:
            with self._cv:
                self._closed = True
                self._cv.notify_all()

    # ---- output -------------------------------------------------------
    def mark(self):
        """Index of the next line to arrive; use with since()."""
        with self._cv:
            return len(self.lines)

    def since(self, mark):
        with self._cv:
            return list(self.lines[mark:])

    def wait_for(self, pred, timeout, mark=0):
        """Wait for a line at index >= mark satisfying pred.

        Returns (line, index) or None on deadline. Does not kill the process.
        """
        deadline = time.monotonic() + timeout
        with self._cv:
            while True:
                for i in range(mark, len(self.lines)):
                    if pred(self.lines[i].text):
                        return self.lines[i], i
                if self._closed and self._killed:
                    return None
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return None
                self._cv.wait(min(remaining, 0.05))

    def wait_quiet(self, quiet_s, timeout):
        """Wait until no new line has arrived for quiet_s. Returns bool."""
        deadline = time.monotonic() + timeout
        with self._cv:
            last_len = len(self.lines)
            last_change = time.monotonic()
            while time.monotonic() < deadline:
                if len(self.lines) != last_len:
                    last_len = len(self.lines)
                    last_change = time.monotonic()
                if time.monotonic() - last_change >= quiet_s:
                    return True
                self._cv.wait(0.02)
            return False

    # ---- input --------------------------------------------------------
    def send(self, line):
        if self._killed:
            raise RuntimeError("engine already killed")
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()
        return time.monotonic()

    def uci_handshake(self, timeout=5.0):
        self.send("uci")
        got = self.wait_for(lambda s: s.strip() == "uciok", timeout)
        if got is None:
            raise RuntimeError("no uciok")
        self.send("isready")
        if self.wait_for(lambda s: s.strip() == "readyok", timeout) is None:
            raise RuntimeError("no readyok")
        return True

    def set_option(self, name, value, timeout=5.0):
        mark = self.mark()
        self.send(f"setoption name {name} value {value}")
        # setoption is handled synchronously before the next command, so a
        # round-trip on isready proves it was consumed.
        self.send("isready")
        if self.wait_for(lambda s: s.strip() == "readyok", timeout, mark) is None:
            raise RuntimeError(f"no readyok after setoption {name}")

    def new_game(self, timeout=5.0):
        mark = self.mark()
        self.send("ucinewgame")
        self.send("isready")
        if self.wait_for(lambda s: s.strip() == "readyok", timeout, mark) is None:
            raise RuntimeError("no readyok after ucinewgame")

    # ---- lifecycle ----------------------------------------------------
    def alive(self):
        return self.proc.poll() is None

    def kill(self):
        if self._killed:
            return
        self._killed = True
        try:
            self.proc.send_signal(signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        with self._cv:
            self._cv.notify_all()

    def close(self):
        """Clean quit if the engine is still talking; kill as a fallback."""
        if self._killed:
            return
        try:
            self.send("quit")
            self.proc.wait(timeout=5)
        except Exception:
            pass
        if self.proc.poll() is None:
            self.kill()
        with self._cv:
            self._cv.notify_all()


# ---- parsing helpers --------------------------------------------------
def is_bestmove(text):
    return text.startswith("bestmove ")


def parse_bestmove(text):
    """('e2e4', 'e7e5') from 'bestmove e2e4 ponder e7e5'."""
    parts = text.split()
    if len(parts) < 2:
        return None, None
    best = parts[1]
    ponder = None
    if len(parts) >= 4 and parts[2] == "ponder":
        ponder = parts[3]
    return best, ponder


def parse_info(text):
    """dict of the numeric/string fields of an 'info depth ...' line."""
    if not text.startswith("info depth "):
        return None
    out = {}
    parts = text.split()
    i = 0
    while i < len(parts):
        key = parts[i]
        if key in ("depth", "seldepth", "multipv", "nodes", "nps", "hashfull", "time", "tbhits"):
            try:
                out[key] = int(parts[i + 1])
            except (IndexError, ValueError):
                pass
            i += 2
        elif key == "score":
            j = i + 1
            kind = None
            val = None
            while j < len(parts) and parts[j] not in ("nodes", "nps", "pv", "hashfull", "time", "seldepth",
                                                       "multipv", "tbhits"):
                if parts[j] in ("cp", "mate"):
                    kind = parts[j]
                    try:
                        val = int(parts[j + 1])
                    except (IndexError, ValueError):
                        pass
                    j += 2
                else:
                    j += 1
            out["score"] = (kind, val)
            i = j
        elif key == "pv":
            out["pv"] = parts[i + 1:]
            i = len(parts)
        else:
            i += 1
    return out


def info_lines(lines):
    return [(l, parse_info(l.text)) for l in lines if parse_info(l.text)]


def bestmoves(lines):
    return [l for l in lines if is_bestmove(l.text)]


if __name__ == "__main__":
    # Smoke: handshake, then one bounded depth search.
    exe = sys.argv[1] if len(sys.argv) > 1 else "/tmp/forge-build/forge"
    e = Engine(exe)
    e.uci_handshake()
    e.set_option("OwnBook", "false")
    mark = e.mark()
    e.send("position startpos")
    e.send("go depth 6")
    got = e.wait_for(is_bestmove, 20.0, mark)
    print("bestmove:", got[0].text if got else "CAPPED")
    e.close()
