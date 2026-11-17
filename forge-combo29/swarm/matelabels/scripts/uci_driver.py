"""Minimal UCI driver that never sends a command into a live search.

Rule 1 of the brief: piping `quit` into a live search makes forge abort and
fabricate a `bestmove` with zero `info` lines. This driver writes one command,
then reads stdout until the expected terminator arrives, and only then writes
anything else.
"""
import queue
import subprocess
import threading
import time


class Uci:
    def __init__(self, path, options=None, startup_timeout=60.0):
        self.proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.lines = queue.Queue()
        self.stderr_lines = []
        self._out_thread = threading.Thread(target=self._pump_out, daemon=True)
        self._err_thread = threading.Thread(target=self._pump_err, daemon=True)
        self._out_thread.start()
        self._err_thread.start()
        self.send("uci")
        self._read_until(lambda l: l.strip() == "uciok", startup_timeout)
        for name, value in (options or {}).items():
            self.send(f"setoption name {name} value {value}")
        self.send("isready")
        ready = self._read_until(lambda l: l.strip() == "readyok", startup_timeout)
        if not ready[0]:
            raise RuntimeError("engine never became ready")

    def _pump_out(self):
        for line in self.proc.stdout:
            self.lines.put(line)
        self.lines.put(None)

    def _pump_err(self):
        for line in self.proc.stderr:
            self.stderr_lines.append(line.rstrip("\n"))

    def send(self, cmd):
        self.proc.stdin.write(cmd + "\n")
        self.proc.stdin.flush()

    def _read_until(self, pred, timeout):
        """Read lines until pred(line) is true. Returns (found, lines, elapsed)."""
        collected = []
        start = time.monotonic()
        deadline = start + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return (False, collected, time.monotonic() - start)
            try:
                line = self.lines.get(timeout=remaining)
            except queue.Empty:
                return (False, collected, time.monotonic() - start)
            if line is None:
                return (False, collected, time.monotonic() - start)
            line = line.rstrip("\n")
            collected.append(line)
            if pred(line):
                return (True, collected, time.monotonic() - start)

    def position(self, fen, moves=()):
        cmd = f"position fen {fen}"
        if moves:
            cmd += " moves " + " ".join(moves)
        self.send(cmd)

    def search(self, go_cmd, timeout=60.0):
        """Run one search to completion. Returns (bestmove, info_lines, elapsed, timed_out).

        The engine is only spoken to after `bestmove` is seen, so no command can
        land inside a live search.
        """
        self.send(go_cmd)
        found, lines, elapsed = self._read_until(
            lambda l: l.startswith("bestmove"), timeout
        )
        info = [l for l in lines if l.startswith("info")]
        best = None
        for l in lines:
            if l.startswith("bestmove"):
                best = l.split()[1]
                break
        return best, info, elapsed, (not found)

    def isready(self, timeout=30.0):
        self.send("isready")
        found, _lines, _elapsed = self._read_until(lambda l: l.strip() == "readyok", timeout)
        return found

    def quit(self):
        try:
            self.send("quit")
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()


def parse_score(info_line):
    """Extract (depth, multipv, score_kind, score_value, nodes, pv) from an info line."""
    tok = info_line.split()
    if "score" not in tok:
        return None
    d = {"depth": None, "multipv": 1, "kind": None, "value": None, "nodes": None, "pv": []}
    i = 0
    while i < len(tok):
        t = tok[i]
        if t == "depth" and i + 1 < len(tok):
            d["depth"] = int(tok[i + 1]); i += 2
        elif t == "multipv" and i + 1 < len(tok):
            d["multipv"] = int(tok[i + 1]); i += 2
        elif t == "nodes" and i + 1 < len(tok):
            d["nodes"] = int(tok[i + 1]); i += 2
        elif t == "score" and i + 2 < len(tok):
            d["kind"] = tok[i + 1]
            d["value"] = int(tok[i + 2]); i += 3
        elif t == "pv":
            d["pv"] = tok[i + 1:]; break
        else:
            i += 1
    return d


def last_score_per_multipv(info_lines, depth=None):
    """Return {multipv: parsed} keeping the last line seen for each multipv index."""
    out = {}
    for line in info_lines:
        p = parse_score(line)
        if p is None or p["kind"] is None:
            continue
        if depth is not None and p["depth"] != depth:
            continue
        out[p["multipv"]] = p
    return out
