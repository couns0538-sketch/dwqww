"""UCI harness for the repetition / fifty-move / insufficient-material audit.

Two rules are enforced here rather than left to each script:

  1. Every FEN is validated with python-chess before it is sent.
  2. Every reply window is scanned for `info string invalid FEN` /
     `info string illegal move`.  The engine always emits that diagnostic but
     its LOCATION varies: with `isready` after `position` it lands in the
     POSITION reply before `readyok`; without it, in the `go` output ahead of
     the first `info depth` line.  A refusal leaves the previous board in
     place, so reading only one stream misses it half the time and silently
     measures a stale position.  We scan both.

On top of that, `Probe.setup()` asserts `go perft 1` agrees with python-chess
movegen for the board actually loaded, so a silently-stale board cannot be
mistaken for the fixture under test.
"""

import queue
import shutil
import subprocess
import threading
import time

import chess

ENGINE = "build/forge"
TIMEOUT_S = 30.0


class EngineError(RuntimeError):
    pass


REFUSAL_PREFIXES = ("info string invalid FEN", "info string illegal move")


def scan_refusal(where, lines, context=""):
    """Raise if any line in a reply window is a FEN/move refusal.

    Called on both the position reply and the go output; the diagnostic's
    location depends on whether `isready` was sent, so neither stream alone
    is sufficient.
    """
    for line in lines:
        for prefix in REFUSAL_PREFIXES:
            if line.startswith(prefix):
                raise EngineError(
                    "%r refused (%s): %s -- engine kept the previous board"
                    % (context, where, line)
                )


class UciSession:
    """Line-oriented UCI session with an explicit read-until-predicate."""

    def __init__(self, path=ENGINE):
        self.proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.lines = queue.Queue()
        self.transcript = []
        self._reader = threading.Thread(target=self._pump, daemon=True)
        self._reader.start()

    def _pump(self):
        for line in self.proc.stdout:
            line = line.rstrip("\n")
            self.transcript.append(line)
            self.lines.put(line)
        self.lines.put(None)

    def send(self, text):
        assert self.proc.poll() is None, "engine exited"
        self.transcript.append(">>> " + text)
        self.proc.stdin.write(text + "\n")
        self.proc.stdin.flush()

    def read_until(self, predicate, timeout=TIMEOUT_S, what="token"):
        """Collect lines until predicate(line) is true. Returns (match, collected)."""
        collected = []
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise EngineError(
                    "timeout after %.1fs waiting for %s; last=%r" % (timeout, what, collected[-3:])
                )
            try:
                line = self.lines.get(timeout=remaining)
            except queue.Empty:
                continue
            if line is None:
                raise EngineError("engine closed stdout waiting for %s" % what)
            collected.append(line)
            if predicate(line):
                return line, collected

    def sync(self, timeout=TIMEOUT_S):
        self.send("isready")
        self.read_until(lambda l: l.strip() == "readyok", timeout, "readyok")

    def close(self):
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


class Probe:
    """A single fixture loaded into a fresh session, verified, then searched."""

    def __init__(self, fen, name="", moves=None, session=None):
        self.name = name or fen
        self.fen = fen
        self.moves = list(moves or [])
        self._own_session = session is None
        self.uci = session or UciSession()
        self.board = self._validate_fen()
        self.trace = []
        self._loaded()
        self._verify_board()

    # -- fixture validation ------------------------------------------------
    def _validate_fen(self):
        try:
            board = chess.Board(self.fen)
        except ValueError as exc:
            raise EngineError("python-chess rejected FEN %r: %s" % (self.fen, exc))
        for i, move in enumerate(self.moves):
            try:
                board.push_uci(move)
            except ValueError as exc:
                raise EngineError(
                    "python-chess rejected move %r (#%d) in %r: %s" % (move, i, self.fen, exc)
                )
        return board

    # -- engine sync -------------------------------------------------------
    def _position_command(self):
        cmd = "position fen " + self.fen
        if self.moves:
            cmd += " moves " + " ".join(self.moves)
        return cmd

    def _loaded(self):
        """Send `position` and consume its reply, including invalid-FEN refusals."""
        self.uci.send(self._position_command())
        # `position` is synchronous and prints nothing on success.  The only
        # output it can produce is an error diagnostic.  Read the position
        # reply window by syncing, then scan every line of it -- not just the
        # first.  The go window is scanned separately in `search()`.
        self.uci.send("isready")
        _, window = self.uci.read_until(lambda l: l.strip() == "readyok", what="readyok")
        scan_refusal("position reply", window, self.name)

    def _verify_board(self):
        """perft 1 from the engine must match python-chess for the loaded board."""
        expected = len(list(self.board.legal_moves))
        self.uci.send("go perft 1")
        _, collected = self.uci.read_until(lambda l: l.startswith("nodes "), what="perft nodes")
        got = int(collected[-1].split()[1])
        roots = {l.split(":")[0] for l in collected if ":" in l and not l.startswith("info")}
        fen_moves = {m.uci() for m in self.board.legal_moves}
        if got != expected:
            raise EngineError(
                "perft-1 mismatch on %r: engine=%d python-chess=%d -- board not loaded as sent"
                % (self.name, got, expected)
            )
        if roots != fen_moves:
            raise EngineError(
                "perft-1 move set mismatch on %r: only-engine=%s only-oracle=%s"
                % (self.name, sorted(roots - fen_moves), sorted(fen_moves - roots))
            )
        self.perft1 = got

    # -- oracle repetition -------------------------------------------------
    def oracle_repetition_count(self):
        """Occurrences of the current position in the game history (>=1).

        python-chess treats the current board as the last entry of
        move_stack; `is_repetition(n)` requires n prior occurrences, so the
        total occurrence count is the largest n with is_repetition(n) true,
        plus one for the current position.
        """
        n = 1
        while self.board.is_repetition(n + 1):
            n += 1
        return n

    def oracle_threefold(self):
        """True when the position has occurred three or more times."""
        return self.oracle_repetition_count() >= 3

    # -- search ------------------------------------------------------------
    def search(self, limit="depth 6", extra="", guard=True):
        cmd = "go " + limit + ((" " + extra) if extra else "")
        self.uci.send(cmd)
        best, collected = self.uci.read_until(
            lambda l: l.startswith("bestmove") or l.startswith("info string invalid"), what="bestmove"
        )
        if guard:
            # Second half of the two-stream defence: without a preceding
            # isready the refusal lands here, ahead of the first info depth.
            scan_refusal("go output", collected, self.name)
        infos = [l for l in collected if l.startswith("info depth")]
        last = infos[-1] if infos else ""
        nodes, score, depth, pv = 0, None, 0, []
        if last:
            tok = last.split()
            for i, t in enumerate(tok):
                if t == "nodes":
                    nodes = int(tok[i + 1])
                elif t == "score":
                    score = (tok[i + 1], int(tok[i + 2]))
                elif t == "depth":
                    depth = int(tok[i + 1])
                elif t == "pv":
                    pv = tok[i + 1:]
        self.trace.append({"cmd": cmd, "bestmove": best.split()[1], "nodes": nodes,
                           "score": score, "depth": depth, "pv": pv})
        return {"bestmove": best.split()[1], "nodes": nodes, "score": score,
                "depth": depth, "pv": pv, "info_lines": len(infos)}

    def close(self):
        if self._own_session:
            self.uci.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def require_engine(path=ENGINE):
    import os
    if not os.path.exists(path):
        raise EngineError("engine binary missing at %s; run cmake --build build" % path)
    return shutil.which(path) or path
