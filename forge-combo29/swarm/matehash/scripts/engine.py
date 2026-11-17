"""UCI driver for forge-combo29 that never lets EOF reach a running search.

Rule 1 of the audit brief: a `quit` (or EOF) that arrives while a search is live
makes the engine fabricate a `bestmove` with zero `info` lines. So every search
here is sent, then read until `bestmove`, and only then is the next command sent.
The process is closed by sending `quit` only when no search is in flight.
"""

import os
import re
import select
import subprocess
import time

INFO_RE = re.compile(r"^info\b")
DEPTH_RE = re.compile(r"\bdepth (\d+)")
SELDEPTH_RE = re.compile(r"\bseldepth (\d+)")
NODES_RE = re.compile(r"\bnodes (\d+)")
TIME_RE = re.compile(r"\btime (\d+)")
SCORE_RE = re.compile(r"\bscore (cp|mate) (-?\d+)")
PV_RE = re.compile(r"\bpv (.+)$")
MATE_SCORE_RE = re.compile(r"^mate (-?\d+)$")


class EngineError(RuntimeError):
    pass


def parse_info(line):
    """Turn one `info` line into a dict. Only `score`/`pv`/`depth` are kept."""
    rec = {"raw": line}
    m = DEPTH_RE.search(line)
    if m:
        rec["depth"] = int(m.group(1))
    m = SELDEPTH_RE.search(line)
    if m:
        rec["seldepth"] = int(m.group(1))
    m = NODES_RE.search(line)
    if m:
        rec["nodes"] = int(m.group(1))
    m = TIME_RE.search(line)
    if m:
        rec["time"] = int(m.group(1))
    m = SCORE_RE.search(line)
    if m:
        rec["score_kind"] = m.group(1)
        rec["score"] = int(m.group(2))
    m = PV_RE.search(line)
    if m:
        rec["pv"] = m.group(1).strip().split()
    return rec


class Engine:
    """One long-lived engine process, driven strictly request/response."""

    def __init__(self, path, hash_mb=64, threads=1, options=None):
        self.path = path
        self.proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        self._dead = False
        self._buf = b""
        self.send("uci")
        self.read_until(lambda l: l.strip() == "uciok", timeout=10.0)
        self.setoption("Hash", hash_mb)
        self.setoption("Threads", threads)
        for name, value in (options or {}).items():
            self.setoption(name, value)

    # -- raw io ---------------------------------------------------------

    def send(self, line):
        if self._dead:
            raise EngineError("engine already stopped")
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def _readline(self, timeout):
        fd = self.proc.stdout.fileno()
        deadline = time.monotonic() + timeout
        while True:
            if b"\n" in self._buf:
                line, _, self._buf = self._buf.partition(b"\n")
                return line.decode(errors="replace")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise EngineError("timeout waiting for engine output")
            r, _, _ = select.select([fd], [], [], remaining)
            if not r:
                continue
            chunk = os.read(fd, 65536)
            if not chunk:
                raise EngineError("engine closed stdout (died?)")
            self._buf += chunk

    def read_until(self, predicate, timeout=60.0, collect=None):
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise EngineError("timeout in read_until")
            line = self._readline(remaining)
            if collect is not None:
                collect.append(line)
            if predicate(line):
                return line

    # -- uci ------------------------------------------------------------

    def setoption(self, name, value):
        self.send(f"setoption name {name} value {value}")

    def ucinewgame(self):
        """True cold reset: Searcher::clear() wipes histories AND the table."""
        self.send("ucinewgame")
        self.send("isready")
        self.read_until(lambda l: l.strip() == "readyok", timeout=30.0)

    def isready(self):
        self.send("isready")
        self.read_until(lambda l: l.strip() == "readyok", timeout=30.0)

    def position(self, fen=None, moves=None):
        if fen is None:
            cmd = "position startpos"
        else:
            cmd = f"position fen {fen}"
        if moves:
            cmd += " moves " + " ".join(moves)
        self.send(cmd)

    def go(self, **limits):
        parts = ["go"]
        for key, value in limits.items():
            if value is True:
                parts.append(key)
            else:
                parts.append(f"{key} {value}")
        self.send(" ".join(parts))
        lines = []
        last = self.read_until(lambda l: l.startswith("bestmove"), timeout=limits.get("_timeout", 300.0), collect=lines)
        bestmove = last.split()[1] if len(last.split()) > 1 else None
        infos = [parse_info(l) for l in lines if INFO_RE.match(l)]
        return {"bestmove": bestmove, "infos": infos, "lines": lines}

    def quit(self):
        if self._dead:
            return
        try:
            self.send("quit")
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()
        finally:
            self._dead = True

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.quit()
        return False


def final_score(result):
    """The score of the last `info depth` line, or None if the search said nothing."""
    scored = [i for i in result["infos"] if "score" in i and "depth" in i]
    if not scored:
        return None
    return scored[-1]


def mate_distance(result):
    """Reported mate distance in MOVES (UCI convention) or None."""
    last = final_score(result)
    if last is None or last.get("score_kind") != "mate":
        return None
    return last["score"]


def search(path, fen, moves=None, limits=None, hash_mb=64, cold=True, options=None, timeout=300.0):
    """One complete, isolated search in its own process. The safe default."""
    limits = dict(limits or {"depth": 8})
    limits["_timeout"] = timeout
    with Engine(path, hash_mb=hash_mb, options=options) as eng:
        if cold:
            eng.ucinewgame()
        eng.position(fen, moves)
        return eng.go(**limits)
