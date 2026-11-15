#!/usr/bin/env python3
"""A held-open UCI driver for job 10: writes commands one at a time and reads the reply.
Used for the interrupted-search tests, where the timing of `stop` matters to the
millisecond, so nothing may be piped in advance.
"""
import queue
import subprocess
import threading
import time

ENGINE = "/tmp/ds/build-release/forge"


class Engine:
    def __init__(self, threads=1, hash_mb=16, multipv=1, own_book=False, engine=ENGINE):
        self.proc = subprocess.Popen([engine], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True, bufsize=1)
        self.q = queue.Queue()
        self.lines = []
        threading.Thread(target=self._read, daemon=True).start()
        threading.Thread(target=lambda: [self._drain_err()], daemon=True).start()
        self.send(f"setoption name Threads value {threads}")
        self.send(f"setoption name Hash value {hash_mb}")
        self.send("setoption name NNUEArch value false")
        self.send(f"setoption name OwnBook value {'true' if own_book else 'false'}")
        self.send(f"setoption name MultiPV value {multipv}")
        self.send("isready")
        self.until("readyok", 120)

    def _drain_err(self):
        for _ in self.proc.stderr:
            pass

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
            self.lines.append(line)
            if line.startswith(needle):
                return line

    def get(self, timeout):
        try:
            line = self.q.get(timeout=timeout)
        except queue.Empty:
            return None
        if line is None:
            return None
        self.lines.append(line)
        return line

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
