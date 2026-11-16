"""forge_io.py -- seat 10's engine I/O helper that does NOT trip the EOF-aborts-search trap.

Facts established by measurement (audit/raw/E1_*):
  * When the engine's stdin reaches EOF while a search is running, the search is ABORTED and
    `bestmove` is printed at once (startpos `go depth 12` returns in 0.02 s with bestmove a2a3
    and no `info` line).
  * Keeping stdin open lets the same command complete normally (info depth 12 ... nodes 56720).
So every search here is driven by an INTERACTIVE pipe: the helper writes a line, then reads until the
expected reply, and only then writes the next line. stdin is never closed before `bestmove` is read.
"""
import os
import re
import select

import subprocess
import time


class Engine:
    def __init__(self, exe, env=None):
        e = dict(os.environ if env is None else env)
        for k in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
            e.pop(k, None)
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True, bufsize=1, env=e)
        self.lines = []

    def send(self, line):
        self.p.stdin.write(line + "\n")
        self.p.stdin.flush()

    def read_until(self, pred, timeout=1800):
        """read lines until pred(line) is true; returns all lines read"""
        got = []
        t0 = time.monotonic()
        while True:
            r, _, _ = select.select([self.p.stdout], [], [], 0.2)
            if r:
                line = self.p.stdout.readline()
                if line == "":
                    raise RuntimeError("engine closed stdout (EOF) after %r" % got[-3:])
                got.append(line.rstrip("\n"))
                if pred(line.strip()):
                    self.lines.extend(got)
                    return got
            if time.monotonic() - t0 > timeout:
                raise TimeoutError("timeout waiting; last lines %r" % got[-5:])

    def isready(self):
        self.send("isready")
        return self.read_until(lambda l: l == "readyok", timeout=60)

    def uci(self):
        self.send("uci")
        return self.read_until(lambda l: l == "uciok", timeout=60)

    def setoption(self, name, value=None):
        if value is None:
            self.send("setoption name %s" % name)
        else:
            self.send("setoption name %s value %s" % (name, value))

    def position(self, cmd):
        self.send(cmd)
        self.isready()

    def go(self, cmd, timeout=1800):
        """send a go command and read until bestmove; returns (last info nodes, bestmove, lines)"""
        self.send(cmd)
        got = self.read_until(lambda l: l.startswith("bestmove"), timeout=timeout)
        nodes = None
        for l in got:
            m = re.search(r" nodes (\d+)", l)
            if m and l.startswith("info"):
                nodes = int(m.group(1))
        best = got[-1].split()[1] if got else None
        return nodes, best, got

    def perft(self, depth, timeout=1800):
        """perft prints one line per root move then 'nodes N'"""
        self.send("go perft %d" % depth)
        self.isready()
        # the divides and the total precede the readyok; gather from self.lines is awkward, so
        # read until the 'nodes N' line first, then the readyok
        return None

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()


def simple(exe, lines, keep_open_for=0.0, timeout=1800):
    """Fallback for NON-search commands: write everything, read everything, close.
    Safe for uci/isready/setoption/position/perft (perft completes on its own before EOF)."""
    p = subprocess.run([exe], input="\n".join(lines) + "\n",
                       capture_output=True, text=True, timeout=timeout)
    return p.stdout, p.stderr, p.returncode
