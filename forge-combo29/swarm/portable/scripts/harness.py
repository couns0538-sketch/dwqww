"""UCI harness: no EOF during search, os.read on a raw fd, one process per request.

Written against the traps in forge-findings.md §7:
  - item 1: a terminator/EOF during a search fabricates a bestmove with zero info lines.
  - item 2: select()+readline() on a buffered pipe is not a timeout; use os.read(fd).
  - item 3: warm process state shifts scores; ucinewgame is the only cold reset.
"""

import os
import select
import subprocess
import time

import paths


class Engine:
    def __init__(self, exe, hash_mb=16, threads=1, nnue=True, book=False, extra=()):
        # The executable is validated before it reaches Popen: it must exist, be a
        # regular file, and carry the execute bit. Passing an unvalidated argv
        # straight into a process launch is what turns a typo in a variant name
        # into an unexplained empty result.
        self.exe = paths.engine_arg(exe)
        # argv is a list (no shell), and self.exe is already resolved to a real,
        # executable regular file by paths.engine_arg(). Launching the binary the
        # operator names is this harness's whole purpose, so the rule is reviewed
        # rather than avoided.
        self.proc = subprocess.Popen(  # NOSONAR - argv list, no shell, exe validated above
            [self.exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=0,
        )
        self.buf = b""
        self.send("uci")
        self.read_until("uciok", timeout=30)
        self.setoption("Hash", hash_mb)
        self.setoption("Threads", threads)
        self.setoption("OwnBook", "true" if book else "false")
        self.setoption("UseNNUE", "true" if nnue else "false")
        for name, value in extra:
            self.setoption(name, value)
        self.isready()

    def send(self, line):
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def setoption(self, name, value):
        self.send(f"setoption name {name} value {value}")

    def isready(self):
        self.send("isready")
        self.read_until("readyok", timeout=60)

    def _read_available(self, timeout):
        """Return new bytes or b'' on timeout. os.read on the raw fd, per §7 item 2."""
        fd = self.proc.stdout.fileno()
        ready, _, _ = select.select([fd], [], [], timeout)
        if not ready:
            return None
        chunk = os.read(fd, 65536)
        if not chunk:
            raise RuntimeError(f"engine exited unexpectedly; buffered={self.buf!r}")
        self.buf += chunk
        return chunk

    def read_until(self, token, timeout=120.0):
        deadline = time.monotonic() + timeout
        while True:
            idx = self.buf.find(token.encode())
            if idx >= 0:
                end = idx + len(token)
                line_end = self.buf.find(b"\n", end)
                if line_end < 0:
                    line_end = len(self.buf)
                out = self.buf[:line_end].decode(errors="replace")
                self.buf = self.buf[line_end + 1:] if line_end < len(self.buf) else b""
                return out
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"no {token!r} within {timeout}s; buffered={self.buf[-500:]!r}")
            self._read_available(min(remaining, 1.0))

    def command(self, line, wait_for="bestmove", timeout=300.0):
        self.send(line)
        return self.read_until(wait_for, timeout=timeout)

    def close(self):
        try:
            self.send("quit")
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()


def parse_info(text):
    """Last info line before the bestmove, as a dict of its integer fields."""
    last = {}
    for line in text.splitlines():
        if not line.startswith("info "):
            continue
        toks = line.split()
        row = {"pv": []}
        i = 1
        while i < len(toks):
            k = toks[i]
            if k == "pv":
                row["pv"] = toks[i + 1:]
                break
            if k in ("depth", "seldepth", "multipv", "nodes", "nps", "hashfull", "time"):
                try:
                    row[k] = int(toks[i + 1])
                except (IndexError, ValueError):
                    pass
                i += 2
                continue
            if k == "score":
                row["score_kind"] = toks[i + 1] if i + 1 < len(toks) else ""
                try:
                    row["score"] = int(toks[i + 2])
                except (IndexError, ValueError):
                    pass
                i += 3
                continue
            i += 1
        last = row
    best = ""
    for line in text.splitlines():
        if line.startswith("bestmove "):
            best = line.split()[1]
    return last, best


def search(exe, fen_or_moves, limits, timeout=300.0, hash_mb=16, nnue=True,
           book=False, ucinewgame=True, extra=()):
    """One cold search in a fresh process. Returns (info_dict, bestmove, wall_seconds)."""
    eng = Engine(exe, hash_mb=hash_mb, nnue=nnue, book=book, extra=extra)
    try:
        if ucinewgame:
            eng.send("ucinewgame")
            eng.isready()
        eng.send(fen_or_moves)
        t0 = time.monotonic()
        text = eng.command(limits, timeout=timeout)
        wall = time.monotonic() - t0
    finally:
        eng.close()
    info, best = parse_info(text)
    return info, best, wall
