"""uci_driver.py - small, bounded UCI driver for Forge identity checks (no games, no matches).

usage (python -I -B uci_driver.py <cmd> ...; JSON result on stdout, non-zero exit on any failure):
  uciopts <exe> [--opt N=V ...]                    the engine's `option name ...` lines after `uci`
  bench   <exe> --depths 11,13,16 [--nnue on|off] [--opt N=V ...] [--opt-seq "N=V,N=V;N=V"]
                                                   bench node counts; --opt-seq applies option groups in order
                                                   (';' separates groups, each group followed by one bench set)
  perft   <exe> --depth 5 --pos startpos|kiwipete
  fens    <exe> --fens <file> --depth 13 [--nnue on|off] [--opt N=V ...] [--limit N] --out <tsv>
          QA L3 protocol: per FEN `ucinewgame`, `isready`, `position fen`, `go depth D` (OwnBook false, Threads 1,
          Hash 16); records depth, score and nodes of the last `info depth` line and the bestmove.
  warm    <exe> --fens <file> --nodes 20000 [--limit N] --out <tsv>
          warm-table protocol: one `ucinewgame` at the start, then `position fen` + `go nodes N` per FEN.
Placement: the driver pins itself to CPUs 12-15 at Idle priority before starting the engine (the engine inherits
it) and verifies the engine process's affinity and priority; it refuses to run otherwise. Any `info string ...
invalid` reply to a setoption fails the run.
"""
import json
import queue
import re
import subprocess
import sys
import threading
import time

import psutil

CPUS = [12, 13, 14, 15]
KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
INFO_RE = re.compile(r"^info depth (\d+) .*?score (cp -?\d+|mate -?\d+)(?: (?:lowerbound|upperbound))? nodes (\d+)")
BENCH_RE = re.compile(r"^info string bench depth (\d+) nodes (\d+)")


def place_self():
    me = psutil.Process()
    me.cpu_affinity(CPUS)
    me.nice(psutil.IDLE_PRIORITY_CLASS)
    if sorted(me.cpu_affinity()) != CPUS or me.nice() != psutil.IDLE_PRIORITY_CLASS:
        raise SystemExit("placement not applied")


class Engine:
    """One engine process. Output is read by a thread so every wait has a real timeout. The engine is never killed
    (job rule): on any failure it is asked to stop and quit and its stdin is closed, which ends Forge's command loop;
    if it still has not exited after 60 s, its pid is reported so the owner can decide."""

    def __init__(self, exe, timeout=3600.0):
        self.timeout = timeout
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, bufsize=1, encoding="ascii", errors="replace")
        self.q = queue.Queue()
        threading.Thread(target=self._reader, daemon=True).start()
        self.log = []
        child = psutil.Process(self.p.pid)
        if sorted(child.cpu_affinity()) != CPUS or child.nice() != psutil.IDLE_PRIORITY_CLASS:
            self.fail(f"engine placement wrong: {child.cpu_affinity()} {child.nice()}")

    def _reader(self):
        for line in self.p.stdout:
            self.q.put(line)
        self.q.put(None)

    def send(self, line):
        self.p.stdin.write(line + "\n")
        self.p.stdin.flush()

    def until(self, pred):
        deadline = time.time() + self.timeout
        while True:
            left = deadline - time.time()
            if left <= 0:
                self.fail(f"timeout after {self.timeout:.0f} s waiting for the engine")
            try:
                line = self.q.get(timeout=min(left, 5.0))
            except queue.Empty:
                continue
            if line is None:
                self.fail("engine exited unexpectedly")
            line = line.rstrip("\r\n")
            self.log.append(line)
            if "info string" in line and "invalid" in line:
                self.fail(f"engine rejected input: {line}")
            if pred(line):
                return line

    def ready(self):
        self.send("isready")
        self.until(lambda s: s == "readyok")

    def setopt(self, name, value):
        self.send(f"setoption name {name} value {value}")

    def close(self):
        """Normal exit: stop, quit, close stdin, wait up to 60 s. Returns the exit code or None if still running."""
        for cmd in ("stop", "quit"):
            try:
                self.send(cmd)
            except (OSError, ValueError):
                pass
        try:
            self.p.stdin.close()
        except (OSError, ValueError):
            pass
        try:
            return self.p.wait(60)
        except subprocess.TimeoutExpired:
            return None

    def fail(self, msg):
        rc = self.close()
        extra = "" if rc is not None else f"; engine pid {self.p.pid} did not exit and was left running (not killed)"
        raise SystemExit(msg + extra)

    def quit(self):
        return self.close()


def parse_opts(items):
    out = []
    for it in items:
        name, _, value = it.partition("=")
        if not name or not _:
            raise SystemExit(f"bad --opt {it!r}")
        out.append((name, value))
    return out


def arg(argv, name, default=None, many=False):
    vals = [argv[i + 1] for i, a in enumerate(argv) if a == name and i + 1 < len(argv)]
    if many:
        return vals
    return vals[-1] if vals else default


def cmd_uciopts(exe, argv):
    e = Engine(exe, 120)
    for n, v in parse_opts(arg(argv, "--opt", many=True)):
        e.setopt(n, v)
    e.send("uci")
    e.until(lambda s: s == "uciok")
    lines = [s for s in e.log if s.startswith("option name ")]
    rc = e.quit()
    return {"exe": exe, "options": lines, "count": len(lines), "exit": rc}


def bench_set(e, depths):
    res = {}
    for d in depths:
        e.send(f"bench {d}")
        line = e.until(lambda s: BENCH_RE.match(s) is not None)
        m = BENCH_RE.match(line)
        if int(m.group(1)) != d:
            raise SystemExit(f"bench depth mismatch: {line}")
        res[str(d)] = int(m.group(2))
    return res


def cmd_bench(exe, argv):
    depths = [int(x) for x in arg(argv, "--depths", "11,13,16,20,22").split(",")]
    nnue = arg(argv, "--nnue", "on")
    e = Engine(exe)
    e.send("uci")
    e.until(lambda s: s == "uciok")
    if nnue == "off":
        e.setopt("UseNNUE", "false")
    for n, v in parse_opts(arg(argv, "--opt", many=True)):
        e.setopt(n, v)
    e.ready()
    out = {"exe": exe, "nnue": nnue, "opts": arg(argv, "--opt", many=True), "sets": []}
    seq = arg(argv, "--opt-seq")
    groups = [g for g in seq.split(";")] if seq else [""]
    for g in groups:
        applied = [x for x in g.split(",") if x]
        for n, v in parse_opts(applied):
            e.setopt(n, v)
        e.ready()
        out["sets"].append({"applied": applied, "nodes": bench_set(e, depths)})
    out["exit"] = e.quit()
    return out


def cmd_perft(exe, argv):
    depth = int(arg(argv, "--depth", "5"))
    pos = arg(argv, "--pos", "startpos")
    e = Engine(exe)
    e.send("uci")
    e.until(lambda s: s == "uciok")
    e.send("position startpos" if pos == "startpos" else f"position fen {KIWIPETE}")
    e.ready()
    e.send(f"go perft {depth}")
    line = e.until(lambda s: s.startswith("nodes "))
    out = {"exe": exe, "pos": pos, "depth": depth, "nodes": int(line.split()[1])}
    out["exit"] = e.quit()
    return out


def read_fens(path, limit):
    fens = [x.strip() for x in open(path, encoding="ascii").read().splitlines() if x.strip()]
    return fens[:limit] if limit else fens


def cmd_fens(exe, argv, warm=False):
    fens = read_fens(arg(argv, "--fens"), int(arg(argv, "--limit", "0")))
    depth = int(arg(argv, "--depth", "13"))
    nodes = int(arg(argv, "--nodes", "20000"))
    nnue = arg(argv, "--nnue", "on")
    outp = arg(argv, "--out")
    e = Engine(exe)
    e.send("uci")
    e.until(lambda s: s == "uciok")
    e.setopt("OwnBook", "false")
    e.setopt("Threads", "1")
    e.setopt("Hash", "16")
    if nnue == "off":
        e.setopt("UseNNUE", "false")
    for n, v in parse_opts(arg(argv, "--opt", many=True)):
        e.setopt(n, v)
    e.ready()
    if warm:
        e.send("ucinewgame")
        e.ready()
    rows = []
    t0 = time.time()
    for i, fen in enumerate(fens):
        if not warm:
            e.send("ucinewgame")
            e.ready()
        e.send(f"position fen {fen}")
        e.send(f"go nodes {nodes}" if warm else f"go depth {depth}")
        last = None
        while True:
            line = e.until(lambda s: s.startswith("info depth ") or s.startswith("bestmove "))
            if line.startswith("bestmove "):
                best = line.split()[1]
                break
            if INFO_RE.match(line):
                last = line
        m = INFO_RE.match(last) if last else None
        if not m:
            raise SystemExit(f"no info line for fen {i}")
        rows.append((i, int(m.group(1)), m.group(2), int(m.group(3)), best))
        e.log.clear()
    rc = e.quit()
    with open(outp, "x", encoding="ascii", newline="\n") as f:
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")
    return {"exe": exe, "mode": "warm" if warm else "cold", "nnue": nnue, "count": len(rows),
            "depth": None if warm else depth, "nodes_per_move": nodes if warm else None,
            "total_nodes": sum(r[3] for r in rows), "seconds": round(time.time() - t0, 1), "out": outp, "exit": rc}


def main(argv):
    if len(argv) < 3:
        raise SystemExit(__doc__)
    place_self()
    cmd, exe = argv[1], argv[2]
    fn = {"uciopts": cmd_uciopts, "bench": cmd_bench, "perft": cmd_perft, "fens": cmd_fens,
          "warm": lambda x, a: cmd_fens(x, a, warm=True)}.get(cmd)
    if fn is None:
        raise SystemExit(__doc__)
    print(json.dumps(fn(exe, argv[3:]), indent=1))


if __name__ == "__main__":
    main(sys.argv)
