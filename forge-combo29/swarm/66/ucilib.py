"""ucilib.py - hardened UCI driver for the swarm-66 clock audit.

Rules this module enforces for every caller:
  * stdout is drained by a daemon thread using os.read on the fd. Never
    select() + readline(): the text wrapper buffers ahead and that pattern
    reports false hangs (measured elsewhere in this repo).
  * Every line is stored with its monotonic arrival time, so a search time is
    "bestmove arrival minus go write", not an estimate.
  * `isready` waits are bounded. A search waits for `bestmove` with an explicit
    timeout and never blocks forever.
  * `position` is followed by `isready` and the reply is scanned for
    "invalid FEN" BEFORE the search is allowed to run. The `go` output is
    scanned again. The diagnostic moves between those two places depending on
    whether an `isready` sits between them (measured: position reply when it
    does, go output when it does not), so both are scanned and the go-side
    result is not trusted on its own.
  * Every FEN is validated with python-chess before it is sent, because an
    illegal FEN makes the engine silently search the PREVIOUS position.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import threading
import time

import chess


class EngineError(RuntimeError):
    pass


class Engine:
    """One engine process, line-oriented, time-stamped."""

    def __init__(self, path, argv=()):
        self.path = path
        self.proc = subprocess.Popen(
            [path, *argv],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
            close_fds=True,
        )
        self._in = self.proc.stdin.fileno()
        self._out = self.proc.stdout.fileno()
        self._lines = []          # list[tuple[float, str]]
        self._cursor = 0          # first unread index
        self._cond = threading.Condition()
        self._eof = False
        self._pump_thread = threading.Thread(target=self._pump, daemon=True)
        self._pump_thread.start()

    # -- reader ------------------------------------------------------------
    def _pump(self):
        buf = b""
        while True:
            try:
                chunk = os.read(self._out, 65536)
            except OSError:
                break
            if not chunk:
                break
            buf += chunk
            while b"\n" in buf:
                raw, buf = buf.split(b"\n", 1)
                text = raw.decode("utf-8", "replace").rstrip("\r")
                stamp = time.monotonic()
                with self._cond:
                    self._lines.append((stamp, text))
                    self._cond.notify_all()
        if buf:
            with self._cond:
                self._lines.append((time.monotonic(), buf.decode("utf-8", "replace")))
        with self._cond:
            self._eof = True
            self._cond.notify_all()

    # -- io ----------------------------------------------------------------
    def send(self, command):
        """Write one command line. Returns the monotonic send time."""
        stamp = time.monotonic()
        os.write(self._in, (command + "\n").encode())
        return stamp

    def wait_for(self, predicate, timeout, since=0):
        """Wait for a line satisfying predicate.

        Returns (line_or_None, [(t, text), ...], elapsed_seconds). The returned
        list is every line consumed since index `since`, so callers can scan a
        whole reply for diagnostics.
        """
        started = time.monotonic()
        with self._cond:
            base = since
            deadline = started + timeout
            while True:
                while self._cursor < len(self._lines):
                    stamp, text = self._lines[self._cursor]
                    self._cursor += 1
                    if predicate(text):
                        return text, self._lines[base:self._cursor], time.monotonic() - started
                if self._eof:
                    return None, self._lines[base:self._cursor], time.monotonic() - started
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return None, self._lines[base:self._cursor], time.monotonic() - started
                self._cond.wait(remaining)

    def mark(self):
        with self._cond:
            return self._cursor

    def lines_since(self, index):
        with self._cond:
            return list(self._lines[index:])

    # -- protocol ----------------------------------------------------------
    def uci(self, timeout=10.0):
        self.send("uci")
        line, seen, _ = self.wait_for(lambda t: t == "uciok", timeout)
        if line is None:
            raise EngineError("no uciok from %s" % self.path)
        return [t for _, t in seen]

    def isready(self, timeout=10.0):
        start = self.mark()
        self.send("isready")
        line, seen, _ = self.wait_for(lambda t: t == "readyok", timeout, since=start)
        return line is not None, [t for _, t in seen]

    def setoption(self, name, value):
        self.send("setoption name %s value %s" % (name, value))

    def newgame(self):
        self.send("ucinewgame")
        ok, _ = self.isready()
        return ok

    def set_position(self, fen=None, moves=(), timeout=10.0):
        """Set the position and CONSUME the reply up to readyok.

        The returned dict carries `invalid_fen` from the position reply only.
        Callers must still scan the go output as well.
        """
        command = "position startpos" if fen is None else "position fen %s" % fen
        if moves:
            command += " moves " + " ".join(moves)
        start = self.mark()
        self.send(command)
        self.send("isready")
        line, seen, _ = self.wait_for(lambda t: t == "readyok", timeout, since=start)
        texts = [t for _, t in seen]
        return {
            "ok": line is not None,
            "lines": texts,
            "invalid_fen": any("invalid FEN" in t for t in texts),
            "command": command,
        }

    def go(self, arguments, timeout, since=None):
        """Run one search and wait for bestmove.

        Returns a dict with elapsed_ms measured from the write of `go` to the
        arrival of `bestmove`, the whole reply, and the parsed last info line.
        Never blocks past `timeout`.
        """
        start = self.mark() if since is None else since
        sent = self.send("go " + arguments)
        line, seen, _ = self.wait_for(lambda t: t.startswith("bestmove"), timeout, since=start)
        received = seen[-1][0] if seen else time.monotonic()
        texts = [t for _, t in seen]
        best = None
        if line is not None:
            parts = line.split()
            best = parts[1] if len(parts) > 1 else ""
        return {
            "go": "go " + arguments,
            "timed_out": line is None,
            "bestmove": best,
            "elapsed_ms": (received - sent) * 1000.0,
            "invalid_fen": any("invalid FEN" in t for t in texts),
            "info": [t for t in texts if t.startswith("info depth")],
            "strings": [t for t in texts if "info string" in t],
            "lines": texts,
            "last_info": parse_info(texts),
        }

    def stop(self, timeout=5.0):
        start = self.mark()
        self.send("stop")
        line, seen, _ = self.wait_for(lambda t: t.startswith("bestmove"), timeout, since=start)
        return line, [t for _, t in seen]

    def quit(self, timeout=5.0):
        try:
            self.send("quit")
        except OSError:
            pass
        try:
            self.proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=timeout)
        try:
            self.proc.stdin.close()
        except OSError:
            pass

    def kill(self):
        try:
            self.proc.kill()
        except OSError:
            pass


_INFO_RE = {
    "depth": re.compile(r"\bdepth (\d+)"),
    "seldepth": re.compile(r"\bseldepth (\d+)"),
    "nodes": re.compile(r"\bnodes (\d+)"),
    "time": re.compile(r"\btime (\d+)"),
    "score": re.compile(r"\bscore (cp|mate) (-?\d+)"),
}


def parse_info(texts):
    """Last `info depth` line, parsed. None when the search printed none."""
    last = None
    for text in texts:
        if text.startswith("info depth"):
            last = text
    if last is None:
        return None
    out = {"line": last}
    for key, pattern in _INFO_RE.items():
        found = pattern.search(last)
        if not found:
            out[key] = None
            continue
        out[key] = (found.group(1), int(found.group(2))) if key == "score" else int(found.group(1))
    return out


# -- FEN validation --------------------------------------------------------

def check_fen(fen):
    """Validate with python-chess. Returns (ok, reason)."""
    board = chess.Board()
    try:
        board.set_fen(fen)
    except ValueError as exc:
        return False, "python-chess refused: %s" % exc
    if not board.is_valid():
        return False, "python-chess is_valid() false: %s" % "; ".join(str(s) for s in board.status())
    return True, ""


def check_line(fen, moves):
    """Validate a FEN plus a move list, all legal, using python-chess."""
    ok, reason = check_fen(fen)
    if not ok:
        return False, reason
    board = chess.Board(fen)
    for index, move in enumerate(moves):
        try:
            parsed = chess.Move.from_uci(move)
        except ValueError:
            return False, "move %d %r is not uci" % (index, move)
        if parsed not in board.legal_moves:
            return False, "move %d %r illegal in %s" % (index, move, board.fen())
        board.push(parsed)
    return True, ""


def require_fen(fen, moves=()):
    ok, reason = check_line(fen, moves)
    if not ok:
        raise EngineError("refusing to send an invalid position: %s" % reason)


# -- reporting -------------------------------------------------------------

def emit(payload, path=None):
    text = json.dumps(payload, indent=2, sort_keys=True)
    print(text)
    if path:
        with open(path, "w") as handle:
            handle.write(text + "\n")
    return payload


class Checker:
    """Collects PASS/FAIL rows and prints real denominators."""

    def __init__(self, title):
        self.title = title
        self.rows = []

    def add(self, name, ok, detail):
        self.rows.append({"check": name, "pass": bool(ok), "detail": detail})
        print("%-4s %-46s %s" % ("PASS" if ok else "FAIL", name, detail))
        return ok

    def summary(self):
        passed = sum(1 for row in self.rows if row["pass"])
        total = len(self.rows)
        print("\n%s: %d/%d checks passed" % (self.title, passed, total))
        return {"title": self.title, "passed": passed, "total": total, "rows": self.rows}


def engine_ready(path):
    """Start one engine, apply the audit's fixed settings, return it."""
    engine = Engine(path)
    engine.uci()
    engine.setoption("Threads", 1)
    engine.setoption("Hash", 32)
    engine.setoption("OwnBook", "false")
    ok, lines = engine.isready()
    if not ok:
        raise EngineError("engine did not answer isready: %r" % lines)
    return engine
