#!/usr/bin/env python3
"""One UCI process. Reads every line. Stops on a bad engine line."""
import hashlib
import queue
import subprocess
import threading
import time
from pathlib import Path

BAD = ("unknown option", "invalid value", "invalid fen", "illegal move")


class UciError(RuntimeError):
    pass


class Session:
    def __init__(self, exe):
        self.exe = str(Path(exe).resolve())
        self.sha256 = hashlib.sha256(Path(self.exe).read_bytes()).hexdigest()
        self.proc = subprocess.Popen(
            [self.exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.options = []
        self.id_name = ""
        self.log = []
        self.lines = queue.Queue()
        self.reader = threading.Thread(target=self._read_stdout, daemon=True)
        self.reader.start()

    def _read_stdout(self):
        for line in self.proc.stdout:
            self.lines.put(line)
        self.lines.put(None)

    def send(self, line):
        self.log.append(">> " + line + "\n")
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, predicate, timeout):
        end = time.time() + timeout
        got = []
        while time.time() < end:
            try:
                line = self.lines.get(timeout=0.5)
            except queue.Empty:
                if self.proc.poll() is not None:
                    break
                continue
            if line is None:
                break
            self.log.append(line)
            got.append(line)
            low = line.lower()
            for bad in BAD:
                if bad in low:
                    raise UciError(line.rstrip("\n"))
            if line.startswith("id name "):
                self.id_name = line[len("id name "):].rstrip("\n")
            if predicate(line):
                return got
        raise UciError("timeout waiting for engine")

    def ready(self, timeout=30):
        self.send("isready")
        self.read_until(lambda line: line.startswith("readyok"), timeout)

    def setoption(self, name, value):
        text = f"setoption name {name} value {value}"
        self.options.append(text)
        self.send(text)
        self.ready()

    def uci(self):
        self.send("uci")
        return self.read_until(lambda line: line.startswith("uciok"), 30)

    def close(self):
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()

    def meta(self, command):
        opts = "\n".join(self.options) if self.options else ""
        return (
            f"exe={self.exe}\n"
            f"sha256={self.sha256}\n"
            f"id_name={self.id_name}\n"
            f"options=\n{opts}\n"
            f"command={command}\n"
        )
