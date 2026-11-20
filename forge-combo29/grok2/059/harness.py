#!/usr/bin/env python3
"""STEP 2 harness for seat 059 arm 9. Write this file, then run it.
  python3 harness.py honesty <exe> <out_prefix>
  python3 harness.py orun <exe> <raw_path> <switch: none|false|true> <fens>
A fresh process is used for every honesty line. No setoption is sent on those
processes. orun sends S14, Threads 1, Hash 16, then the switch when named,
and isready after every setoption and every position. Stops on unknown option,
invalid value, invalid FEN, or illegal move.
"""
import hashlib
import queue
import subprocess
import sys
import threading

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
SWITCH = "IdeaS13"


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
        self.q = queue.Queue()
        self.lines = []

        def reader():
            for line in self.proc.stdout:
                self.q.put(line.rstrip("\r\n"))
            self.q.put(None)

        threading.Thread(target=reader, daemon=True).start()

    def send(self, cmd):
        if self.proc.poll() is not None:
            raise SystemExit(f"STOP: engine already exited before {cmd}")
        self.proc.stdin.write(cmd + "\n")
        self.proc.stdin.flush()

    def read_until(self, pred, timeout):
        import time

        end = time.time() + timeout
        while time.time() < end:
            try:
                line = self.q.get(timeout=0.5)
            except queue.Empty:
                if self.proc.poll() is not None:
                    raise SystemExit("STOP: engine exited while waiting")
                continue
            if line is None:
                raise SystemExit("STOP: engine closed stdout")
            self.lines.append(line)
            for marker in STOP_MARKERS:
                if marker in line:
                    raise SystemExit(f"STOP: {line}")
            if pred(line):
                return line
        raise SystemExit("STOP: timeout waiting for engine")

    def close(self):
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def id_name(exe):
    eng = Engine(exe)
    try:
        eng.send("uci")
        eng.read_until(lambda line: line.strip() == "uciok", 30)
    finally:
        eng.close()
    for line in eng.lines:
        if line.startswith("id name "):
            return line[len("id name "):]
    raise SystemExit("STOP: no id name")


def write_meta(path, exe, digest, name, options):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"exe: {exe}\n")
        f.write(f"sha256: {digest}\n")
        f.write(f"id name: {name}\n")
        f.write("options:\n")
        if not options:
            f.write("(none)\n")
        for opt in options:
            f.write(opt + "\n")


def run_honesty_one(exe, command, out_path, name, digest):
    eng = Engine(exe)
    try:
        eng.send(command)
        if command.startswith("bench"):
            eng.read_until(lambda line: line.startswith("info string bench "), 300)
        else:
            eng.read_until(lambda line: line.startswith("nodes "), 300)
        eng.send("quit")
        eng.proc.wait(timeout=30)
    finally:
        text = "\n".join(eng.lines) + ("\n" if eng.lines else "")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        write_meta(out_path + ".meta", exe, digest, name, [])
    print(f"{out_path}: {eng.lines[-1] if eng.lines else 'EMPTY'}", flush=True)


def honesty(exe, prefix):
    digest = sha256_file(exe)
    name = id_name(exe)
    jobs = [
        ("bench 11", f"{prefix}_bench11.txt"),
        ("bench 13", f"{prefix}_bench13.txt"),
        ("bench 16", f"{prefix}_bench16.txt"),
        ("go perft 5", f"{prefix}_perft5.txt"),
    ]
    # One fresh process per line. Run them one after another so a failure
    # is tied to a single command. Four short searches fit in one call.
    for command, out_path in jobs:
        run_honesty_one(exe, command, out_path, name, digest)


def orun(exe, raw_path, switch, fens_path):
    if switch not in ("none", "false", "true"):
        raise SystemExit("switch must be none, false, or true")
    digest = sha256_file(exe)
    name = id_name(exe)
    options = [f"setoption name {opt} value {val}" for opt, val in S14]
    if switch != "none":
        options.append(f"setoption name {SWITCH} value {switch}")
    fens = [line.strip() for line in open(fens_path, encoding="utf-8") if line.strip()]
    eng = Engine(exe)
    try:
        eng.send("uci")
        eng.read_until(lambda line: line.strip() == "uciok", 30)
        for opt in options:
            eng.send(opt)
            eng.send("isready")
            eng.read_until(lambda line: line.strip() == "readyok", 30)
        for index, fen in enumerate(fens, start=1):
            eng.send("ucinewgame")
            eng.send("isready")
            eng.read_until(lambda line: line.strip() == "readyok", 30)
            eng.send(f"position fen {fen}")
            eng.send("isready")
            eng.read_until(lambda line: line.strip() == "readyok", 30)
            eng.send("go depth 12")
            eng.read_until(lambda line: line.startswith("bestmove "), 180)
            if index % 25 == 0 or index == len(fens):
                print(f"{raw_path}: {index}/{len(fens)}", file=sys.stderr, flush=True)
        eng.send("quit")
        eng.proc.wait(timeout=30)
    finally:
        text = "\n".join(eng.lines) + ("\n" if eng.lines else "")
        with open(raw_path, "w", encoding="utf-8") as f:
            f.write(text)
        write_meta(raw_path + ".meta", exe, digest, name, options)
    print(f"wrote {raw_path} lines {len(eng.lines)}", flush=True)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    mode = sys.argv[1]
    if mode == "honesty":
        honesty(sys.argv[2], sys.argv[3])
    elif mode == "orun":
        orun(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
