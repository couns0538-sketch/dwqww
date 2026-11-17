"""Minimal UCI driver for the Forge info-field audit.

Two hard rules from the brief are enforced here rather than trusted:

  * a search is never terminated by piping `quit` into stdin; we always read to
    the `bestmove` line first, and `stop` is the only way a live search is cut;
  * every command gets its own write + read-to-bestmove cycle, so a reader can
    never consume a stale line from a previous search.
"""

import queue
import subprocess
import threading
import time


class Engine:
    def __init__(self, path):
        self.path = path
        self.proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.lines = queue.Queue()
        self._reader = threading.Thread(target=self._pump, daemon=True)
        self._reader.start()

    def _pump(self):
        for line in self.proc.stdout:
            self.lines.put(line.rstrip("\n"))
        self.lines.put(None)

    def send(self, command):
        self.proc.stdin.write(command + "\n")
        self.proc.stdin.flush()

    def read_until(self, predicate, timeout=120.0):
        """Collect lines until predicate(line) is true. Raises on timeout."""
        out = []
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("timeout after %ss; last=%r" % (timeout, out[-1:]))
            try:
                line = self.lines.get(timeout=remaining)
            except queue.Empty:
                raise TimeoutError("timeout after %ss; last=%r" % (timeout, out[-1:]))
            if line is None:
                raise RuntimeError("engine closed stdout")
            out.append(line)
            if predicate(line):
                return out

    def handshake(self):
        self.send("uci")
        uci = self.read_until(lambda l: l.strip() == "uciok")
        self.send("isready")
        self.read_until(lambda l: l.strip() == "readyok")
        return uci

    def setoption(self, name, value):
        self.send("setoption name %s value %s" % (name, value))
        self.send("isready")
        self.read_until(lambda l: l.strip() == "readyok")

    def position(self, fen=None, moves=()):
        cmd = "position startpos" if fen is None else "position fen %s" % fen
        if moves:
            cmd += " moves " + " ".join(moves)
        self.send(cmd)

    def search(self, go, timeout=600.0, stop_after=None):
        """Run one search. Returns (lines, bestmove_line).

        `stop_after` (seconds) sends `stop` instead of a blocking read, which is
        the only legal mid-search abort. Never send `quit` here.
        """
        self.send(("go %s" % go).strip())
        if stop_after is not None:
            time.sleep(stop_after)
            self.send("stop")
            timeout = max(timeout, 60.0)
        lines = self.read_until(lambda l: l.startswith("bestmove"), timeout=timeout)
        return lines, lines[-1]

    def quit(self):
        try:
            self.send("quit")
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()


def parse_info(line):
    """Split an `info` line into (fields, pv_moves).

    Two fields are not plain key/value pairs: `score cp N` / `score mate N`
    carries a unit and a number, and `pv` is a variadic list. Both are handled
    explicitly, otherwise the generic two-token step desynchronises and every
    following field is read under the wrong key.
    """
    tok = line.split()
    if not tok or tok[0] != "info":
        return None, []
    fields = {}
    i = 1
    while i < len(tok):
        key = tok[i]
        if key == "pv":
            return fields, tok[i + 1:]
        if key == "string":
            fields["string"] = " ".join(tok[i + 1:])
            return fields, []
        if key == "score":
            unit = tok[i + 1] if i + 1 < len(tok) else None
            value = tok[i + 2] if i + 2 < len(tok) else None
            fields["score"] = "%s %s" % (unit, value)
            fields["score_unit"] = unit
            fields["score_value"] = value
            i += 3
            continue
        val = tok[i + 1] if i + 1 < len(tok) else None
        fields[key] = val
        i += 2
    return fields, []


def info_lines(lines):
    return [l for l in lines if l.startswith("info")]
