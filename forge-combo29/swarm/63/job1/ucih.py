"""Minimal UCI driver with the two-reply invalid-FEN guard.

Protocol facts this encodes (see STATUS.md, "FEN diagnostic"):
  * `position` answers `info string invalid FEN: ...` BEFORE the `readyok` that follows it.
  * The same line, when a `go` follows without an intervening `isready` drain, appears in the
    `go` output ahead of the first `info depth`.
  So every position is validated from BOTH replies, and any refusal raises immediately.
"""
import queue
import re
import subprocess
import threading
import time

INVALID_FEN = "invalid FEN"


class EngineError(RuntimeError):
    pass


class Engine:
    def __init__(self, exe, env=None, name="engine"):
        self.exe = exe
        self.name = name
        self.p = subprocess.Popen(
            [exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, bufsize=1, env=env,
        )
        self.q = queue.Queue()
        self.transcript = []
        self.t = threading.Thread(target=self._pump, daemon=True)
        self.t.start()
        self.send("uci")
        self.banner = self.until("uciok", 20.0)

    def _pump(self):
        for line in self.p.stdout:
            self.q.put(line.rstrip("\n"))
        self.q.put(None)

    def send(self, cmd):
        self.transcript.append(">>> " + cmd)
        try:
            self.p.stdin.write(cmd + "\n")
            self.p.stdin.flush()
        except (BrokenPipeError, ValueError) as exc:
            raise EngineError("engine died before %r: %s" % (cmd, exc))

    def until(self, token, timeout):
        """Read lines until one starts with `token`; return all lines read (token last)."""
        lines = []
        deadline = time.monotonic() + timeout
        while True:
            left = deadline - time.monotonic()
            if left <= 0:
                raise EngineError("timeout %.1fs waiting for %r; got %r" % (timeout, token, lines[-4:]))
            try:
                line = self.q.get(timeout=left)
            except queue.Empty:
                raise EngineError("timeout %.1fs waiting for %r" % (timeout, token))
            if line is None:
                raise EngineError("engine EOF waiting for %r; got %r" % (token, lines[-4:]))
            self.transcript.append(line)
            lines.append(line)
            if line.split(" ") and line.startswith(token):
                return lines

    def ready(self, timeout=30.0):
        self.send("isready")
        return self.until("readyok", timeout)

    def position(self, fen=None, moves=None, timeout=30.0):
        """Set a position and return (position_reply, go_prefix_sentinel).

        The position reply is drained with isready, so a refusal is caught here. The caller's
        `go` output is scanned separately by `go()`.
        """
        if fen is None:
            cmd = "position startpos"
        else:
            cmd = "position fen " + fen
        if moves:
            cmd += " moves " + " ".join(moves)
        self.send(cmd)
        reply = self.ready(timeout)
        self.check_fen(reply, "position reply")
        return reply

    def check_fen(self, lines, where):
        for line in lines:
            if INVALID_FEN in line:
                raise EngineError("%s refused: %r" % (where, line))

    def perft(self, n, timeout=120.0):
        """`go perft n` does NOT send bestmove: it ends with `Nodes searched: N`."""
        self.send("go perft %d" % n)
        lines = []
        deadline = time.monotonic() + timeout
        while True:
            left = deadline - time.monotonic()
            if left <= 0:
                raise EngineError("timeout %.1fs waiting for Nodes searched (perft %d)" % (timeout, n))
            try:
                line = self.q.get(timeout=left)
            except queue.Empty:
                raise EngineError("timeout %.1fs waiting for Nodes searched (perft %d)" % (timeout, n))
            if line is None:
                raise EngineError("engine EOF in perft %d" % n)
            self.transcript.append(line)
            lines.append(line)
            if INVALID_FEN in line:
                raise EngineError("perft refused the position: %r" % line)
            if line.startswith("Nodes searched:"):
                return lines, int(line.split()[2])
            # this engine's perft summary is a bare "nodes N" line
            if line.startswith("nodes "):
                return lines, int(line.split()[1])

    def go(self, gocmd, timeout=60.0):
        """Send `go ...`, scan for invalid FEN, read to bestmove. Returns (lines, bestmove, info)."""
        self.send(gocmd)
        lines = []
        deadline = time.monotonic() + timeout
        while True:
            left = deadline - time.monotonic()
            if left <= 0:
                raise EngineError("timeout %.1fs waiting for bestmove after %r" % (timeout, gocmd))
            try:
                line = self.q.get(timeout=left)
            except queue.Empty:
                raise EngineError("timeout %.1fs waiting for bestmove after %r" % (timeout, gocmd))
            if line is None:
                raise EngineError("engine EOF waiting for bestmove after %r" % gocmd)
            self.transcript.append(line)
            lines.append(line)
            if INVALID_FEN in line:
                raise EngineError("go output refused the position: %r (position was never applied)" % line)
            if line.startswith("bestmove"):
                parts = line.split()
                bm = parts[1] if len(parts) > 1 else None
                return lines, bm, [l for l in lines if l.startswith("info depth")]

    def nodes_from(self, info_lines):
        """Last `nodes N` in the info lines, or 0 when no info line carried one."""
        best = 0
        for line in info_lines:
            m = re.search(r"\bnodes (\d+)", line)
            if m:
                best = int(m.group(1))
        return best

    def quit(self):
        try:
            self.send("quit")
            self.p.wait(timeout=20)
        except Exception:
            try:
                self.p.kill()
            except Exception:
                pass


def engine_id(exe):
    e = Engine(exe)
    ident = [l for l in e.banner if l.startswith("id name")]
    e.quit()
    return ident[0] if ident else "(no id name)"
