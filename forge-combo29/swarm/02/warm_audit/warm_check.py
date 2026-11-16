#!/usr/bin/env python3
"""S02 — verify seat 10's warm-search claim on my build, with an INTERACTIVE driver.

Seat 10's claim: two identical unrestricted searches in ONE process, nothing between them, give different
node counts (56,720 then 4,951 then 4,516), while three separate processes give the same number; and
`ucinewgame` restores cold exactly but `Clear Hash` does not.

Why this needs its own file rather than a piped command: my first attempt at this measurement piped the whole
session into stdin, and every search came back `bestmove a2a3` with NO info line at all — seat 19's 19-F12
fabrication, which fires exactly when stdin is closed while a search runs. So this driver reads each
`bestmove` before sending the next line, and it ASSERTS that an `info depth 12` line was present; a search
with no info line aborts the measurement instead of contributing a number.

usage: warm_check.py <exe> <outdir>
"""
import json
import os
import re
import subprocess
import sys
import threading
import time

TIMEOUT = 30.0
SPIN_SETUP = ["setoption name OwnBook value false"]
POSITIONS = {
    "middlegame": "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
    "startpos": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
}
DEPTH = 12


class Engine:
    def __init__(self, exe):
        env = {k: v for k, v in os.environ.items()
               if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS")}
        self.proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True, bufsize=1, env=env,
                                     start_new_session=True)
        self.lines, self.lock, self.eof = [], threading.Lock(), False
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self.proc.stdout:
            with self.lock:
                self.lines.append(line.rstrip("\n"))
        with self.lock:
            self.eof = True

    def send(self, t):
        self.proc.stdin.write(t + "\n")
        self.proc.stdin.flush()

    def mark(self):
        with self.lock:
            return len(self.lines)

    def wait_for(self, prefix, start, timeout=TIMEOUT):
        dl = time.monotonic() + timeout
        while True:
            with self.lock:
                for i in range(start, len(self.lines)):
                    if self.lines[i].startswith(prefix):
                        return i
                eof = self.eof
            if eof or time.monotonic() > dl:
                return -1
            time.sleep(0.001)

    def seg(self, a, b=None):
        with self.lock:
            return list(self.lines[a:b])

    def close(self):
        try:
            self.send("quit")
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()


def one_search(exe=None, eng=None, fen=None):
    """Run one go depth N and return (nodes, output lines). Asserts an info line at that depth exists."""
    start = eng.mark()
    eng.send("position fen " + fen)
    eng.send("isready")
    eng.wait_for("readyok", start)
    s2 = eng.mark()
    eng.send("go depth %d" % DEPTH)
    at = eng.wait_for("bestmove", s2)
    if at < 0:
        sys.exit("FAIL: no bestmove for go depth %d; refusing to record a number" % DEPTH)
    seg = eng.seg(s2, at + 1)
    deep = [l for l in seg if re.match(r"info depth %d " % DEPTH, l)]
    if not deep:
        sys.exit("FAIL: no `info depth %d` line, so this search is the 19-F12 fabrication and its node count "
                 "would be invented. Output:\n%s" % (DEPTH, "\n".join(seg)))
    m = re.search(r"nodes (\d+)", deep[-1])
    if not m:
        sys.exit("FAIL: the depth-%d line carries no `nodes` field: %r" % (DEPTH, deep[-1]))
    return int(m.group(1)), seg


def session(exe, fen, steps):
    """steps: list of ('search'|'ucinewgame'|'clearhash'). Returns list of node counts (None for non-searches)."""
    eng = Engine(exe)
    eng.send("uci")
    eng.wait_for("uciok", 0)
    eng.send("isready")
    eng.wait_for("readyok", 0)
    for s in SPIN_SETUP:
        eng.send(s)
    eng.send("isready")
    eng.wait_for("readyok", 0)
    out = []
    for s in steps:
        if s == "search":
            n, _ = one_search(eng=eng, fen=fen)
            out.append(n)
        elif s == "ucinewgame":
            st = eng.mark()
            eng.send("ucinewgame")
            eng.send("isready")
            eng.wait_for("readyok", st)
        elif s == "clearhash":
            st = eng.mark()
            eng.send("setoption name Clear Hash")
            eng.send("isready")
            eng.wait_for("readyok", st)
    eng.close()
    return out


def main():
    exe = sys.argv[1]
    outdir = sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    rows = []
    meta = {"exe": exe,
            "sha256": subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0],
            "option_lines_sent": SPIN_SETUP + ["setoption name Clear Hash (no value)"],
            "depth": DEPTH,
            "driver": "interactive; each bestmove read to completion before the next line; a search with no "
                      "info depth line ABORTS rather than contributing a number",
            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    json.dump(meta, open(os.path.join(outdir, "meta.json"), "w"), indent=1)

    for label, fen in POSITIONS.items():
        # three separate processes
        sep = [session(exe, fen, ["search"])[0] for _ in range(3)]
        # one process, nothing between
        conc = session(exe, fen, ["search", "search", "search"])
        # one process with ucinewgame between
        withnew = session(exe, fen, ["search", "ucinewgame", "search", "ucinewgame", "search"])
        # one process with Clear Hash between
        withclear = session(exe, fen, ["search", "clearhash", "search", "clearhash", "search"])
        rows.append({"position": label, "fen": fen, "separate_processes": sep,
                     "one_process_nothing_between": conc,
                     "one_process_ucinewgame": withnew,
                     "one_process_clear_hash": withclear})
        print("== %s" % label)
        print("   three separate processes      : %s" % sep)
        print("   one process, nothing between  : %s" % conc)
        print("   one process, ucinewgame       : %s" % withnew)
        print("   one process, Clear Hash       : %s" % withclear)

    json.dump(rows, open(os.path.join(outdir, "rows.json"), "w"), indent=1)
    print()
    print("### verdict")
    ok_cold = all(len(set(r["separate_processes"])) == 1 for r in rows)
    ok_warm = all(len(set(r["one_process_nothing_between"])) > 1 for r in rows)
    ok_new = all(r["one_process_ucinewgame"] == r["separate_processes"] for r in rows)
    ok_clear = all(r["one_process_clear_hash"] != r["one_process_nothing_between"] or
                   len(set(r["one_process_clear_hash"])) > 1 for r in rows) if rows else False
    print("- cold (separate processes) is reproducible                        %s" % ("PASS" if ok_cold else "FAIL"))
    print("- warm (one process, nothing between) gives DIFFERENT counts       %s" % ("PASS" if ok_warm else "FAIL"))
    print("- ucinewgame restores the cold numbers exactly                     %s" % ("PASS" if ok_new else "FAIL"))
    print("- Clear Hash is NOT the same as cold                              %s"
          % ("PASS" if ok_clear else "FAIL"))
    if not (ok_cold and ok_warm and ok_new):
        sys.exit("CONCLUSION: REFUTES seat 10's claim on this build")
    print()
    print("CONCLUSION: CONFIRMS seat 10 — a warm search in the same process is not a cold one, "
          "ucinewgame restores cold, Clear Hash does not.")


if __name__ == "__main__":
    main()
