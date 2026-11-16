#!/usr/bin/env python3
"""timing.py — AREA 8 job 1: wall time from sending `go` to reading `bestmove`.

Usage: timing.py EXE OUTDIR CONFIG
CONFIG is one of: mt50 mt500 wt1000 wt10000
Positions: the first 100 of O then the first 100 of G (200 searches per run), FEN part only.
One engine process per run; `ucinewgame` + `isready` before every `go`; Threads 1, Hash 16, S14
settings sent as setoption lines. Timing uses time.monotonic() around the `go` .. `bestmove` exchange.

The engine's stdout is read with os.read() on the RAW fd (bufsize=0, binary), never through a buffered
TextIOWrapper: select() on a buffered wrapper reports "no data" while bytes sit in the wrapper, which
fakes a hang. (A first version of this harness had exactly that bug; 3 of 200 searches timed out at
the 60 s watchdog while the engine was answering normally. See job1/README_HARNESS_BUG.md.)

Writes OUTDIR/<config>.txt (one TSV line per search) and OUTDIR/<config>.meta.
"""
import hashlib
import os
import select
import subprocess
import sys
import time

S14 = {
    "LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
    "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
    "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
    "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true",
}
CONFIGS = {
    "mt50": "go movetime 50",
    "mt500": "go movetime 500",
    "wt1000": "go wtime 1000 btime 1000 winc 10 binc 10",
    "wt10000": "go wtime 10000 btime 10000 winc 100 binc 100",
}


class Engine:
    """Unbuffered line reader over the process's stdout fd."""

    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, bufsize=0)
        self.fd = self.p.stdout.fileno()
        self.buf = b""
        self.log = []

    def send(self, line):
        self.log.append(line)
        self.p.stdin.write((line + "\n").encode())
        self.p.stdin.flush()

    def readline(self, timeout):
        deadline = time.monotonic() + timeout
        while True:
            nl = self.buf.find(b"\n")
            if nl >= 0:
                line, self.buf = self.buf[:nl], self.buf[nl + 1:]
                return line.decode("utf-8", "replace").rstrip("\r")
            left = deadline - time.monotonic()
            if left <= 0:
                return None
            r, _, _ = select.select([self.fd], [], [], min(left, 0.05))
            if not r:
                continue
            chunk = os.read(self.fd, 65536)
            if not chunk:
                return None
            self.buf += chunk

    def read_until(self, token, timeout):
        """Read lines until one starts with token; returns (lines, ok)."""
        lines = []
        deadline = time.monotonic() + timeout
        while True:
            left = deadline - time.monotonic()
            if left <= 0:
                return lines, False
            line = self.readline(left)
            if line is None:
                return lines, False
            lines.append(line)
            if line.split(" ")[0] == token:
                return lines, True

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=5)
        except Exception:
            self.p.kill()
        try:
            self.p.stdout.close()
        except Exception:
            pass


def read_positions(paths, n):
    out = []
    for path in paths:
        with open(path) as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    out.append(line)
                if len(out) >= n:
                    return out
    return out


def main() -> int:
    exe, outdir, config = sys.argv[1], sys.argv[2], sys.argv[3]
    go = CONFIGS[config]
    os.makedirs(outdir, exist_ok=True)
    here = os.path.dirname(os.path.abspath(__file__))
    fens = read_positions([os.path.join(here, "O.fens"), os.path.join(here, "G.epd")], 200)
    fens = [f.split(";")[0].split(" bm")[0].strip() for f in fens]

    sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    meta = [f"exe_started {os.path.abspath(exe)}", f"exe_sha256 {sha}",
            "option Threads 1", "option Hash 16"]
    meta += [f"option {k} {v}" for k, v in S14.items()]

    eng = Engine(exe)
    eng.send("uci")
    lines, ok = eng.read_until("uciok", 20)
    idname = next((l for l in lines if l.startswith("id name")), "id name MISSING")
    meta.append(idname)

    for name, value in [("Threads", 1), ("Hash", 16)] + list(S14.items()):
        eng.send(f"setoption name {name} value {value}")
        eng.send("isready")
        _l, ok = eng.read_until("readyok", 20)
        if not ok:
            print(f"STOP no readyok after setoption {name}", file=sys.stderr)
            return 2
    meta.append(f"go_line {go}")
    meta.append(f"positions {len(fens)}")

    rows = []
    for i, fen in enumerate(fens):
        eng.send("ucinewgame")
        eng.send("isready")
        _l, ok = eng.read_until("readyok", 20)
        if not ok:
            rows.append((i, fen, "NOREOK", "", "", "NOREOK"))
            continue
        eng.send(f"position fen {fen}")
        t0 = time.monotonic()
        eng.send(go)
        lines, ok = eng.read_until("bestmove", 60)
        t1 = time.monotonic()
        wall_ms = (t1 - t0) * 1000.0
        best = ""
        etime = ""
        for line in lines:
            if line.startswith("bestmove"):
                parts = line.split()
                best = parts[1] if len(parts) > 1 else ""
            if line.startswith("info") and " time " in line:
                parts = line.split()
                if "time" in parts:
                    etime = parts[parts.index("time") + 1]
        rows.append((i, fen, f"{wall_ms:.3f}", best, etime, "ok" if ok else "NORESP"))

    eng.close()
    with open(os.path.join(outdir, config + ".txt"), "w") as fh:
        fh.write("i\tfen\twall_ms\tbestmove\tengine_time_ms\tstatus\n")
        for r in rows:
            fh.write("\t".join(str(x) for x in r) + "\n")
    with open(os.path.join(outdir, config + ".meta"), "w") as fh:
        fh.write("\n".join(meta) + "\n")
        fh.write("lines_sent_first200\n" + "\n".join(eng.log[:200]) + "\n")
    print(f"{config}: {len(rows)} searches written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
