#!/usr/bin/env python3
"""O run: S14, Threads 1, Hash 16, ucinewgame+isready, go depth 12."""
import hashlib
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

OUT = Path(__file__).resolve().parent
FENS = Path.home() / "first200.fens"
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
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Engine:
    def __init__(self, exe):
        self.exe = exe
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.lines = []
        self.q = queue.Queue()

        def reader():
            try:
                for raw in self.proc.stdout:
                    self.q.put(raw)
            finally:
                self.q.put(None)

        threading.Thread(target=reader, daemon=True).start()

    def send(self, text):
        self.proc.stdin.write(text + "\n")
        self.proc.stdin.flush()

    def readline(self, seconds):
        try:
            raw = self.q.get(timeout=seconds)
        except queue.Empty:
            self.proc.kill()
            raise SystemExit("STOP timeout")
        if raw is None:
            self.proc.kill()
            raise SystemExit("STOP eof")
        line = raw.rstrip("\r\n")
        self.lines.append(line)
        if any(b in line for b in BAD):
            self.proc.kill()
            raise SystemExit("STOP " + line)
        return line

    def read_until(self, pred, seconds):
        deadline = time.time() + seconds
        while True:
            line = self.readline(max(0.1, deadline - time.time()))
            if pred(line):
                return line

    def close(self):
        try:
            self.send("quit")
            self.proc.stdin.close()
        except Exception:
            pass
        deadline = time.time() + 15
        while time.time() < deadline:
            try:
                raw = self.q.get(timeout=0.5)
            except queue.Empty:
                if self.proc.poll() is not None:
                    break
                continue
            if raw is None:
                break
            self.lines.append(raw.rstrip("\r\n"))
        if self.proc.poll() is None:
            self.proc.wait(timeout=15)


def main():
    if len(sys.argv) != 4:
        sys.exit("usage: o_run.py <label> <exe> <switch:none|false|true>")
    label, exe, switch = sys.argv[1], sys.argv[2], sys.argv[3]
    if switch not in ("none", "false", "true"):
        sys.exit("switch must be none, false, or true")
    fens = [ln.strip() for ln in FENS.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if len(fens) != 200:
        sys.exit(f"STOP expected 200 fens, got {len(fens)}")
    options = [
        "setoption name Threads value 1",
        "setoption name Hash value 16",
        *S14,
    ]
    if switch != "none":
        options.append(f"setoption name IdeaB8 value {switch}")
    eng = Engine(exe)
    try:
        eng.send("uci")
        eng.read_until(lambda line: line == "uciok", 30)
        for opt in options:
            eng.send(opt)
            eng.send("isready")
            eng.read_until(lambda line: line == "readyok", 30)
        for i, fen in enumerate(fens, start=1):
            eng.send("ucinewgame")
            eng.send("isready")
            eng.read_until(lambda line: line == "readyok", 30)
            eng.send("position fen " + fen)
            eng.send("isready")
            eng.read_until(lambda line: line == "readyok", 30)
            eng.send("go depth 12")
            eng.read_until(lambda line: line.startswith("bestmove "), 180)
            if i % 25 == 0:
                print(f"{label} {i}/200", file=sys.stderr, flush=True)
    finally:
        if eng.proc.poll() is None:
            eng.close()
    out = OUT / f"o_{label}.txt"
    meta = OUT / f"o_{label}.meta"
    out.write_text("\n".join(eng.lines) + "\n", encoding="utf-8")
    id_name = ""
    for line in eng.lines:
        if line.startswith("id name "):
            id_name = line[len("id name "):]
            break
    body = [
        f"exe: {exe}",
        f"sha256: {sha256(exe)}",
        f"id_name: {id_name}",
        "options_sent:",
        *options,
        "",
    ]
    meta.write_text("\n".join(body), encoding="utf-8")
    print(f"wrote {out.name} lines {len(eng.lines)}", flush=True)


if __name__ == "__main__":
    main()
