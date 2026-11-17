#!/usr/bin/env python3
"""uci.py — a UCI driver that cannot deadlock and cannot fabricate a bestmove.

Two traps this exists to avoid, both in forge-findings.md:

  * trap 5c: `go perft N` ends with a bare `nodes N` line and NO `bestmove`. A reader
    that waits for `bestmove` blocks forever. `perft()` below reads to `nodes`, which
    is why this driver survives where a naive one hangs.
  * trap 3a: a piped harness that lets EOF reach a running search fabricates a
    `bestmove` with zero `info` lines. Every non-`go` command is therefore followed by
    `isready` and drained to `readyok`, and `go` is read to `bestmove` — never to EOF.

Usage:
    from uci import Engine, parse, perft
    e = Engine("./forge", (("Hash", 16), ("Threads", 1), ("OwnBook", "false")))
    e.setup("ucinewgame", "position fen <FEN> moves <moves>")
    r = parse(e.go("go depth 10"))
    r["nodes"], r["depth"], r["kind"], r["cp"], r["pv"], r["bestmove"], r["n_info"]
"""
import subprocess


class Engine:
    def __init__(self, exe, opts=(("Hash", 16), ("Threads", 1))):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.send("uci")
        self.until("uciok")
        for k, v in opts:
            self.send("setoption name %s value %s" % (k, v))
        self.sync()

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def until(self, prefix):
        lines = []
        while True:
            ln = self.p.stdout.readline()
            if not ln:
                raise SystemExit("engine closed waiting for %r; got %r" % (prefix, lines))
            ln = ln.rstrip("\n")
            lines.append(ln)
            if ln.startswith(prefix):
                return lines

    def sync(self):
        self.send("isready")
        return self.until("readyok")

    def setup(self, *commands):
        for c in commands:
            self.send(c)
        return self.sync()

    def go(self, spec):
        self.send(spec)
        return self.until("bestmove")

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            self.p.kill()


def parse(lines):
    """Last `info depth` line's fields plus the bestmove."""
    out = {"info": [], "bestmove": None, "n_info": 0}
    for ln in lines:
        if ln.startswith("info depth"):
            out["info"].append(ln)
        elif ln.startswith("bestmove"):
            out["bestmove"] = ln.split()[1]
    out["n_info"] = len(out["info"])
    if out["info"]:
        f = out["info"][-1].split()

        def g(k):
            return f[f.index(k) + 1] if k in f else None

        out["depth"] = int(g("depth"))
        out["seldepth"] = int(g("seldepth"))
        out["nodes"] = int(g("nodes"))
        out["kind"] = f[f.index("score") + 1] if "score" in f else None
        out["cp"] = f[f.index("score") + 2] if "score" in f else None
        out["pv"] = f[f.index("pv") + 1:] if "pv" in f else []
    return out


def perft(engine, depth):
    """`go perft N` terminates with a bare `nodes N` line and no bestmove (trap 5c)."""
    engine.send("go perft %d" % depth)
    out = []
    while True:
        ln = engine.p.stdout.readline()
        if not ln:
            raise SystemExit("engine closed during perft")
        ln = ln.rstrip("\n")
        out.append(ln)
        if ln.startswith("nodes "):
            return out
