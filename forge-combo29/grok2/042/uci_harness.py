#!/usr/bin/env python3
"""uci_harness.py (seat 042). One engine session, written before it is run.

  python3 uci_harness.py honesty <exe> <out> <meta> bench <depth>
  python3 uci_harness.py honesty <exe> <out> <meta> perft <depth>
  python3 uci_harness.py orun <exe> <fens> <out> <meta> [SwitchName true|false]

Honesty: a fresh process, uci (for id name) then the one command, no setoption.
O-run: S14 in the brief's order, then Threads 1, Hash 16, then the switch if
given. ucinewgame + isready before every position. isready after every
setoption and every position. Stops on unknown option, invalid value,
invalid FEN, illegal move.
"""
import hashlib
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

STOP_MARKERS = ("unknown option", "invalid value", "invalid FEN", "illegal move")

S14 = [
    ("LmrQuietBase", "93"),
    ("LmrQuietDivisor", "205"),
    ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"),
    ("LmrHistoryDivisor", "5643"),
    ("NullMoveBase", "5"),
    ("LmpBase", "8"),
    ("HistoryPruneMultiplier", "2220"),
    ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"),
    ("HistoryBonusMax", "2212"),
    ("SingularDepth", "6"),
    ("IirDepth", "2"),
    ("NonPawnCorrection", "true"),
    ("Threads", "1"),
    ("Hash", "16"),
]


class Stop(Exception):
    pass


class Engine:
    def __init__(self, exe):
        self.exe = str(Path(exe).resolve())
        self.proc = subprocess.Popen(
            [self.exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.lines = []
        self.q = queue.Queue()

        def reader():
            assert self.proc.stdout is not None
            for line in self.proc.stdout:
                self.q.put(line.rstrip("\r\n"))
            self.q.put(None)

        self.thread = threading.Thread(target=reader, daemon=True)
        self.thread.start()

    def send(self, line):
        if self.proc.stdin is None:
            raise Stop("stdin closed")
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, done, timeout):
        end = time.monotonic() + timeout
        while True:
            remaining = end - time.monotonic()
            if remaining <= 0:
                raise Stop(f"timeout after {timeout}s, last={self.lines[-3:]}")
            try:
                line = self.q.get(timeout=remaining)
            except queue.Empty:
                raise Stop(f"timeout after {timeout}s, last={self.lines[-3:]}")
            if line is None:
                raise Stop(f"engine exited, last={self.lines[-5:]}")
            self.lines.append(line)
            for marker in STOP_MARKERS:
                if marker in line:
                    raise Stop(line)
            if done(line):
                return line

    def close(self):
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=5)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_meta(path, exe, id_name, options):
    text = [
        f"exe: {exe}",
        f"sha256: {sha256_file(exe)}",
        f"id name: {id_name}",
        "options:",
    ]
    if options:
        text.extend(options)
    else:
        text.append("(none)")
    Path(path).write_text("\n".join(text) + "\n", encoding="utf-8")


def handshake(eng):
    eng.send("uci")
    id_name = ""

    def on_line(line):
        nonlocal id_name
        if line.startswith("id name "):
            id_name = line[len("id name "):]
        return line == "uciok"

    eng.read_until(on_line, 60)
    if not id_name:
        raise Stop("no id name before uciok")
    return id_name


def setoption(eng, name, value):
    line = f"setoption name {name} value {value}"
    eng.send(line)
    eng.send("isready")
    eng.read_until(lambda s: s == "readyok", 60)
    return line


def main():
    argv = sys.argv[1:]
    if not argv:
        sys.exit(__doc__)
    mode = argv[0]
    try:
        if mode == "honesty":
            _, exe, out, meta, kind, depth = argv
            eng = Engine(exe)
            id_name = handshake(eng)
            if kind == "bench":
                eng.send(f"bench {depth}")
                eng.read_until(lambda s: s.startswith("info string bench depth "), 180)
            elif kind == "perft":
                eng.send(f"go perft {depth}")
                eng.read_until(lambda s: s.startswith("nodes "), 180)
            else:
                raise Stop(f"bad honesty kind {kind}")
            write_meta(meta, eng.exe, id_name, [])
        elif mode == "orun":
            exe, fens, out, meta = argv[1:5]
            switch = argv[5:]
            if len(switch) not in (0, 2):
                raise Stop("switch needs Name and true|false, or nothing")
            if len(switch) == 2 and switch[1] not in ("true", "false"):
                raise Stop("switch value must be true or false")
            eng = Engine(exe)
            id_name = handshake(eng)
            sent = []
            for name, value in S14:
                sent.append(setoption(eng, name, value))
            if len(switch) == 2:
                sent.append(setoption(eng, switch[0], switch[1]))
            fens_path = Path(fens)
            positions = [ln.strip() for ln in fens_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
            if len(positions) != 200:
                raise Stop(f"expected 200 fens, got {len(positions)}")
            for fen in positions:
                eng.send("ucinewgame")
                eng.send("isready")
                eng.read_until(lambda s: s == "readyok", 60)
                eng.send(f"position fen {fen}")
                eng.send("isready")
                eng.read_until(lambda s: s == "readyok", 60)
                eng.send("go depth 12")
                eng.read_until(lambda s: s.startswith("bestmove "), 180)
            write_meta(meta, eng.exe, id_name, sent)
        else:
            raise Stop(f"bad mode {mode}")
        Path(out).write_text("\n".join(eng.lines) + "\n", encoding="utf-8")
        eng.close()
        print(f"wrote {out} lines {len(eng.lines)}")
    except Stop as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        if "eng" in locals() and getattr(eng, "lines", None):
            Path(out).write_text("\n".join(eng.lines) + "\n", encoding="utf-8")
            eng.close()
        sys.exit(1)


if __name__ == "__main__":
    main()
