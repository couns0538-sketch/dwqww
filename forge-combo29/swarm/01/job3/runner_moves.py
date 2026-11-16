#!/usr/bin/env python3
"""swarm seat 01, job 3 runner: replay a committed ply list through `position startpos moves`, then the
same list with ONE illegal move at ply 1, 10 and 500.

Every case is a FRESH engine process:
    position startpos moves <plies...>
    isready                       (every answer line kept, read to readyok)
    go perft 1                    (read to `nodes N`)
python-chess replays the prefix the engine is supposed to keep and its legal-move count is compared
with the engine's `nodes N`.

Usage: runner_moves.py <exe> <plies-file> <outdir>
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

TIMEOUT = 180.0
ILLEGAL = "e1e3"


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


def replay(plies):
    b = chess.Board()
    for p in plies:
        b.push(chess.Move.from_uci(p))
    return b


def engine_case(exe, plies, label, illegal_at=None):
    sent = list(plies)
    if illegal_at is not None:
        idx = illegal_at - 1
        b = replay(sent[:idx])
        assert chess.Move.from_uci(ILLEGAL) not in b.legal_moves, "injected move is legal there"
        sent = sent[:idx] + [ILLEGAL] + sent[idx:]

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

    t0 = time.monotonic()
    send("position startpos moves " + " ".join(sent))
    send("isready")
    ready = until("readyok")
    setup_s = time.monotonic() - t0
    answer = [l for l in buf if l.startswith("info string")]
    nodes = None
    if ready is not None:
        send("go perft 1")
        if until("nodes ") is not None:
            for l in buf:
                if l.startswith("nodes "):
                    nodes = int(l.split()[1])
    send("quit")
    try:
        p.wait(timeout=60)
    except Exception:
        p.kill()
    san = [l for l in buf if ("AddressSanitizer" in l or "runtime error" in l or "SUMMARY:" in l)]
    return {"label": label, "illegal_at": illegal_at, "plies_sent": len(sent),
            "answer_lines": answer, "perft1_engine": nodes, "setup_seconds": round(setup_s, 2),
            "sanitizer": san, "crashed": ready is None}


def main():
    exe = sys.argv[1]
    pliesfile = sys.argv[2]
    outdir = Path(sys.argv[3])
    outdir.mkdir(parents=True, exist_ok=True)
    plies = open(pliesfile).read().split()
    replay(plies)  # the whole list is legal, asserted by the generator too

    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    nm = subprocess.run(["nm", "-C", exe], capture_output=True, text=True).stdout
    meta = [
        "exe_started: %s" % exe,
        "sha256: %s" % sha,
        "nm -C grep -c __asan_ : %d" % sum(1 for l in nm.splitlines() if "__asan_" in l),
        "nm -C grep -c __ubsan_ : %d" % sum(1 for l in nm.splitlines() if "__ubsan_" in l),
        "option lines sent: NONE",
        "per case: 'position startpos moves <list>' then 'isready' read to readyok then 'go perft 1'",
        "injected illegal move: %s (king two squares); verified illegal in the target position" % ILLEGAL,
        "ply list file: %s (%d plies)" % (pliesfile, len(plies)),
    ]
    (outdir / "meta.txt").write_text("\n".join(meta) + "\n")

    cases = [("full_list", None), ("illegal_ply_1", 1), ("illegal_ply_10", 10), ("illegal_ply_500", 500)]
    results = []
    for label, at in cases:
        rec = engine_case(exe, plies, label, at)
        keep = plies if at is None else plies[:at - 1]
        board = replay(keep)
        rec["expected_perft1"] = board.legal_moves.count()
        rec["expected_fen"] = board.fen()
        rec["match"] = rec["perft1_engine"] == rec["expected_perft1"]
        results.append(rec)
        print("%-16s sent=%-5d answer=%-45s perft1=%-4s expected=%-4d match=%s"
              % (label, rec["plies_sent"], "; ".join(rec["answer_lines"]) or "(none)",
                 rec["perft1_engine"], rec["expected_perft1"], rec["match"]), flush=True)
    (outdir / "results.json").write_text(json.dumps(results, indent=1))

    lines = ["job 3 table: 1,000-ply move list and one illegal move at ply 1 / 10 / 500",
             "case\tplies_sent\tanswer_lines\tperft1_engine\tpython_chess_perft1\tmatch\tsetup_s\tsanitizer"]
    for r in results:
        lines.append("%s\t%d\t%s\t%s\t%d\t%s\t%s\t%d" % (
            r["label"], r["plies_sent"], "; ".join(r["answer_lines"]) or "(none)",
            r["perft1_engine"], r["expected_perft1"], r["match"], r["setup_seconds"],
            len(r["sanitizer"])))
    text = "\n".join(lines) + "\n"
    (outdir / "table.txt").write_text(text)
    (outdir / "expected_fens.txt").write_text(
        "\n".join("%s\t%s" % (r["label"], r["expected_fen"]) for r in results) + "\n")
    print("")
    print(text)


if __name__ == "__main__":
    main()
