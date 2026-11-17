#!/usr/bin/env python3
"""Bounded UCI driver. Waits for the terminal token of every command before
writing the next; never pipes a follow-up into a live search."""
import os
import select
import subprocess
import sys
import time


class Engine:
    def __init__(self, exe, env_extra=None, cwd=None):
        env = dict(os.environ)
        if env_extra:
            env.update(env_extra)
        self.p = subprocess.Popen(
            [exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, env=env, cwd=cwd, bufsize=0)
        self.buf = b""
        self.log = []
        self.broken = False

    def send(self, cmd):
        try:
            self.p.stdin.write((cmd + "\n").encode())
            self.p.stdin.flush()
        except (BrokenPipeError, ValueError, OSError):
            self.broken = True

    def read_until(self, tokens, deadline_s):
        """Read until any token appears as a line prefix; return (lines, token)."""
        end = time.monotonic() + deadline_s
        while True:
            tok = None
            for cand in tokens:
                if self.line_ready(cand):
                    tok = cand
                    break
            if tok:
                break
            remain = end - time.monotonic()
            if remain <= 0:
                return self.flush_lines(), None
            try:
                r, _, _ = select.select([self.p.stdout], [], [], min(remain, 0.25))
            except (OSError, ValueError):
                return self.flush_lines(), "EOF"
            if r:
                try:
                    chunk = os.read(self.p.stdout.fileno(), 1 << 20)
                except (OSError, ValueError):
                    return self.flush_lines(), "EOF"
                if not chunk:
                    return self.flush_lines(), "EOF"
                self.buf += chunk
        return self.flush_lines(), tok

    def line_ready(self, tok):
        """True only for a COMPLETE line starting with tok.

        The buffer's final element is the not-yet-terminated tail. Matching it
        would declare the token present while the line is still arriving, and
        the line would then stay in the buffer (and out of the evidence) after
        flush_lines puts it back. That made `nodes 4865609` and every
        `info string eval` line disappear from an otherwise complete run.
        """
        b = tok.encode()
        parts = self.buf.split(b"\n")
        complete = parts[:-1] if not self.buf.endswith(b"\n") else parts[:-1]
        for ln in complete:
            if ln.startswith(b):
                return True
        return False

    def flush_lines(self):
        parts = self.buf.split(b"\n")
        self.buf = parts.pop()
        out = []
        for ln in parts:
            out.append(ln.decode("utf-8", "backslashreplace"))
            self.log.append(out[-1])
        return out

    def cmd(self, cmd, tokens=("bestmove",), timeout_s=30.0):
        self.send(cmd)
        return self.read_until(tokens, timeout_s)

    def drain(self, timeout_s=0.3):
        return self.read_until(("\x00never\x00",), timeout_s)[0]

    def quit(self):
        try:
            self.send("quit")
            self.p.stdin.close()
        except Exception:
            pass
        try:
            self.p.wait(timeout=5)
        except Exception:
            self.p.kill()
        tail = self.read_until(("\x00never\x00",), 0.2)[0]
        rc = self.p.returncode
        return tail, rc


def main():
    e = Engine(sys.argv[1])
    print(e.cmd("uci", ("uciok",), 10)[1])
    e.quit()


if __name__ == "__main__":
    main()
