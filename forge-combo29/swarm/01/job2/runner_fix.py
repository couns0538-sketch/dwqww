#!/usr/bin/env python3
"""swarm seat 01, job 2 CORRECTION: runner_extreme.py mislabelled one case.

`white_pawn_rank8` in runner_extreme.py used the FEN "4k3/4P3/8/8/8/8/8/4K3", whose FIRST rank field
is "4k3" (the black king on e8) and whose pawn sits on e7, i.e. rank 7 — NOT rank 8. So the case
tested "a white pawn on the 7th rank", which is legal, and its acceptance is correct. The script is
not edited (the run that produced results.json is what it is); the corrected case is run here and the
label error is written into REPORT_job2.md under "what I did NOT do / corrections".

This script also carries the pawn-on-rank-8 and pawn-on-rank-1 cases with the king placed OFF the pawn's
file so the only illegality is the pawn itself.

Usage: runner_fix.py <exe> <outdir>
"""
import hashlib
import json
import os
import select
import subprocess
import sys
import time
from pathlib import Path

import chess

TIMEOUT = 60.0


class R:
    def __init__(self, fd):
        self.fd, self.buf, self.eof = fd, b"", False

    def line(self, deadline):
        while b"\n" not in self.buf:
            if self.eof:
                return None
            remain = deadline - time.monotonic()
            if remain <= 0:
                return None
            r, _, _ = select.select([self.fd], [], [], remain)
            if not r:
                return None
            c = os.read(self.fd, 65536)
            if not c:
                self.eof = True
                return None
            self.buf += c
        l, _, self.buf = self.buf.partition(b"\n")
        return l.decode("utf-8", "replace")


def one(exe, fen):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, bufsize=0, cwd="/tmp")
    rd = R(p.stdout.fileno())
    buf = []

    def until(prefix):
        d = time.monotonic() + TIMEOUT
        while True:
            l = rd.line(d)
            if l is None:
                return None
            buf.append(l)
            if l.startswith(prefix):
                return l

    def send(s):
        p.stdin.write((s + "\n").encode())
        p.stdin.flush()

    send("position fen " + fen)
    send("isready")
    until("readyok")
    refusal = [l for l in buf if l.startswith("info string invalid FEN")]
    bmline = None
    perft2 = None
    if not refusal:
        send("go perft 2")
        if until("nodes ") is not None:
            for l in buf:
                if l.startswith("nodes "):
                    perft2 = int(l.split()[1])
    time.sleep(0.2)
    send("quit")
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()
    san = [l for l in buf if ("AddressSanitizer" in l or "runtime error" in l or "SUMMARY:" in l)]
    return {"fen": fen, "refused": bool(refusal), "refusal": refusal,
            "perft2_engine": perft2, "sanitizer": san}


def py_perft2(fen):
    try:
        b = chess.Board(fen)
    except Exception:  # noqa: BLE001
        return None
    if not b.is_valid():
        return None

    def pf(bd, d):
        if d == 0:
            return 1
        n = 0
        for m in bd.legal_moves:
            bd.push(m)
            n += pf(bd, d - 1)
            bd.pop()
        return n
    return pf(b, 2)


def main():
    exe = sys.argv[1]
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    cases = [
        ("pawn_white_on_rank8", "4P3/8/8/8/8/8/8/K6k w - - 0 1"),
        ("pawn_black_on_rank1", "K6k/8/8/8/8/8/8/4p3 b - - 0 1"),
        ("pawn_white_on_rank1", "K6k/8/8/8/8/8/8/4P3 w - - 0 1"),
        ("pawn_black_on_rank8", "4p3/8/8/8/8/8/8/K6k b - - 0 1"),
        ("mislabel_checked", "4k3/4P3/8/8/8/8/8/4K3 w - - 0 1"),
    ]
    lines = ["job 2 correction run: pawns on the promotion ranks, kings off the pawn's file",
             "exe_started: %s" % exe,
             "sha256: %s" % hashlib.sha256(Path(exe).read_bytes()).hexdigest()]
    nm = subprocess.run(["nm", "-C", exe], capture_output=True, text=True).stdout
    lines.append("nm -C grep -c __asan_ : %d" % sum(1 for l in nm.splitlines() if "__asan_" in l))
    lines.append("nm -C grep -c __ubsan_ : %d" % sum(1 for l in nm.splitlines() if "__ubsan_" in l))
    lines.append("option lines sent: NONE")
    lines.append("")
    lines.append("case\tfen\trefused\trefusal\tperft2_engine\tpy_perft2\tmatch")
    res = []
    for name, fen in cases:
        r = one(exe, fen)
        r["case"] = name
        r["py_perft2"] = py_perft2(fen)
        r["match"] = (r["perft2_engine"] is not None and r["py_perft2"] is not None
                      and r["perft2_engine"] == r["py_perft2"])
        res.append(r)
        lines.append("%s\t%s\t%s\t%s\t%s\t%s\t%s" % (
            name, fen, r["refused"], "; ".join(r["refusal"]), r["perft2_engine"],
            r["py_perft2"], r["match"]))
    (out / "results_fix.json").write_text(json.dumps(res, indent=1))
    text = "\n".join(lines) + "\n"
    (out / "table_fix.txt").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
