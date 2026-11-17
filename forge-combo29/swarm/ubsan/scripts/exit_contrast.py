#!/usr/bin/env python3
"""Contrast test, the point of which is requirement 3 of the seat brief:

A harness that stops reading at `bestmove` and then kills the child reports a
CLEAN zero on a build that does have an exit-time UB report. A harness that
drains to EOF sees it. Run both against the same binary.

Usage: exit_contrast.py <exe-with-exit-plant>
"""
import json
import os
import select
import subprocess
import sys
import time

ENV = dict(os.environ)
ENV["UBSAN_OPTIONS"] = "print_stacktrace=1:halt_on_error=0:report_error_type=1"
ENV["ASAN_OPTIONS"] = "detect_leaks=1:abort_on_error=1"


def read_until(p, token, timeout):
    buf = b""
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        r, _, _ = select.select([p.stdout], [], [], 0.2)
        if not r:
            continue
        ch = os.read(p.stdout.fileno(), 1 << 16)
        if not ch:
            return buf, False
        buf += ch
        if token in buf:
            return buf, True
    return buf, False


def naive(exe):
    """Stop at bestmove, kill the child. This is the seat's described defect."""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, env=ENV)
    p.stdin.write(b"uci\nisready\nposition fen 6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1\neval\ngo depth 8\n")
    p.stdin.flush()
    out, _ = read_until(p, b"bestmove", 120)
    p.kill()                      # never drained
    p.wait()
    text = out.decode("utf-8", "backslashreplace")
    return {"harness": "bestmove-then-kill", "drained_to_eof": False,
            "san_lines": [l for l in text.splitlines() if "runtime error:" in l
                          or "Sanitizer" in l],
            "verdict": "CLEAN" if not any("runtime error:" in l or "Sanitizer" in l
                                          for l in text.splitlines()) else "REPORT"}


def drained(exe):
    """Send quit, drain to EOF, wait for the exit status."""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, env=ENV)
    p.stdin.write(b"uci\nisready\nposition fen 6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1\neval\ngo depth 8\n")
    p.stdin.flush()
    read_until(p, b"bestmove", 120)
    p.stdin.write(b"quit\n")
    p.stdin.flush()
    p.stdin.close()
    buf = b""
    while True:
        r, _, _ = select.select([p.stdout], [], [], 30)
        if not r:
            break
        ch = os.read(p.stdout.fileno(), 1 << 16)
        if not ch:
            break
        buf += ch
    rc = p.wait()
    text = buf.decode("utf-8", "backslashreplace")
    lines = [l for l in text.splitlines() if "runtime error:" in l or "Sanitizer" in l]
    return {"harness": "drain-to-eof", "drained_to_eof": True, "exit_code": rc,
            "san_lines": lines, "verdict": "REPORT" if lines else "CLEAN"}


def main():
    exe = sys.argv[1]
    out = {"exe": exe, "UBSAN_OPTIONS": ENV["UBSAN_OPTIONS"],
           "arms": [naive(exe), drained(exe)]}
    out["conclusion"] = (
        "the bestmove-only harness misses an exit-time UB report that the "
        "drain-to-EOF harness catches"
        if out["arms"][0]["verdict"] == "CLEAN" and out["arms"][1]["verdict"] == "REPORT"
        else "contrast did not reproduce")
    print(json.dumps(out, indent=1))
    json.dump(out, open(sys.argv[2], "w"), indent=1)


if __name__ == "__main__":
    main()
