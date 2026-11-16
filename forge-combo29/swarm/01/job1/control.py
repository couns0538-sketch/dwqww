#!/usr/bin/env python3
"""swarm seat 01, job 1 control: a 3,000-character first field must be refused, no crash, no sanitizer line.

Also re-checks stability (P7): the same three FENs are replayed in a second process to see the
same accept/refuse answer.

Usage: control.py <exe> <outdir>
"""
import hashlib
import json
import os
import select
import subprocess
import sys
import time
from pathlib import Path

TIMEOUT = 30.0


class Reader:
    def __init__(self, fd):
        self.fd = fd
        self.buf = b""
        self.eof = False

    def readline(self, deadline):
        while b"\n" not in self.buf:
            if self.eof:
                return None
            remain = deadline - time.monotonic()
            if remain <= 0:
                return None
            r, _, _ = select.select([self.fd], [], [], remain)
            if not r:
                return None
            chunk = os.read(self.fd, 65536)
            if not chunk:
                self.eof = True
                return None
            self.buf += chunk
        line, _, self.buf = self.buf.partition(b"\n")
        return line.decode("utf-8", "replace")


def one_run(exe, fens):
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, bufsize=0, cwd="/tmp")
    rd = Reader(proc.stdout.fileno())
    out = []
    for fen in fens:
        proc.stdin.write(("position fen " + fen + "\n").encode())
        proc.stdin.write(b"isready\n")
        proc.stdin.flush()
        lines = []
        ok = False
        deadline = time.monotonic() + TIMEOUT
        while True:
            line = rd.readline(deadline)
            if line is None:
                break
            lines.append(line)
            if line.startswith("readyok"):
                ok = True
                break
        if not ok:
            out.append({"fen_len": len(fen), "hung_or_died": True, "lines": lines})
            try:
                proc.kill()
            except Exception:
                pass
            return out
        proc.stdin.write(b"go depth 2\n")
        proc.stdin.flush()
        got_bm = False
        deadline = time.monotonic() + TIMEOUT
        while True:
            line = rd.readline(deadline)
            if line is None:
                break
            lines.append(line)
            if line.startswith("bestmove"):
                got_bm = True
                break
        out.append({
            "fen_len": len(fen),
            "refused": any(l.startswith("info string invalid FEN") for l in lines),
            "refusal": [l for l in lines if l.startswith("info string invalid FEN")],
            "got_bestmove": got_bm,
            "sanitizer": [l for l in lines if ("AddressSanitizer" in l or "runtime error" in l
                                               or "SUMMARY:" in l)],
            "lines": lines,
        })
    proc.stdin.write(b"quit\n")
    proc.stdin.flush()
    try:
        proc.wait(timeout=30)
    except Exception:
        proc.kill()
    return out


def main():
    exe = sys.argv[1]
    outdir = Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    longfield = "8" * 3000
    fens = [
        longfield + " w - - 0 1",
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w KQkq - 0 1",
    ]
    first = one_run(exe, fens)
    second = one_run(exe, fens)
    stable = all(a["refused"] == b["refused"] for a, b in zip(first, second))
    lines = []
    lines.append("control: 3,000-character first field must be refused without a crash")
    lines.append("exe_started: %s" % exe)
    lines.append("sha256: %s" % hashlib.sha256(Path(exe).read_bytes()).hexdigest())
    lines.append("nm -C grep -c __asan_ : %d" % len([l for l in subprocess.run(
        ["nm", "-C", exe], capture_output=True, text=True).stdout.splitlines() if "__asan_" in l]))
    lines.append("nm -C grep -c __ubsan_ : %d" % len([l for l in subprocess.run(
        ["nm", "-C", exe], capture_output=True, text=True).stdout.splitlines() if "__ubsan_" in l]))
    lines.append("")
    for tag, run in (("run1", first), ("run2", second)):
        for k, rec in enumerate(run):
            lines.append("%s fen[%d] len=%d refused=%s bestmove=%s sanitizer=%d"
                         % (tag, k, rec["fen_len"], rec.get("refused"), rec.get("got_bestmove"),
                            len(rec.get("sanitizer", []))))
            for l in rec.get("refusal", []):
                lines.append("    %s" % l)
            for l in rec.get("sanitizer", [])[:5]:
                lines.append("    SAN %s" % l)
    lines.append("")
    lines.append("STABLE accept/refuse across two processes: %s" % stable)
    v = first[0]
    lines.append("CONTROL VERDICT: %s" % ("PASS (refused, no crash, no sanitizer line)"
                                          if (v.get("refused") and v.get("got_bestmove")
                                              and not v.get("sanitizer")) else "FAIL"))
    text = "\n".join(lines) + "\n"
    (outdir / "control.txt").write_text(text)
    (outdir / "control_raw.json").write_text(json.dumps({"run1": first, "run2": second}, indent=1))
    print(text)


if __name__ == "__main__":
    main()
