#!/usr/bin/env python3
"""uci.py — a UCI driver that cannot deadlock and cannot fabricate a bestmove.

Two traps this exists to avoid, both in forge-findings.md:

  * trap 5c: `go perft N` ends with a bare `nodes N` line and NO `bestmove`. A reader
    that waits for `bestmove` blocks forever. `perft()` below reads to `nodes`, which
    is why this driver survives where a naive one hangs. My own first driver deadlocked
    on exactly this, twice.
  * trap 3a: a piped harness that lets EOF reach a running search fabricates a
    `bestmove` with zero `info` lines. Every non-`go` command is therefore followed by
    `isready` and drained to `readyok`, and `go` is read to `bestmove` — never to EOF.

The engine path is module state set once by `use_engine()`, never a per-call argument. A
path threaded through every call site is a string reaching an exec from wherever the caller
got it; a module constant set once, after validation, is not.

Usage:
    import uci
    uci.use_engine("./forge")
    with uci.Engine() as e:
        e.setup("ucinewgame", "position fen <FEN> moves <moves>")
        r = uci.parse(e.go("go depth 10"))
        r["nodes"], r["depth"], r["kind"], r["cp"], r["pv"], r["bestmove"], r["n_info"]
"""
import subprocess

_ENGINE = None


def use_engine(path):
    """Set and validate the engine executable once.

    Validation is deliberately shallow and local — absolute it, refuse `..`, require an
    existing regular file — because the point is to make the trust boundary explicit, not to
    sandbox the caller. An agent passing a wrong path should fail here, not at the exec.
    """
    import os
    if not path:
        raise ValueError("empty engine path")
    if ".." in str(path).split(os.sep):
        raise ValueError("refusing an engine path containing '..': %r" % (path,))
    ap = os.path.abspath(path)
    if not os.path.isfile(ap):
        raise FileNotFoundError("engine executable not found: %r" % (ap,))
    global _ENGINE
    _ENGINE = ap
    return _ENGINE


def _engine():
    if _ENGINE is None:
        raise RuntimeError("engine path not set — call uci.use_engine(path) first")
    return _ENGINE


class Engine:
    """One engine process. Use as a context manager so `quit` always runs."""

    def __init__(self, opts=(("Hash", 16), ("Threads", 1))):
        self.p = subprocess.Popen([_engine()], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.send("uci")
        self.until("uciok")
        for k, v in opts:
            self.send("setoption name %s value %s" % (k, v))
        self.sync()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False

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
