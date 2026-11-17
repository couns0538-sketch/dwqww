#!/usr/bin/env python3
"""UCI driver for a ThreadSanitizer build of Forge.

Never pipes `quit` into a live search: every `go` is read to its `bestmove`
line before the next command is written.  Collects every stderr/stdout line
so the TSan report can be extracted afterwards.

Timing is never recorded.  This driver exists to exercise shared state under
TSan, not to measure speed.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

BESTMOVE = re.compile(r"^bestmove\b")


class Engine:
    def __init__(self, exe, env=None):
        e = dict(os.environ)
        e.setdefault("TSAN_OPTIONS", "halt_on_error=0 second_deadlock_stack=1 history_size=4")
        if env:
            e.update(env)
        self.proc = subprocess.Popen(
            [exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, bufsize=1, env=e)
        self.log = []
        self._send("uci")
        self._wait("uciok", 60)

    def _send(self, cmd):
        self.log.append(">>> " + cmd)
        self.proc.stdin.write(cmd + "\n")
        self.proc.stdin.flush()

    def _wait(self, token, limit):
        """Read until a line equals token (used for uciok/readyok)."""
        t0 = time.time()
        while True:
            if time.time() - t0 > limit:
                raise TimeoutError("timeout waiting for %r after %.0fs" % (token, limit))
            line = self.proc.stdout.readline()
            if not line:
                raise EOFError("EOF waiting for %r" % token)
            line = line.rstrip("\n")
            self.log.append(line)
            if line.strip() == token:
                return

    def _wait_bestmove(self, limit):
        """Read until a bestmove line.  Returns (bestmove_token, info_lines)."""
        t0 = time.time()
        info = []
        while True:
            if time.time() - t0 > limit:
                raise TimeoutError("timeout waiting for bestmove after %.0fs" % limit)
            line = self.proc.stdout.readline()
            if not line:
                raise EOFError("EOF waiting for bestmove")
            line = line.rstrip("\n")
            self.log.append(line)
            if line.startswith("info depth"):
                info.append(line)
            if BESTMOVE.match(line):
                return line.split()[1] if len(line.split()) > 1 else None, info

    def sync(self):
        self._send("isready")
        self._wait("readyok", 120)

    def cmd(self, c):
        self._send(c)

    def go(self, limit, timeout):
        self.sync()
        self._send(limit)
        return self._wait_bestmove(timeout)

    def close(self, timeout=60):
        """Send quit, then DRAIN THE PIPE TO EOF before reaping.

        A sanitizer that reports at exit writes after `quit`.  Reading only up
        to `bestmove` and then calling wait() would leave those reports unread
        in the pipe, and the run would be reported clean without ever having
        observed its own exit.  Drain to EOF first, then wait.
        """
        try:
            self._send("quit")
        except Exception:
            pass
        try:
            # Read every remaining line until the child closes stdout.
            for line in self.proc.stdout:
                self.log.append(line.rstrip("\n"))
        except Exception:
            pass
        try:
            self.proc.wait(timeout)
        except Exception:
            self.proc.kill()
            for line in self.proc.stdout:
                self.log.append(line.rstrip("\n"))
            self.proc.wait(timeout)
        self.drained_to_eof = True
        self.exit_code = self.proc.returncode
        return self.log


RACE_RE = re.compile(r"WARNING: ThreadSanitizer: (.*)")
SUMMARY_RE = re.compile(r"SUMMARY: ThreadSanitizer: (.*)")


def races(log):
    """Group TSan output into individual reports."""
    out = []
    cur = None
    for line in log:
        m = RACE_RE.search(line)
        if m:
            cur = {"kind": m.group(1).strip(), "lines": [line]}
            out.append(cur)
            continue
        if cur is not None:
            cur["lines"].append(line)
    for r in out:
        r["summary"] = None
        for line in r["lines"]:
            m = SUMMARY_RE.search(line)
            if m:
                r["summary"] = m.group(1).strip()
    return out
