#!/usr/bin/env python3
"""Line-oriented UCI session. Reads the raw pipe so a buffered line is never missed."""
import os
import select
import subprocess

STOP_MARKERS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe):
        self.exe = exe
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        self._out = b""
        self.lines = []
        self.stderr = b""

    def _pull(self, timeout):
        assert self.proc.stdout is not None
        fd = self.proc.stdout.fileno()
        ready, _, _ = select.select([fd], [], [], timeout)
        if not ready:
            return False
        chunk = os.read(fd, 1 << 16)
        if chunk == b"":
            return False
        self._out += chunk
        return True

    def read_until(self, marker, timeout):
        assert self.proc.stdin is not None
        while True:
            while b"\n" in self._out:
                raw, self._out = self._out.split(b"\n", 1)
                text = raw.decode("utf-8", "replace").rstrip("\r")
                self.lines.append(text)
                if any(stop in text for stop in STOP_MARKERS):
                    self.close()
                    raise SystemExit("STOP " + text)
                if marker in text:
                    return text
            if self.proc.poll() is not None and b"\n" not in self._out:
                err = self.proc.stderr.read() if self.proc.stderr is not None else b""
                self.stderr += err
                raise SystemExit(
                    "EOF waiting for " + marker + "\n" + "\n".join(self.lines[-30:])
                )
            if not self._pull(timeout):
                raise SystemExit(
                    "TIMEOUT waiting for " + marker + "\n" + "\n".join(self.lines[-30:])
                )

    def send(self, command, marker, timeout):
        assert self.proc.stdin is not None
        self.proc.stdin.write((command + "\n").encode())
        self.proc.stdin.flush()
        if marker is None:
            return ""
        return self.read_until(marker, timeout)

    def close(self):
        if self.proc.poll() is None:
            try:
                assert self.proc.stdin is not None
                self.proc.stdin.write(b"quit\n")
                self.proc.stdin.flush()
                self.proc.wait(timeout=10)
            except Exception:
                self.proc.kill()
        if self.proc.stderr is not None:
            self.stderr += self.proc.stderr.read() or b""


def id_name(lines):
    for line in lines:
        if line.startswith("id name "):
            return line
    return "id name MISSING"
