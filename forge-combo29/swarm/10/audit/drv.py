"""drv.py -- seat 10's robust interactive engine driver (thread-based reader).

Never closes stdin before `bestmove` is read, so it cannot trigger the EOF-abort trap
(seat 19's 19-F12, which I reproduced independently: 0 info lines and a fabricated
`bestmove a2a3` when stdin closes mid-search, 12 info lines / 56720 nodes when it does not).

Usage:
    from drv import Drv
    d = Drv(exe)
    d.cmd("uci", until="uciok")
    d.cmd("isready", until="readyok")
    d.opt("OwnBook", "false")
    d.pos("position startpos")          # sends position then isready, waits for readyok
    nodes, best, lines = d.go("go depth 12")
    d.close()
"""
import os
import queue
import subprocess
import threading
import time


class Drv:
    def __init__(self, exe, timeout=1800):
        env = {k: v for k, v in os.environ.items()
               if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS")}
        self.timeout = timeout
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1, env=env)
        self.q = queue.Queue()
        self.eof = False

        def reader():
            for line in self.p.stdout:
                self.q.put(line.rstrip("\n"))
            self.q.put(None)

        threading.Thread(target=reader, daemon=True).start()
        self.log = []

    def _get(self, deadline):
        item = self.q.get(timeout=max(0.01, deadline - time.monotonic()))
        if item is None:
            self.eof = True
            raise RuntimeError("engine EOF while waiting")
        self.log.append(item)
        return item

    def cmd(self, line, until, timeout=None):
        self.write(line)
        return self._read_until(until, timeout)

    def write(self, line):
        self.p.stdin.write(line + "\n")
        self.p.stdin.flush()

    def _read_until(self, pred, timeout=None, collect=True):
        tmo = timeout or self.timeout
        deadline = time.monotonic() + tmo
        got = []
        while True:
            item = self._get(deadline)
            got.append(item)
            if pred(item):
                return got

    def uci(self):
        self.write("uci")
        lines = self._read_until(lambda l: l == "uciok", timeout=60)
        return lines

    def isready(self):
        self.write("isready")
        return self._read_until(lambda l: l == "readyok", timeout=120)

    def opt(self, name, value=None):
        if value is None:
            self.write("setoption name %s" % name)
        else:
            self.write("setoption name %s value %s" % (name, value))

    def pos(self, cmd):
        self.write(cmd)
        return self.isready()

    def go(self, cmd, timeout=None):
        """returns (last_info_nodes, bestmove, all lines of this search)"""
        self.write(cmd)
        lines = self._read_until(lambda l: l.startswith("bestmove"), timeout=timeout)
        nodes = None
        for l in lines:
            if l.startswith("info") and " nodes " in l:
                try:
                    nodes = int(l.split(" nodes ")[1].split()[0])
                except (IndexError, ValueError):
                    pass
        best = lines[-1].split()[1] if lines else None
        return nodes, best, lines

    def perft(self, depth, timeout=None):
        """the total is on the line 'nodes N' printed BEFORE the trailing readyok"""
        self.write("go perft %d" % depth)
        lines = self._read_until(lambda l: l.startswith("nodes "), timeout=timeout)
        total = None
        for l in lines:
            if l.startswith("nodes "):
                total = int(l.split()[1])
        self.isready()
        return total, lines

    def quit(self):
        try:
            self.write("quit")
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()
