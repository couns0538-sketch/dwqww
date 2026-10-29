#!/usr/bin/env python3
"""UCI regression for the NnueInt16 option (opus-sol-SA2).

  python3 tools/nnue_int16_regression.py <forge_exe>             (an engine built with FORGE_NNUE_INT16)
  python3 tools/nnue_int16_regression.py --absent <forge_exe>    (the default build, switch off)

Checks: the option is listed as `check default false`; an invalid value is reported and keeps the float path;
bench nodes OFF == the AL1 lock pins, ON == the NnueInt16 pins (integer arithmetic is exact, so the ON pins are
platform-independent), and OFF again == the lock pins (switching back restores the float path); a Threads 2 search
with NnueInt16 ON reaches its bestmove; a setoption that arrives during `go infinite` stops the search first (no
data race on the mode flag; the TSan CI job runs this). Waits for engine output, no sleeps.
--absent (R3 stack: the integer path is the build switch FORGE_NNUE_INT16, default off): the option is not listed,
`setoption name NnueInt16 value true` reports an unknown option and bench stays at the lock pins."""
import queue
import re
import subprocess
import sys
import threading

LOCK = {11: 312866, 13: 862329}
INT16 = {11: 330610, 13: 858175}


class Engine:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
        self.lines = queue.Queue()
        threading.Thread(target=self._read, daemon=True).start()
        self.seen = []

    def _read(self):
        for line in self.p.stdout:
            self.lines.put(line.rstrip("\n"))
        self.lines.put(None)

    def send(self, text):
        self.p.stdin.write(text + "\n")
        self.p.stdin.flush()

    def wait(self, pattern, timeout=600):
        rx = re.compile(pattern)
        while True:
            line = self.lines.get(timeout=timeout)
            if line is None:
                raise SystemExit(f"engine exited while waiting for {pattern!r}")
            self.seen.append(line)
            m = rx.search(line)
            if m:
                return m

    def ready(self):
        self.send("isready")
        self.wait(r"^readyok$")

    def bench(self, depth):
        self.send(f"bench {depth}")
        return int(self.wait(rf"^info string bench depth {depth} nodes (\d+) ").group(1))


def absent(exe):
    """The default build (no FORGE_NNUE_INT16): no NnueInt16 option, a setoption for it changes nothing."""
    failures = []

    def check(ok, what):
        print(("ok    " if ok else "FAIL: ") + what, flush=True)
        if not ok:
            failures.append(what)

    e = Engine(exe)
    e.send("uci")
    e.wait(r"^uciok$")
    check(not any("NnueInt16" in s for s in e.seen), "uci does not list NnueInt16 (build switch off)")
    for o in ("Threads value 1", "Hash value 16", "OwnBook value false", "NnueInt16 value true"):
        e.send("setoption name " + o)
    mark = len(e.seen)
    e.ready()
    for d, n in LOCK.items():
        got = e.bench(d)
        check(got == n, f"after setoption NnueInt16 true: bench d{d} nodes {got} == lock {n}")
    check([s for s in e.seen[mark:] if "NnueInt16" in s] == ["info string unknown option NnueInt16"],
          "absent NnueInt16 is reported as unknown")
    e.send("quit")
    e.p.wait(timeout=60)
    if failures:
        print(f"nnue_int16_regression --absent: {len(failures)} failure(s)")
        return 1
    print("nnue_int16_regression --absent: all checks passed")
    return 0


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--absent":
        return absent(sys.argv[2])
    exe = sys.argv[1]
    failures = []

    def check(ok, what):
        print(("ok    " if ok else "FAIL: ") + what, flush=True)
        if not ok:
            failures.append(what)

    e = Engine(exe)
    e.send("uci")
    e.wait(r"^uciok$")
    check("option name NnueInt16 type check default false" in e.seen, "uci lists NnueInt16 as check default false")
    for o in ("Threads value 1", "Hash value 16", "OwnBook value false"):
        e.send("setoption name " + o)
    e.send("setoption name NnueInt16 value maybe")
    e.wait(r"^info string invalid value for option NnueInt16$")
    check(True, "invalid value reported")
    e.ready()
    for d, n in LOCK.items():
        got = e.bench(d)
        check(got == n, f"OFF bench d{d} nodes {got} == lock {n}")
    e.send("setoption name NnueInt16 value true")
    e.wait(r"^info string NnueInt16 active$")
    e.ready()
    for d, n in INT16.items():
        got = e.bench(d)
        check(got == n, f"ON bench d{d} nodes {got} == NnueInt16 pin {n}")
    e.send("setoption name NnueInt16 value false")
    e.ready()
    check(not any("NnueInt16" in s for s in e.seen[-3:]), "OFF prints no NnueInt16 info line")
    got = e.bench(11)
    check(got == LOCK[11], f"OFF again bench d11 nodes {got} == lock {LOCK[11]}")
    # Threads 2 with NnueInt16 ON, then a setoption that arrives during go infinite.
    e.send("setoption name Threads value 2")
    e.send("setoption name NnueInt16 value true")
    e.wait(r"^info string NnueInt16 active$")
    e.send("position startpos moves e2e4 c7c5 g1f3")
    e.send("go depth 9")
    m = e.wait(r"^bestmove (\S+)")
    check(m.group(1) != "0000", f"Threads 2 ON search returns a move ({m.group(1)})")
    e.send("go infinite")
    e.wait(r"^info depth 2 ")
    e.send("setoption name NnueInt16 value false")
    e.wait(r"^bestmove ")
    e.ready()
    check(True, "setoption during go infinite stops the search first")
    e.send("setoption name Threads value 1")
    e.ready()
    got = e.bench(11)
    check(got == LOCK[11], f"after the threaded searches, OFF bench d11 nodes {got} == lock {LOCK[11]}")
    e.send("quit")
    e.p.wait(timeout=60)
    if failures:
        print(f"nnue_int16_regression: {len(failures)} failure(s)")
        return 1
    print("nnue_int16_regression: all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
