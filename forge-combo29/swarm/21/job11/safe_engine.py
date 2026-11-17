#!/usr/bin/env python3
"""safe_engine.py — the ONLY way my harnesses talk to the engine now.

Implements the two actions of seat 19's 19-F12 notice:
  1. every command's stdout is read until the expected token before the next command;
  2. stdin is NEVER closed while a search is running: the harness reads `bestmove` first
     and only then sends `quit` (and waits for the process to exit).

A `send` while a `go` is outstanding raises, so a pipelined harness cannot be written by
accident. Every line read is recorded for the raw file.
"""
import os
import queue
import subprocess
import threading


class Timeout(Exception):
    pass


class SafeEngine:
    def __init__(self, exe, raw_path, hash_mb=16, threads=1):
        self.raw = open(raw_path, "w")
        env = dict(os.environ)
        for k in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
            env.pop(k, None)
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
        self.q = queue.Queue()
        self.eof = False
        threading.Thread(target=self._pump, daemon=True).start()
        self.searching = False
        self.send("uci")
        self.wait_for("uciok")
        for name, val in (("Hash", str(hash_mb)), ("Threads", str(threads)),
                          ("OwnBook", "false")):
            self.send("setoption name %s value %s" % (name, val))
            self.send("isready")
            self.wait_for("readyok")
        self.send("ucinewgame")
        self.send("isready")
        self.wait_for("readyok")

    def _pump(self):
        for line in self.p.stdout:
            self.q.put(line.rstrip("\n"))
        self.eof = True
        self.q.put(None)

    def send(self, line):
        if self.searching:
            raise RuntimeError("refusing to send %r while a search is outstanding: "
                               "read bestmove first (19-F12)" % line)
        self.raw.write(">>> " + line + "\n")
        self.raw.flush()
        try:
            self.p.stdin.write(line + "\n")
            self.p.stdin.flush()
        except BrokenPipeError:
            pass

    def read_line(self, timeout):
        try:
            ln = self.q.get(timeout=timeout)
        except queue.Empty:
            raise Timeout("no output within %.1f s" % timeout)
        if ln is None:
            raise EOFError("engine closed stdout")
        self.raw.write(ln + "\n")
        self.raw.flush()
        return ln

    def wait_for(self, token, timeout=60.0):
        lines = []
        while True:
            ln = self.read_line(timeout)
            lines.append(ln)
            if ln.strip() == token or ln.strip().startswith(token + " "):
                return lines

    def go(self, go_line, timeout=120.0, token="bestmove"):
        """Send a go line and read EVERYTHING up to and including `token`.
        `go perft` answers `nodes N`, not `bestmove`, so the terminator is a parameter.
        While it is outstanding no other send is allowed."""
        self.send(go_line)
        self.searching = True
        try:
            lines = self.wait_for(token, timeout)
        finally:
            self.searching = False
        return lines

    def position(self, pos_line):
        self.send(pos_line)
        self.send("isready")
        return self.wait_for("readyok")

    def close(self):
        if self.searching:
            # never close stdin mid-search: stop first, read bestmove
            self.send("stop")
            try:
                self.wait_for("bestmove", 10)
            except Exception:
                pass
            self.searching = False
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()
        self.raw.close()


def bestmove_of(lines):
    for ln in reversed(lines):
        if ln.startswith("bestmove"):
            return ln.split()[1] if len(ln.split()) > 1 else ""
    return ""


def last_info(lines):
    infos = [ln for ln in lines if ln.startswith("info depth")]
    return infos[-1] if infos else ""