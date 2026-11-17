"""Minimal UCI driver for the trace build.

Two rules this driver exists to obey, both from earlier seats on this engine:

* Read to `bestmove`; never pipe a command and close stdin. EOF aborts the search
  and the engine then reports a fabricated `bestmove` (0 `info depth` lines).
  A piped harness therefore measures nothing and looks perfectly reproducible.
* One fresh process per cell. `Clear Hash` on this engine is not a cold reset:
  it wipes the table and only the evaluator, leaving history, killers and
  correction tables from the previous search. A reused process would measure
  carried-over state, not table size.

The engine is also checked for refusing a position: `position` replies with
`info string invalid FEN` and the caller must see an `info depth` line before
trusting the answer.
"""

import json
import re
import subprocess
import threading
import time

TRACE_RE = re.compile(r"^trace (\{.*\})\s*$")
BESTMOVE_RE = re.compile(r"^bestmove (\S+)(?: ponder (\S+))?\s*$")
INFODEPTH_RE = re.compile(r"^info depth (\d+)")
SCORE_RE = re.compile(r"score (cp|mate) (-?\d+)")


class EngineError(RuntimeError):
    pass


class Engine:
    """A single engine process. Use `search()` once per process."""

    def __init__(self, binary, hash_mb=16, threads=1, own_book=False, timeout=600.0):
        self.binary = binary
        self.timeout = timeout
        self.proc = subprocess.Popen(
            [binary],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._lines = []
        self._lock = threading.Lock()
        self._eof = False
        self._reader = threading.Thread(target=self._pump, daemon=True)
        self._reader.start()

        self._send("uci")
        self._expect_until("uciok")
        self.setoption("Hash", hash_mb)
        self.setoption("Threads", threads)
        self.setoption("OwnBook", "true" if own_book else "false")
        self._send("isready")
        self._expect_until("readyok")

    def _pump(self):
        for line in self.proc.stdout:
            with self._lock:
                self._lines.append(line.rstrip("\n"))
        with self._lock:
            self._eof = True

    def _send(self, command):
        self.proc.stdin.write(command + "\n")
        self.proc.stdin.flush()

    def _drain(self):
        with self._lock:
            lines, self._lines = self._lines, []
        return lines

    def _expect_until(self, token):
        """Read until a line equals token (or starts with it). Raises on EOF."""
        collected = []
        start = time.monotonic()
        while True:
            with self._lock:
                lines, self._lines = self._lines, []
            for line in lines:
                collected.append(line)
                if line.strip() == token or line.startswith(token):
                    return collected
            if self._eof:
                raise EngineError(f"engine exited before {token!r}; got {collected!r}")
            if time.monotonic() - start > self.timeout:
                raise EngineError(f"timeout waiting for {token!r}")
            time.sleep(0.001)

    def setoption(self, name, value):
        self._send(f"setoption name {name} value {value}")

    def new_game(self, fen="startpos"):
        """True cold reset is `ucinewgame`, per the earlier seat's finding."""
        self._send("ucinewgame")
        self._send("isready")
        self._expect_until("readyok")

    def position(self, fen=None, moves=None):
        command = "position " + (f"fen {fen}" if fen else "startpos")
        if moves:
            command += " moves " + " ".join(moves)
        self._send(command)
        self._send("isready")
        lines = self._expect_until("readyok")
        for line in lines:
            if "invalid FEN" in line or "illegal move" in line:
                raise EngineError(f"position refused: {line}")
        return lines

    def search(self, go_command):
        """Run one search to completion and return the recorded cell."""
        self._send(go_command)
        info = []
        trace = None
        bestmove = None
        start_clock = time.monotonic()
        while True:
            with self._lock:
                lines, self._lines = self._lines, []
            for line in lines:
                match = TRACE_RE.match(line)
                if match:
                    trace = json.loads(match.group(1))
                    continue
                match = BESTMOVE_RE.match(line)
                if match:
                    bestmove = match.group(1)
                    continue
                if line.startswith("info "):
                    info.append(line)
                    continue
            if bestmove is not None:
                break
            if self._eof:
                raise EngineError(f"engine exited without bestmove; last lines {info[-3:]!r}")
            if time.monotonic() - start_clock > self.timeout:
                raise EngineError("timeout waiting for bestmove")
            time.sleep(0.001)

        depths = [int(m.group(1)) for m in map(INFODEPTH_RE.match, info) if m]
        if not depths:
            # The piped-harness fabrication signature: no search actually ran.
            raise EngineError("no info depth line: the search did not run")

        last_score = None
        for line in reversed(info):
            match = SCORE_RE.search(line)
            if match:
                kind, value = match.group(1), int(match.group(2))
                last_score = (kind, value)
                break

        final_depth = depths[-1]
        seldepth = 0
        for line in reversed(info):
            if line.startswith("info depth"):
                parts = line.split()
                for i, token in enumerate(parts):
                    if token == "seldepth" and i + 1 < len(parts):
                        try:
                            seldepth = int(parts[i + 1])
                        except ValueError:
                            pass
                break

        nodes = trace["nodes"] if trace else None
        return {
            "bestmove": bestmove,
            "score": last_score,
            "depth": final_depth,
            "seldepth": seldepth,
            "info_lines": len(info),
            "trace": trace,
            "go": go_command,
        }

    def ttstats(self):
        self._send("ttstats")
        self._send("isready")
        lines = self._expect_until("readyok")
        for line in lines:
            if line.startswith("ttstats "):
                return json.loads(line[len("ttstats "):])
        raise EngineError("no ttstats reply")

    def close(self):
        try:
            self._send("quit")
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def one_cell(binary, fen, go_command, hash_mb, moves=None, timeout=600.0, want_ttstats=False):
    """A full cold cell: new process, hash set, position, one search."""
    with Engine(binary, hash_mb=hash_mb, timeout=timeout) as engine:
        engine.position(fen=fen, moves=moves)
        result = engine.search(go_command)
        if want_ttstats:
            result["ttstats"] = engine.ttstats()
        return result
