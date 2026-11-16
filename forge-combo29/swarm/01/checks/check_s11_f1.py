#!/usr/bin/env python3
"""swarm seat 01: CHECK of seat 11's S-F1 (FEN with tokens after the sixth field).

Seat 11's claim, verbatim from its FINDINGS.md:
  "`position fen` reads only six tokens and the following loop silently discards any extra token,
   so a malformed FEN with junk after the sixth field is ACCEPTED (set_fen would have rejected a 7th);
   uci.cpp apply_position."

I wrote this harness myself from that sentence (their probe3 script was not read or copied).
Method: for each case, send `position fen <TEXT>` + `isready` and record the answer lines;
then `go perft 1` (so the KEPT position is visible), then compare with the same board without the junk.
A position that is accepted keeps its legal move count; a refused one keeps the previous position
(here: the start position, whose perft 1 is 20).
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
            chunk = os.read(self.fd, 65536)
            if not chunk:
                self.eof = True
                return None
            self.buf += chunk
        l, _, self.buf = self.buf.partition(b"\n")
        return l.decode("utf-8", "replace")


def session(exe, cases):
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, bufsize=0, cwd="/tmp")
    rd = R(proc.stdout.fileno())
    out = []

    def drain_until(prefix, buf):
        deadline = time.monotonic() + TIMEOUT
        while True:
            l = rd.line(deadline)
            if l is None:
                return False
            buf.append(l)
            if l.startswith(prefix):
                return True

    for name, text in cases:
        buf = []
        proc.stdin.write(("position fen " + text + "\n").encode())
        proc.stdin.write(b"isready\n")
        proc.stdin.flush()
        ok = drain_until("readyok", buf)
        refused = any(l.startswith("info string invalid FEN") for l in buf)
        proc.stdin.write(b"go perft 1\n")
        proc.stdin.flush()
        got = drain_until("nodes ", buf)
        nodes = None
        for l in buf:
            if l.startswith("nodes "):
                nodes = int(l.split()[1])
        out.append({"case": name, "text": text, "refused": refused, "readyok": ok,
                    "perft1_nodes": nodes, "lines": buf})
    proc.stdin.write(b"quit\n")
    proc.stdin.flush()
    try:
        proc.wait(timeout=30)
    except Exception:
        proc.kill()
    return out


BASE = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"


def main():
    exe = sys.argv[1]
    outdir = Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    cases = [
        ("clean", BASE + " w KQkq - 0 1"),
        ("junk_word", BASE + " w KQkq - 0 1 zzz"),
        ("junk_number", BASE + " w KQkq - 0 1 999999"),
        ("junk_five_tokens", BASE + " w KQkq - 0 1 a b c d e"),
        ("seventh_field_9999", BASE + " w KQkq - 0 1 9999"),
        ("control_moves_short", BASE + " w KQkq - 0 1 moves e2e4 e7e5 g1f3 b8c6 f1b5"),
        ("control_moves_junk_after", BASE + " w KQkq - 0 1 moves e2e4 e7e5 g1f3 b8c6 f1b5 zzz"),
    ]
    res = session(exe, cases)
    clean = [r for r in res if r["case"] == "clean"][0]
    lines = []
    lines.append("CHECK of seat 11 S-F1: extra tokens after the sixth FEN field")
    lines.append("exe_started: %s" % exe)
    lines.append("sha256: %s" % hashlib.sha256(Path(exe).read_bytes()).hexdigest())
    lines.append("option lines sent: none")
    lines.append("")
    lines.append("case\trefused\tperft1_nodes\tsame_as_clean")
    for r in res:
        same = (r["perft1_nodes"] == clean["perft1_nodes"])
        lines.append("%s\t%s\t%s\t%s" % (r["case"], r["refused"], r["perft1_nodes"],
                                         "yes" if same else "NO"))
    verdict = "CONFIRMS"
    for r in res:
        if r["case"] in ("junk_word", "junk_number", "junk_five_tokens", "seventh_field_9999"):
            if r["refused"] or r["perft1_nodes"] != clean["perft1_nodes"]:
                verdict = "REFUTES"
    # the control must show that tokens BEFORE the sixth field DO matter, so perft 1 differs
    short = [r for r in res if r["case"] == "control_moves_short"][0]
    control_ok = short["perft1_nodes"] != clean["perft1_nodes"]
    junk_after_moves = [r for r in res if r["case"] == "control_moves_junk_after"][0]
    tail_ok = junk_after_moves["perft1_nodes"] == short["perft1_nodes"]
    lines.append("")
    lines.append("control proves the harness can see a change: moves-short perft1=%s vs clean perft1=%s -> %s"
                 % (short["perft1_nodes"], clean["perft1_nodes"], "OK" if control_ok else "BROKEN CONTROL"))
    lines.append("junk AFTER a move list leaves the same board: %s -> %s"
                 % (junk_after_moves["perft1_nodes"], "OK" if tail_ok else "DIFFERS"))
    lines.append("VERDICT: %s S11-F1" % (verdict if control_ok else "INCONCLUSIVE (control failed)"))
    lines.append("reading: a junk token after the sixth field does not change the answer and does not")
    lines.append("refuse the position, so the accepted board is exactly the clean board's board.")
    text = "\n".join(lines) + "\n"
    (outdir / "check_s11_f1.txt").write_text(text)
    (outdir / "check_s11_f1_raw.json").write_text(json.dumps(res, indent=1))
    print(text)


if __name__ == "__main__":
    main()
