#!/usr/bin/env python3
"""One O run: S14, Threads 1, Hash 16, optional switch, depth 12 on first200.fens.

Raw engine stdout goes to <stem>.txt. Options and the exe identity go to <stem>.meta.
"""
import hashlib
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

OUT = Path(__file__).resolve().parent
FENS = Path.home() / "first200.fens"
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")
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


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Engine:
    def __init__(self, exe):
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        self.q = queue.Queue()
        self.lines = []

        def reader():
            while True:
                raw = self.proc.stdout.readline()
                if not raw:
                    self.q.put(None)
                    return
                self.q.put(raw.decode("utf-8", "replace"))

        self.thread = threading.Thread(target=reader, daemon=True)
        self.thread.start()

    def send(self, line):
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def read_until(self, pred, timeout):
        end = time.time() + timeout
        while time.time() < end:
            try:
                line = self.q.get(timeout=max(0.05, min(1.0, end - time.time())))
            except queue.Empty:
                continue
            if line is None:
                raise SystemExit("STOP: engine closed stdout")
            self.lines.append(line)
            for bad in BAD:
                if bad in line:
                    raise SystemExit(f"STOP: {line.rstrip()}")
            if pred(line):
                return
        tail = self.lines[-1].rstrip() if self.lines else "no output"
        raise SystemExit(f"STOP: timeout, last line: {tail}")

    def close(self):
        try:
            self.send("quit")
        except BrokenPipeError:
            pass
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def id_name(lines):
    for line in lines:
        if line.startswith("id name "):
            return line[len("id name "):].rstrip("\n")
    return ""


def main():
    if len(sys.argv) != 4:
        sys.exit("usage: o_run.py <exe> <stem> <switch|none>")
    exe = str(Path(sys.argv[1]).resolve())
    stem = sys.argv[2]
    switch = sys.argv[3]
    options = list(S14)
    if switch != "none":
        name, value = switch.split("=", 1)
        if value not in ("true", "false"):
            sys.exit("switch value must be true or false")
        options.append((name, value))
    sent = [f"setoption name {name} value {value}" for name, value in options]
    fens = [line.strip() for line in FENS.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(fens) != 200:
        sys.exit(f"STOP: expected 200 fens, got {len(fens)}")
    eng = Engine(exe)
    try:
        eng.send("uci")
        eng.read_until(lambda line: line.startswith("uciok"), 30)
        for line in sent:
            eng.send(line)
            eng.send("isready")
            eng.read_until(lambda got: got.startswith("readyok"), 30)
        for index, fen in enumerate(fens, 1):
            eng.send("ucinewgame")
            eng.send("isready")
            eng.read_until(lambda got: got.startswith("readyok"), 30)
            eng.send(f"position fen {fen}")
            eng.send("isready")
            eng.read_until(lambda got: got.startswith("readyok"), 30)
            eng.send("go depth 12")
            eng.read_until(lambda got: got.startswith("bestmove"), 180)
            if index % 50 == 0:
                print(f"{stem} {index}/200", flush=True)
    finally:
        text = "".join(eng.lines)
        (OUT / f"{stem}.txt").write_text(text, encoding="utf-8")
        meta = (
            f"exe: {exe}\n"
            f"sha256: {sha256_file(exe)}\n"
            f"id_name: {id_name(eng.lines)}\n"
            f"fens: {FENS}\n"
            f"fens_sha256: {sha256_file(FENS)}\n"
            "options:\n"
            + "".join(line + "\n" for line in sent)
        )
        (OUT / f"{stem}.meta").write_text(meta, encoding="utf-8")
        eng.close()
    print(f"wrote {stem}", flush=True)


if __name__ == "__main__":
    main()
