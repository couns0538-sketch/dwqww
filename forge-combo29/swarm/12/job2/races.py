#!/usr/bin/env python3
"""races.py EXE OUTDIR — area 2 job 2: interrupt a running search with one command.

For each interrupt command (stop, ponderhit, ucinewgame, setoption Hash, quit) and each
delay in 0..50 ms, start a `go infinite` (or `go depth 30`), sleep the delay, send the one
command, and record what the engine did.

The harness obeys the rule from seat 19: it reads stdout to `bestmove` before sending anything
else, it never closes stdin while a search is still running, and a sequence that ends without a
bestmove gets a `stop` and then a bounded wait, not a `quit`.

Per case: exit code, whether a bestmove arrived, whether it was legal for the position,
sanitizer lines, and the readyok that follows the next `isready`.
"""
import json
import os
import queue
import random
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

import chess

SAN = re.compile(r"ERROR: (AddressSanitizer|LeakSanitizer)|SUMMARY: (Address|Undefined|Leak)Sanitizer|"
                 r"runtime error: ")
POS = "position fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
BOARD = chess.Board(POS.split("fen ")[1])


class Engine:
    """A live engine process with a reader thread; every wait is bounded."""

    def __init__(self, exe, timeout_s=25.0):
        self.timeout_s = timeout_s
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1,
                                  env={"PATH": "/usr/bin:/bin", "ASAN_OPTIONS": "detect_leaks=0",
                                       "UBSAN_OPTIONS": "print_stacktrace=1"})
        self.q = queue.Queue()
        self.lines = []
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for ln in self.p.stdout:
            self.q.put(ln.rstrip("\n"))
        self.q.put(None)

    def send(self, line):
        self.p.stdin.write(line + "\n")
        self.p.stdin.flush()

    def wait_for(self, predicate, bound_s=None):
        """Collect lines until predicate(line) or the bound; returns the matching line."""
        deadline = time.monotonic() + (bound_s if bound_s is not None else self.timeout_s)
        while time.monotonic() < deadline:
            try:
                ln = self.q.get(timeout=0.05)
            except queue.Empty:
                if self.p.poll() is not None:
                    return None
                continue
            if ln is None:
                return None
            self.lines.append(ln)
            if predicate(ln):
                return ln
        return "TIMEOUT"

    def drain(self, quiet_s=0.05):
        while True:
            try:
                ln = self.q.get(timeout=quiet_s)
            except queue.Empty:
                return
            if ln is None:
                return
            self.lines.append(ln)

    def close_cleanly(self):
        """Ask for a bestmove if a search is open, then quit; never close stdin mid-search."""
        try:
            self.send("stop")
            self.wait_for(lambda l: l.startswith("bestmove"), 5.0)
            self.send("quit")
            self.p.stdin.close()
        except (BrokenPipeError, OSError):
            pass
        try:
            self.p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.p.kill()
        return self.p.returncode


def one_case(exe, go_line, interrupt, delay_ms):
    eng = Engine(exe)
    rec = {"go": go_line, "interrupt": interrupt, "delay_ms": delay_ms}
    try:
        eng.send("uci")
        eng.wait_for(lambda l: l == "uciok")
        eng.send(POS)
        eng.send("isready")
        eng.wait_for(lambda l: l == "readyok")
        eng.send(go_line)
        # let the search actually start before interrupting; at 0 ms this is one scheduler tick
        if delay_ms:
            time.sleep(delay_ms / 1000.0)
        else:
            time.sleep(0.0005)
        eng.send(interrupt)

        if interrupt == "quit":
            rc = None
            try:
                rc = eng.p.wait(timeout=eng.timeout_s)
            except subprocess.TimeoutExpired:
                eng.p.kill()
                rec["hung_after_quit"] = True
                rc = eng.p.wait()
            eng.drain(0.05)
            bm = [l for l in eng.lines if l.startswith("bestmove")]
            rec["exit"] = rc
            rec["bestmove"] = bm[-1].split()[1] if bm else None
        else:
            bm_line = eng.wait_for(lambda l: l.startswith("bestmove"), 10.0)
            rec["bestmove"] = (bm_line.split()[1]
                               if bm_line and bm_line != "TIMEOUT" else None)
            rec["no_bestmove"] = bm_line in (None, "TIMEOUT")
            # the engine must still answer isready afterwards
            eng.send("isready")
            ready = eng.wait_for(lambda l: l == "readyok", 10.0)
            rec["readyok_after"] = ready == "readyok"
            rec["exit"] = eng.close_cleanly()
    except (BrokenPipeError, OSError) as exc:
        rec["pipe_error"] = str(exc)
        rec["exit"] = eng.p.poll()

    bm = rec.get("bestmove")
    if bm in (None, "0000"):
        rec["bestmove_legal"] = None          # not applicable / nothing printed
    else:
        try:
            rec["bestmove_legal"] = chess.Move.from_uci(bm) in BOARD.legal_moves
        except ValueError:
            rec["bestmove_legal"] = False
    rec["sanitizer_lines"] = [l for l in eng.lines if SAN.search(l)][:5]
    rec["crash"] = rec.get("exit") is not None and rec["exit"] < 0
    return rec


def main():
    exe, outdir = sys.argv[1], Path(sys.argv[2])
    per = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    outdir.mkdir(parents=True, exist_ok=True)

    sha = subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0]
    probe = subprocess.run([exe], input="uci\nquit\n", capture_output=True, text=True)
    id_name = next((l for l in probe.stdout.splitlines() if l.startswith("id name")), "?")
    nm = subprocess.run(f"nm -C {exe} | grep -c __asan_", shell=True,
                        capture_output=True, text=True).stdout.strip()
    (outdir / "races.meta").write_text(
        f"exe: {exe}\nsha256: {sha}\n{id_name}\ndate_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n"
        f"nm_asan: {nm}\n"
        f"position: {POS}\n"
        f"go lines: go infinite, go depth 30\n"
        f"interrupts: stop, ponderhit, ucinewgame, setoption name Hash value 64, quit\n"
        f"delays: random 0..50 ms, {per} cases per (go, interrupt) pair\n"
        "options_sent: setoption name Hash value 64 (only as the interrupt under test)\n"
        "env: ASAN_OPTIONS=detect_leaks=0 UBSAN_OPTIONS=print_stacktrace=1\n")
    print((outdir / "races.meta").read_text())

    rng = random.Random(1201)
    gotos = ["go infinite", "go depth 30"]
    interrupts = ["stop", "ponderhit", "ucinewgame", "setoption name Hash value 64", "quit"]
    all_recs = []
    out = (outdir / "races.jsonl").open("w")
    for go_line in gotos:
        for interrupt in interrupts:
            stats = {"cases": 0, "crash": 0, "san": 0, "illegal": 0, "no_bm": 0,
                     "no_readyok": 0, "hang_quit": 0}
            for _ in range(per):
                delay = rng.randint(0, 50)
                rec = one_case(exe, go_line, interrupt, delay)
                all_recs.append(rec)
                out.write(json.dumps(rec) + "\n")
                out.flush()
                stats["cases"] += 1
                stats["crash"] += bool(rec["crash"])
                stats["san"] += bool(rec["sanitizer_lines"])
                stats["illegal"] += rec.get("bestmove_legal") is False
                stats["no_bm"] += bool(rec.get("no_bestmove")) or rec.get("bestmove") is None
                stats["no_readyok"] += rec.get("readyok_after") is False
                stats["hang_quit"] += bool(rec.get("hung_after_quit"))
            print(f"{go_line:12} | {interrupt:28} | cases {stats['cases']:3} crash {stats['crash']:2} "
                  f"san {stats['san']:2} illegal {stats['illegal']:2} no_bestmove {stats['no_bm']:3} "
                  f"no_readyok {stats['no_readyok']:2} hangquit {stats['hang_quit']:2}", flush=True)
    out.close()
    bad = [r for r in all_recs if r["crash"] or r["sanitizer_lines"] or r.get("bestmove_legal") is False
           or r.get("readyok_after") is False or r.get("hung_after_quit")]
    print(f"\ntotal cases {len(all_recs)}; cases that fired anything: {len(bad)}")
    for r in bad[:20]:
        print(f"  {r}")
    (outdir / "races.summary.json").write_text(json.dumps({"total": len(all_recs),
                                                           "fired": bad}, indent=1) + "\n")


if __name__ == "__main__":
    main()
