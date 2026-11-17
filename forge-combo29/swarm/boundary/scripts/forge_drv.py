"""Minimal, honest UCI driver for forge.

Rules enforced here (from brief-late.md):
  * never send `quit` while a search is live -- we read to `bestmove` first;
  * a refused FEN is detected from the `position fen` reply, not the search output,
    and is raised as RefusedFen so a caller can never record its result;
  * every record carries the `info` lines verbatim so a null can be proved.

One process serves many searches. Each `position` command resets the root, so the
boundary families do not depend on TT state carried across positions.
"""
import subprocess
import threading
import queue
import re

REFUSED = "invalid FEN"


class RefusedFen(Exception):
    """Engine replied `info string invalid FEN: ...`; previous board was kept."""


class NoSearch(Exception):
    """No bestmove arrived in time."""


def _last_int(infos, key):
    for line in reversed(infos):
        m = re.search(r"\b%s (\d+)" % key, line)
        if m:
            return int(m.group(1))
    return None


class Rec:
    __slots__ = ("fen", "go", "bestmove", "infos", "raw", "refused")

    def __init__(self, fen, go):
        self.fen = fen
        self.go = go
        self.bestmove = None
        self.infos = []
        self.raw = []
        self.refused = False

    @property
    def last_info(self):
        return self.infos[-1] if self.infos else None

    def depth(self):
        return _last_int(self.infos, "depth")

    def seldepth(self):
        return _last_int(self.infos, "seldepth")

    def nodes(self):
        return _last_int(self.infos, "nodes")

    def score(self):
        """Return ('mate', n) or ('cp', n) from the last info line, or None."""
        for line in reversed(self.infos):
            m = re.search(r"\bscore (mate|cp) (-?\d+)", line)
            if m:
                return (m.group(1), int(m.group(2)))
        return None

    def pv(self):
        for line in reversed(self.infos):
            m = re.search(r"\bpv\b(.*)$", line)
            if m:
                return m.group(1).split()
        return []

    def pv_shape(self):
        """'absent' | 'empty' | 'moves'.

        The report's main client finding is that an empty (`pv` printed with
        nothing after it) and an absent (`pv` never printed) mean different
        things, so the two must never be collapsed into one `[]`.
        """
        last = self.last_info
        if last is None:
            return "absent"
        if not re.search(r"\bpv\b", last):
            return "absent"
        tail = last.split(" pv", 1)[1] if " pv" in last else last.split("pv", 1)[1]
        return "moves" if tail.strip() else "empty"

    def info_strings(self):
        out = []
        for line in self.infos:
            m = re.match(r"info string (.*)$", line)
            if m:
                out.append(m.group(1))
        return out

    def __repr__(self):
        return f"<Rec {self.bestmove} {self.score()} nodes={self.nodes()} infos={len(self.infos)}>"


class Forge:
    def __init__(self, exe, options=None, timeout=180.0):
        self.exe = exe
        self.timeout = timeout
        self.p = subprocess.Popen(
            [exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, bufsize=1,
        )
        self.q = queue.Queue()
        self.t = threading.Thread(target=self._pump, daemon=True)
        self.t.start()
        self.send("uci")
        self._await(lambda ln: ln.startswith("uciok"))
        for k, v in (options or {}).items():
            self.send(f"setoption name {k} value {v}")
        self.send("isready")
        self._await(lambda ln: ln == "readyok")

    def _pump(self):
        for line in self.p.stdout:
            self.q.put(line.rstrip("\n"))
        self.q.put(None)

    def send(self, cmd):
        self.p.stdin.write(cmd + "\n")
        self.p.stdin.flush()

    def _await(self, pred, collect=None):
        while True:
            try:
                line = self.q.get(timeout=self.timeout)
            except queue.Empty:
                raise NoSearch(f"timeout after {self.timeout}s")
            if line is None:
                raise NoSearch("engine closed stdout")
            if collect is not None:
                collect.append(line)
            if pred(line):
                return line

    def set_position(self, fen=None, moves=None):
        """Set the board. Raises RefusedFen if the engine refused the FEN."""
        if fen is None:
            cmd = "position startpos"
        else:
            cmd = f"position fen {fen}"
        if moves:
            cmd += " moves " + " ".join(moves)
        collect = []
        self.send(cmd)
        # `position` is silent on success, so drain the pipe with a cheap
        # deterministic query and inspect what came back for a refusal.
        self.send("isready")
        self._await(lambda ln: ln == "readyok", collect=collect)
        for line in collect:
            if REFUSED in line:
                raise RefusedFen(line.strip())

    def search(self, fen, go, moves=None):
        rec = Rec(fen, go)
        self.set_position(fen, moves)
        self.send(go)
        self._await(lambda ln: ln.startswith("bestmove"), collect=rec.raw)
        rec.infos = [ln for ln in rec.raw if ln.startswith("info")]
        bm = rec.raw[-1].split()
        rec.bestmove = bm[1] if len(bm) > 1 else None
        self.send("isready")
        self._await(lambda ln: ln == "readyok")
        return rec

    def raw_command(self, cmd, wait_for="readyok"):
        collect = []
        self.send(cmd)
        self.send("isready")
        try:
            self._await(lambda ln: ln == wait_for, collect=collect)
        except NoSearch:
            pass
        return collect

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()
