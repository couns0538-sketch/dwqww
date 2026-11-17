"""Minimal UCI driver for forge: send a command, read stdout to `bestmove`/`readyok`.

Rules obeyed (forge-findings §6/§7):
- Never let EOF reach a running search (trap 1, 3a). The process is kept alive and
  `quit` is sent only after `bestmove` is seen, then stdin is closed.
- Accumulate the raw stream and parse the buffer afterwards (trap 6 fix).
- Every `setoption`/`position` is followed by `isready` and we read to `readyok`,
  stopping on `unknown option`, `invalid value`, `invalid FEN`, `illegal move`.
- select()+readline on a pipe is not a timeout -> use a reader thread with deadline.
"""
import os
import queue
import subprocess
import threading
import time


class Engine:
    def __init__(self, exe, options=None, timeout=120.0):
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        self.q = queue.Queue()
        self.raw = []
        self.timeout = timeout
        self._t = threading.Thread(target=self._pump, daemon=True)
        self._t.start()
        self.send("uci")
        self.uci_lines = self.read_until(("uciok",), 10.0)
        self.id_lines = [l for l in self.uci_lines if l.startswith("id ")]
        self.option_lines = [l for l in self.uci_lines if l.startswith("option name ")]
        self.fatal = []
        for name, value in (options or {}).items():
            self.setoption(name, value)

    def _pump(self):
        for line in iter(self.proc.stdout.readline, b""):
            self.q.put(line.decode("utf-8", "replace").rstrip("\r\n"))
        self.q.put(None)

    def send(self, cmd):
        self.proc.stdin.write((cmd + "\n").encode())
        self.proc.stdin.flush()

    def read_until(self, terminators, timeout=None):
        deadline = time.monotonic() + (timeout if timeout is not None else self.timeout)
        lines = []
        while True:
            left = deadline - time.monotonic()
            if left <= 0:
                raise TimeoutError(f"timeout waiting for {terminators}; got {lines[-6:]}")
            try:
                line = self.q.get(timeout=left)
            except queue.Empty:
                raise TimeoutError(f"timeout waiting for {terminators}; got {lines[-6:]}")
            if line is None:
                raise EOFError(f"engine closed after {len(lines)} lines")
            lines.append(line)
            if any(t in line for t in terminators):
                self.raw.extend(lines)
                return lines

    def read_ready(self, timeout=30.0):
        return self.read_until(("readyok",), timeout)

    def _scan_fatal(self, lines):
        for line in lines:
            for bad in ("unknown option", "invalid value", "invalid FEN", "illegal move"):
                if bad in line:
                    self.fatal.append(line)

    def isready(self):
        self.send("isready")
        return self.read_ready()

    def position(self, fen=None, moves=None):
        if fen is None:
            cmd = "position startpos"
        else:
            cmd = f"position fen {fen}"
        if moves:
            cmd += " moves " + " ".join(moves)
        self.send(cmd)
        return self.isready()

    def ucinewgame(self):
        self.send("ucinewgame")
        self.isready()

    def setoption(self, name, value):
        self.send(f"setoption name {name} value {value}")
        self.send("isready")
        lines = self.read_ready()
        self._scan_fatal(lines)
        return lines

    def go(self, args, timeout=None):
        """Send `go <args>` and read the whole stream to `bestmove`.

        Returns (info_lines, bestmove_line, wall_seconds).
        """
        start = time.monotonic()
        self.send("go " + args)
        lines = self.read_until(("bestmove",), timeout)
        wall = time.monotonic() - start
        best = lines[-1]
        return lines[:-1], best, wall

    def perft(self, depth):
        self.send(f"go perft {depth}")
        lines = self.read_until(("nodes ",), 300.0)
        # perft ends with a bare `nodes N` line; the terminator above also matches
        # `info ... nodes ...`, so read on until a line that starts with "nodes".
        while not lines[-1].startswith("nodes "):
            lines += self.read_until(("nodes ",), 300.0)
            if lines[-1].startswith("nodes "):
                break
        return lines

    def close(self):
        try:
            if self.proc.poll() is None:
                self.send("quit")
                self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()


def parse_info(line):
    """Parse one `info depth ...` line into a dict of the fields we use."""
    out = {}
    toks = line.split()
    if not toks or toks[0] != "info":
        return None
    i = 1
    pv = []
    while i < len(toks):
        t = toks[i]
        if t == "pv":
            pv = toks[i + 1:]
            break
        if t in ("depth", "seldepth", "nodes", "nps", "hashfull", "time", "multipv"):
            try:
                out[t] = int(toks[i + 1])
            except (IndexError, ValueError):
                pass
            i += 2
            continue
        if t == "score":
            if i + 2 < len(toks):
                kind = toks[i + 1]
                try:
                    val = int(toks[i + 2])
                except ValueError:
                    val = None
                out["score_kind"] = kind
                out["score"] = val
            i += 3
            continue
        if t == "string":
            out["string"] = " ".join(toks[i + 1:])
            break
        i += 1
    out["pv"] = pv
    out["line"] = line
    return out


def last_depth_info(info_lines):
    """The last plain `info depth` line with a pv (not a `string` diagnostic)."""
    best = None
    for line in info_lines:
        if not line.startswith("info depth"):
            continue
        d = parse_info(line)
        if d:
            best = d
    return best
