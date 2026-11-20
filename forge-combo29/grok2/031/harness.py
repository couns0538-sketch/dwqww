#!/usr/bin/env python3
"""UCI harness for Grok swarm 2 measurements.

A fresh process for each honesty line. No setoption on honesty.
O-runs send Threads, Hash, then S14, then the switch (or none), and
isready after every setoption and every position.

  python3 harness.py honesty EXE OUTDIR PREFIX
  python3 harness.py orun EXE FENS OUT META SWITCH
SWITCH is "none", or "Name=true", or "Name=false".
"""
import hashlib
import select
import subprocess
import sys

STOPS = ("unknown option", "invalid value", "invalid FEN", "illegal move")
S14 = [
    "setoption name LmrQuietBase value 93",
    "setoption name LmrQuietDivisor value 205",
    "setoption name LmrNoisyBase value 13",
    "setoption name LmrNoisyDivisor value 333",
    "setoption name LmrHistoryDivisor value 5643",
    "setoption name NullMoveBase value 5",
    "setoption name LmpBase value 8",
    "setoption name HistoryPruneMultiplier value 2220",
    "setoption name HistoryBonusQuadratic value 24",
    "setoption name HistoryBonusLinear value 54",
    "setoption name HistoryBonusMax value 2212",
    "setoption name SingularDepth value 6",
    "setoption name IirDepth value 2",
    "setoption name NonPawnCorrection value true",
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Engine:
    def __init__(self, exe, log):
        self.exe = exe
        self.log = log
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        self.id_name = ""

    def send(self, cmd):
        self.log.write(">> " + cmd + "\n")
        self.log.flush()
        self.proc.stdin.write((cmd + "\n").encode())
        self.proc.stdin.flush()

    def read_until(self, kind, timeout):
        lines = []
        while True:
            ready, _, _ = select.select([self.proc.stdout], [], [], timeout)
            if not ready:
                self.proc.kill()
                raise SystemExit(f"STOP: timeout waiting for {kind}")
            raw = self.proc.stdout.readline()
            if raw == b"":
                self.proc.kill()
                raise SystemExit(f"STOP: engine closed stdout waiting for {kind}")
            line = raw.decode("utf-8", "replace").rstrip("\r\n")
            self.log.write(line + "\n")
            self.log.flush()
            for stop in STOPS:
                if stop in line:
                    self.proc.kill()
                    raise SystemExit(f"STOP: {line}")
            if line.startswith("id name "):
                self.id_name = line[len("id name "):]
            lines.append(line)
            if kind == "uciok" and line == "uciok":
                return lines
            if kind == "readyok" and line == "readyok":
                return lines
            if kind == "bestmove" and line.startswith("bestmove "):
                return lines
            if kind == "bench" and line.startswith("info string bench depth "):
                return lines
            if kind == "perft" and line.startswith("nodes "):
                return lines

    def close(self):
        try:
            self.send("quit")
        except BrokenPipeError:
            pass
        try:
            self.proc.stdin.close()
        except Exception:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def write_meta(path, exe, digest, id_name, options):
    with open(path, "w", encoding="utf-8") as m:
        m.write(f"exe: {exe}\n")
        m.write(f"sha256: {digest}\n")
        m.write(f"id name: {id_name}\n")
        m.write("options:\n")
        if not options:
            m.write("(none)\n")
        else:
            for opt in options:
                m.write(opt + "\n")


def handshake(eng):
    eng.send("uci")
    eng.read_until("uciok", 60)
    eng.send("isready")
    eng.read_until("readyok", 60)


def honesty(exe, outdir, prefix):
    digest = sha256_file(exe)
    jobs = [
        ("bench11", "bench 11", "bench"),
        ("bench13", "bench 13", "bench"),
        ("bench16", "bench 16", "bench"),
        ("perft5", "go perft 5", "perft"),
    ]
    for tag, cmd, kind in jobs:
        out = f"{outdir}/{prefix}_{tag}.txt"
        meta = f"{outdir}/{prefix}_{tag}.meta"
        with open(out, "w", encoding="utf-8") as log:
            eng = Engine(exe, log)
            handshake(eng)
            eng.send(cmd)
            eng.read_until(kind, 300)
            id_name = eng.id_name
            eng.close()
        write_meta(meta, exe, digest, id_name, [])
        print(f"honesty {prefix} {tag} wrote {out}")


def orun(exe, fens_path, out_path, meta_path, switch):
    digest = sha256_file(exe)
    options = [
        "setoption name Threads value 1",
        "setoption name Hash value 16",
    ] + list(S14)
    if switch != "none":
        name, value = switch.split("=", 1)
        if value not in ("true", "false"):
            raise SystemExit(f"STOP: switch value must be true or false, got {value}")
        options.append(f"setoption name {name} value {value}")
    with open(fens_path, encoding="utf-8") as f:
        fens = [ln.strip() for ln in f if ln.strip()]
    with open(out_path, "w", encoding="utf-8") as log:
        eng = Engine(exe, log)
        handshake(eng)
        for opt in options:
            eng.send(opt)
            eng.send("isready")
            eng.read_until("readyok", 60)
        for i, fen in enumerate(fens, 1):
            eng.send("ucinewgame")
            eng.send("isready")
            eng.read_until("readyok", 60)
            eng.send("position fen " + fen)
            eng.send("isready")
            eng.read_until("readyok", 60)
            eng.send("go depth 12")
            eng.read_until("bestmove", 180)
            if i % 50 == 0:
                print(f"{out_path} position {i}", flush=True)
        id_name = eng.id_name
        eng.close()
    write_meta(meta_path, exe, digest, id_name, options)
    print(f"orun wrote {out_path} positions {len(fens)}")


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    mode = sys.argv[1]
    if mode == "honesty":
        honesty(sys.argv[2], sys.argv[3], sys.argv[4])
    elif mode == "orun":
        orun(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
