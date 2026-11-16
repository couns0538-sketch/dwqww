#!/usr/bin/env python3
"""seat 17: setoption to an EXTREME while a search is running.

The dangerous combination the coordinator asked for: `setoption` mid-search is known to truncate
the search, and an extreme value on top of that is the worst case.

How this harness avoids my earlier select()+readline() artefact (see NOTE_select_readline_artifact.md):
stdout is read by a DEDICATED READER THREAD on a BINARY pipe, so reading never blocks the writer and
there is no `select` + buffered `readline` pairing. Every command is still answered in order, and the
search is never left with stdin closed (19-F12).

Per case:
  1. uci / isready / PC20 / isready / position / isready
  2. send `go infinite` (or the given go line)
  3. wait `delay_ms`, then send `setoption name <switch> value <extreme>` + `isready`
  4. wait for `readyok`; then send `stop` and wait for `bestmove`
  5. record: bestmove (and whether it is legal), how many info lines arrived before the setoption,
     whether `readyok` came, whether `bestmove` came after stop, and every sanitizer word.

A case where no `bestmove` ever arrives is a HANG and is recorded as such, never as a pass.

usage: midsetopt.py <exe> <outdir>
"""
import json
import os
import queue
import subprocess
import sys
import threading
import time

import chess

S14 = [
    ("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
    ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
    ("IirDepth", "2"), ("NonPawnCorrection", "true"),
]
PC20_EXTRA = [
    ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
    ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false"),
]
PC20 = S14 + PC20_EXTRA

FEN = "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1"

# (label, option, extreme value) -- extremes chosen as the worst a GUI could send
CASES = [
    ("HistRework_max", "HistRework", "3"),
    ("HistRework_above_max", "HistRework", "9"),
    ("Hash_min", "Hash", "1"),
    ("Hash_max", "Hash", "2048"),
    ("Threads_max", "Threads", "256"),
    ("CuckooRep_on", "CuckooRep", "true"),
    ("TtPruneV2_on", "TtPruneV2", "true"),
    ("CorrHistV2_on", "CorrHistV2", "true"),
    ("LmrQuietBase_extreme", "LmrQuietBase", "300"),
    ("HistoryBonusMax_extreme", "HistoryBonusMax", "10000"),
    ("SingularDepth_extreme", "SingularDepth", "20"),
    ("MultiPV_max", "MultiPV", "8"),
    ("DrawJitter_max", "DrawJitter", "8"),
]


class Engine:
    """Binary pipe + dedicated reader thread. No select/readline pairing anywhere."""

    def __init__(self, exe, env=None):
        self.proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, bufsize=0, env=env)
        self.lines = queue.Queue()
        self.buffer = b""
        self._stop = False
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()
        self.all_text = []

    def _read(self):
        while not self._stop:
            chunk = self.proc.stdout.read(65536)
            if not chunk:
                break
            self.buffer += chunk
            while b"\n" in self.buffer:
                raw, self.buffer = self.buffer.split(b"\n", 1)
                text = raw.decode("utf-8", "replace").rstrip("\r")
                self.all_text.append(text)
                self.lines.put(text)

    def send(self, line):
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def wait_for(self, predicate, timeout):
        """Wait for a line matching predicate. Returns (line, elapsed) or (None, elapsed)."""
        start = time.monotonic()
        while True:
            remaining = timeout - (time.monotonic() - start)
            if remaining <= 0:
                return None, time.monotonic() - start
            try:
                line = self.lines.get(timeout=min(remaining, 0.05))
            except queue.Empty:
                continue
            if predicate(line):
                return line, time.monotonic() - start

    def count_until(self, predicate, timeout):
        """Consume lines until predicate; return the count of lines before it."""
        start = time.monotonic()
        count = 0
        while True:
            remaining = timeout - (time.monotonic() - start)
            if remaining <= 0:
                return None, count
            try:
                line = self.lines.get(timeout=min(remaining, 0.05))
            except queue.Empty:
                continue
            count += 1
            if predicate(line):
                return line, count

    def close(self):
        try:
            self.send("quit")
        except (BrokenPipeError, ValueError, OSError):
            pass
        time.sleep(0.1)
        self._stop = True
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()


def run_case(exe, label, option, value, go_line, delay_ms, outdir, env):
    eng = Engine(exe, env=env)
    rec = {"case": label, "option": option, "value": value, "go": go_line,
           "delay_ms": delay_ms, "exe": exe}
    try:
        eng.send("uci")
        eng.wait_for(lambda l: l.strip() == "uciok", 30)
        for name, val in PC20:
            eng.send("setoption name %s value %s" % (name, val))
            eng.send("isready")
            eng.wait_for(lambda l: l.strip() == "readyok", 30)
        eng.send("position fen " + FEN)
        eng.send("isready")
        eng.wait_for(lambda l: l.strip() == "readyok", 30)

        eng.send(go_line)
        time.sleep(delay_ms / 1000.0)
        before = sum(1 for l in eng.all_text if l.startswith("info depth"))
        eng.send("setoption name %s value %s" % (option, value))
        eng.send("isready")
        # The setoption truncates the search, which may emit `bestmove` BEFORE the `readyok`.
        # Consuming lines up to readyok with a bare predicate would swallow that bestmove and then
        # report a HANG that never happened (12 of 12 false hangs in my first run of this script).
        # So every line consumed while waiting is kept and inspected.
        seen_while_waiting = []
        deadline = time.monotonic() + 20
        ready = None
        while time.monotonic() < deadline:
            try:
                line = eng.lines.get(timeout=0.05)
            except queue.Empty:
                continue
            seen_while_waiting.append(line)
            if line.strip() == "readyok":
                ready = line
                break
        bestmove_during_wait = [l for l in seen_while_waiting if l.startswith("bestmove")]
        rec["readyok_after_setoption"] = ready is not None
        rec["info_lines_before_setoption"] = before
        rec["bestmove_before_readyok"] = bestmove_during_wait[0] if bestmove_during_wait else None

        eng.send("stop")
        if bestmove_during_wait:
            best, best_elapsed = bestmove_during_wait[0], 0.0
        else:
            best, best_elapsed = eng.wait_for(lambda l: l.startswith("bestmove"), 25)
        rec["bestmove"] = best
        rec["bestmove_wait_s"] = round(best_elapsed, 3)
        rec["hang"] = best is None

        # is the answered move legal in FEN?
        if best:
            move = best.split()[1]
            try:
                board = chess.Board(FEN)
                rec["legal"] = move in [m.uci() for m in board.legal_moves]
            except ValueError:
                rec["legal"] = None
        text = "\n".join(eng.all_text)
        rec["sanitizer"] = [l for l in text.splitlines()
                            if "AddressSanitizer" in l or "runtime error" in l or "SUMMARY: " in l][:3]
        rec["complaints"] = [l for l in text.splitlines()
                             if "unknown option" in l or "invalid value" in l][:3]
    finally:
        eng.close()
        open(os.path.join(outdir, label + ".log"), "w").write("\n".join(eng.all_text) + "\n")
    return rec


def main():
    exe, outdir = sys.argv[1:3]
    os.makedirs(outdir, exist_ok=True)
    env = dict(os.environ)
    env["ASAN_OPTIONS"] = "detect_leaks=0:abort_on_error=0"
    env["UBSAN_OPTIONS"] = "print_stacktrace=1:halt_on_error=0"
    env.pop("TSAN_OPTIONS", None)
    rows = []
    for label, option, value in CASES:
        for go_line, delay in (("go infinite", 300), ("go nodes 2000000", 200)):
            tag = "%s_%s" % (label, go_line.replace(" ", ""))
            rec = run_case(exe, tag, option, value, go_line, delay, outdir, env)
            rows.append(rec)
            print(json.dumps({k: v for k, v in rec.items()}), flush=True)
    json.dump(rows, open(os.path.join(outdir, "midsetopt.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
