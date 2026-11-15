#!/usr/bin/env python3
"""A held-open engine driver for job 8: writes one command at a time and blocks on the
reply. Piping a whole script with `quit` at the end closes stdin and cuts the search off,
which makes every tiny-clock measurement meaningless (measured: `go depth 2` returns
`bestmove` with no `info depth` line when the script is piped).
"""
import queue
import subprocess
import threading
import time

ENGINE = "/tmp/ds/build-release/forge"


class Engine:
    def __init__(self, threads=1, hash_mb=16, net=None, engine=ENGINE):
        self.proc = subprocess.Popen([engine], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True, bufsize=1)
        self.q = queue.Queue()
        self.stderr_lines = []
        threading.Thread(target=self._read, daemon=True).start()
        threading.Thread(target=lambda: [self.stderr_lines.append(l.rstrip("\n"))
                                         for l in self.proc.stderr], daemon=True).start()
        self.send(f"setoption name Threads value {threads}")
        self.send(f"setoption name Hash value {hash_mb}")
        if net:
            self.send(f"setoption name NNUEArchFile value {net}")
            self.send("setoption name NNUEArch value true")
        else:
            self.send("setoption name NNUEArch value false")
        self.send("isready")
        self.until("readyok", 120)

    def _read(self):
        for line in self.proc.stdout:
            self.q.put(line.rstrip("\n"))
        self.q.put(None)

    def send(self, c):
        self.proc.stdin.write(c + "\n")
        self.proc.stdin.flush()

    def until(self, needle, timeout):
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            try:
                line = self.q.get(timeout=remaining)
            except queue.Empty:
                return None
            if line is None:
                return None
            if line.startswith(needle):
                return line

    def go(self, position, limit, timeout=10.0):
        """Send a go and wait for bestmove. Returns (bestmove, info_lines, elapsed_ms,
        timed_out). The elapsed time is measured from the moment `go` is written."""
        self.send(position)
        t0 = time.monotonic()
        self.send(f"go {limit}")
        infos = []
        deadline = t0 + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None, infos, (time.monotonic() - t0) * 1000.0, True
            try:
                line = self.q.get(timeout=remaining)
            except queue.Empty:
                return None, infos, (time.monotonic() - t0) * 1000.0, True
            if line is None:
                return None, infos, (time.monotonic() - t0) * 1000.0, True
            if line.startswith("info"):
                infos.append(line)
            elif line.startswith("bestmove"):
                elapsed = (time.monotonic() - t0) * 1000.0
                parts = line.split()
                return (parts[1] if len(parts) > 1 else None), infos, elapsed, False

    def close(self):
        try:
            self.send("quit")
        except (BrokenPipeError, ValueError):
            pass
        try:
            self.proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()
