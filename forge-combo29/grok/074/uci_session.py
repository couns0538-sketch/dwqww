#!/usr/bin/env python3
"""UCI session helper. Stops on unknown option, invalid value, invalid FEN, illegal move."""

import hashlib
import subprocess
import threading

STOP_MARKS = (
    "unknown option",
    "invalid value",
    "invalid fen",
    "illegal move",
)


class UciError(RuntimeError):
    pass


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Session:
    def __init__(self, exe):
        self.exe = exe
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.lines = []
        self.failed = None
        self._queue_error = None
        self._closed = False

    def send(self, line):
        if self.failed:
            raise UciError(self.failed)
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, predicate, timeout):
        """Read lines until predicate(line) is true. Returns the matching line."""
        box = {}

        def reader():
            try:
                while True:
                    line = self.proc.stdout.readline()
                    if line == "":
                        box["eof"] = True
                        return
                    text = line.rstrip("\r\n")
                    self.lines.append(text)
                    low = text.lower()
                    for mark in STOP_MARKS:
                        if mark in low:
                            self.failed = text
                            box["stop"] = text
                            return
                    if predicate(text):
                        box["hit"] = text
                        return
            except Exception as exc:  # noqa: BLE001 — surface the reader failure
                box["err"] = exc

        thread = threading.Thread(target=reader, daemon=True)
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            self.close()
            raise UciError("timeout waiting for engine")
        if "err" in box:
            raise UciError(str(box["err"]))
        if "stop" in box:
            raise UciError(box["stop"])
        if "eof" in box:
            raise UciError("engine closed stdout")
        if "hit" not in box:
            raise UciError("read ended without a match")
        return box["hit"]

    def close(self):
        if self._closed:
            return
        self._closed = True
        try:
            self.proc.stdin.write("quit\n")
            self.proc.stdin.flush()
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=5)


def write_meta(path, exe, digest, id_name, options):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(f"exe {exe}\n")
        handle.write(f"sha256 {digest}\n")
        handle.write(f"id_name {id_name}\n")
        if not options:
            handle.write("options none\n")
        else:
            for line in options:
                handle.write(f"option {line}\n")
