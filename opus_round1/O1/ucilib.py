#!/usr/bin/env python3
"""Small UCI driver used by the O1 SMP scripts: non-blocking line reader with timeouts (a missing
reply within the timeout is reported as a hang), crash detection, and legal-move lookup.
Legal moves come from python-chess when it is installed (independent move generator); otherwise
from `go perft 1` of a separate reference engine process (the lock exe, whose move generator is
pinned by perft 5 / kiwipete)."""
import queue
import subprocess
import threading
import time


class EngineError(RuntimeError):
    pass


class Engine:
    def __init__(self, exe, name="engine", log=None):
        self.name = name
        self.log = log
        self.proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.lines = queue.Queue()
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        for line in self.proc.stdout:
            self.lines.put(line.rstrip("\r\n"))
        self.lines.put(None)  # EOF

    def send(self, text):
        if self.log:
            self.log.write(f"> {text}\n")
        try:
            self.proc.stdin.write(text + "\n")
            self.proc.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise EngineError(f"{self.name}: write failed ({exc}); exit code {self.proc.poll()}")

    def expect(self, predicate, timeout, what):
        """Return (matching line, lines seen before it); EngineError on EOF or timeout."""
        seen = []
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise EngineError(f"{self.name}: HANG - no {what} within {timeout:.1f}s; last lines {seen[-5:]}")
            try:
                line = self.lines.get(timeout=remaining)
            except queue.Empty:
                continue
            if line is None:
                raise EngineError(f"{self.name}: CRASH/EXIT while waiting for {what} (exit code {self.proc.wait()}); "
                                  f"last lines {seen[-5:]}")
            if self.log:
                self.log.write(f"< {line}\n")
            if predicate(line):
                return line, seen
            seen.append(line)

    def handshake(self, options=()):
        self.send("uci")
        self.expect(lambda l: l == "uciok", 60, "uciok")
        for name, value in options:
            self.send(f"setoption name {name} value {value}")
        self.ready(60)

    def ready(self, timeout):
        t0 = time.monotonic()
        self.send("isready")
        self.expect(lambda l: l == "readyok", timeout, "readyok")
        return time.monotonic() - t0

    def quit(self, timeout=60):
        try:
            self.send("quit")
        except EngineError:
            pass
        try:
            return self.proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            raise EngineError(f"{self.name}: HANG on quit")


class LegalMoves:
    """legal(fen, moves) -> set of UCI moves legal after `position fen <fen> moves <moves>`."""

    def __init__(self, reference_exe=None):
        try:
            import chess  # noqa: F401
            self.chess = chess
            self.ref = None
            self.source = f"python-chess {chess.__version__}"
        except ImportError:
            if not reference_exe:
                raise SystemExit("python-chess is not installed: pass a reference engine for legal moves")
            self.chess = None
            self.ref = Engine(reference_exe, "reference")
            self.ref.handshake()
            self.source = f"reference engine perft 1 ({reference_exe})"
        self.cache = {}

    def legal(self, fen, moves=()):
        key = (fen, tuple(moves))
        if key in self.cache:
            return self.cache[key]
        if self.chess:
            board = self.chess.Board(fen) if fen != "startpos" else self.chess.Board()
            for m in moves:
                board.push_uci(m)
            result = {m.uci() for m in board.legal_moves}
        else:
            pos = "position startpos" if fen == "startpos" else f"position fen {fen}"
            if moves:
                pos += " moves " + " ".join(moves)
            self.ref.send(pos)
            self.ref.send("go perft 1")
            _, seen = self.ref.expect(lambda l: l.startswith("nodes "), 60, "perft nodes")
            result = {l.split(":")[0] for l in seen if ":" in l}
        self.cache[key] = result
        return result

    def close(self):
        if self.ref:
            self.ref.quit()


def read_positions(path, limit=None):
    """'<FEN> ; <id>' lines (positions50.fen) or EPD lines (forge-10000.epd)."""
    out = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        if " ; " in line:
            fen = line.split(" ; ")[0].strip()
        else:
            fields = line.split()
            fen = " ".join(fields[:4]) + " 0 1"
        out.append(fen)
        if limit and len(out) >= limit:
            break
    return out
