#!/usr/bin/env python3
"""harness.py (seat 066, arm 6, Grok 4.7).

  python3 harness.py honesty EXE OUTDIR TAG
      Fresh process per line. No setoption.
      bench 11, bench 13, bench 16, go perft 5.
      Writes OUTDIR/TAG_<name>.txt and OUTDIR/TAG_<name>.meta

  python3 harness.py orun EXE FENS OUTSTEM MODE
      MODE is none | false | true.
      none: do not send IdeaS32 (exe B).
      false / true: setoption name IdeaS32 value false|true.
      S14, then Threads 1, Hash 16, then the switch when MODE is not none.
      ucinewgame + isready before every position, then position fen, isready, go depth 12.
      Writes OUTSTEM.txt (engine stdout only) and OUTSTEM.meta.
"""
import hashlib
import os
import queue
import re
import subprocess
import sys
import threading

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
]
STOP_BITS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, path):
        self.path = path
        self.proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        self.out = []
        self.lines = queue.Queue()
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        stream = self.proc.stdout
        if stream is None:
            self.lines.put(None)
            return
        for raw in iter(stream.readline, b""):
            self.lines.put(raw.decode("utf-8", "replace").rstrip("\r\n"))
        self.lines.put(None)

    def send(self, line):
        if self.proc.stdin is None:
            raise RuntimeError("stdin closed")
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def readline(self, timeout):
        try:
            line = self.lines.get(timeout=timeout)
        except queue.Empty:
            raise TimeoutError(f"no output within {timeout}s from {self.path}; have {len(self.out)} lines")
        if line is None:
            raise EOFError(f"engine closed stdout, last lines: {self.out[-5:]}")
        self.out.append(line)
        for bit in STOP_BITS:
            if bit in line:
                raise RuntimeError(f"STOP: {line}")
        return line

    def read_until(self, pred, timeout):
        while True:
            line = self.readline(timeout)
            if pred(line):
                return line

    def quit(self):
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


def id_name(path):
    eng = Engine(path)
    try:
        eng.send("uci")
        eng.read_until(lambda line: line == "uciok", 60)
    finally:
        eng.quit()
    for line in eng.out:
        if line.startswith("id name "):
            return line[len("id name "):]
    raise RuntimeError(f"no id name from {path}: {eng.out[:8]}")


def write_meta(path, exe, digest, name, options, extra):
    lines = [
        f"exe={exe}",
        f"sha256={digest}",
        f"id_name={name}",
        "options_sent:",
    ]
    if options:
        lines.extend(options)
    else:
        lines.append("(none)")
    for key, value in extra:
        lines.append(f"{key}={value}")
    text = "\n".join(lines) + "\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def honesty(exe, outdir, tag):
    os.makedirs(outdir, exist_ok=True)
    digest = sha256_file(exe)
    name = id_name(exe)
    jobs = [
        ("bench11", "bench 11", lambda line: line.startswith("info string bench depth ")),
        ("bench13", "bench 13", lambda line: line.startswith("info string bench depth ")),
        ("bench16", "bench 16", lambda line: line.startswith("info string bench depth ")),
        ("perft5", "go perft 5", lambda line: bool(re.fullmatch(r"nodes \d+", line))),
    ]
    for stem, command, pred in jobs:
        eng = Engine(exe)
        try:
            eng.send(command)
            eng.read_until(pred, 180)
        finally:
            eng.quit()
        raw = os.path.join(outdir, f"{tag}_{stem}.txt")
        meta = os.path.join(outdir, f"{tag}_{stem}.meta")
        with open(raw, "w", encoding="utf-8") as f:
            f.write("\n".join(eng.out) + "\n")
        write_meta(meta, os.path.abspath(exe), digest, name, [], [("command", command), ("tag", tag)])
        print(f"wrote {raw} lines={len(eng.out)} last={eng.out[-1] if eng.out else ''}")


def option_lines(mode):
    lines = [f"setoption name {name} value {value}" for name, value in S14]
    lines.append("setoption name Threads value 1")
    lines.append("setoption name Hash value 16")
    if mode == "false":
        lines.append("setoption name IdeaS32 value false")
    elif mode == "true":
        lines.append("setoption name IdeaS32 value true")
    elif mode != "none":
        raise SystemExit(f"MODE must be none, false, or true, got {mode}")
    return lines


def orun(exe, fens_path, outstem, mode):
    with open(fens_path, encoding="utf-8") as f:
        fens = [line.strip() for line in f if line.strip()]
    if len(fens) != 200:
        raise SystemExit(f"expected 200 fens, got {len(fens)} in {fens_path}")
    digest = sha256_file(exe)
    name = id_name(exe)
    sent = option_lines(mode)
    eng = Engine(exe)
    try:
        eng.send("uci")
        eng.read_until(lambda line: line == "uciok", 60)
        for line in sent:
            eng.send(line)
            eng.send("isready")
            eng.read_until(lambda got: got == "readyok", 120)
        for index, fen in enumerate(fens, start=1):
            eng.send("ucinewgame")
            eng.send("isready")
            eng.read_until(lambda got: got == "readyok", 120)
            eng.send(f"position fen {fen}")
            eng.send("isready")
            eng.read_until(lambda got: got == "readyok", 120)
            eng.send("go depth 12")
            eng.read_until(lambda got: got.startswith("bestmove "), 180)
            if index % 25 == 0:
                print(f"{outstem} {index}/200", flush=True)
    finally:
        eng.quit()
    with open(outstem + ".txt", "w", encoding="utf-8") as f:
        f.write("\n".join(eng.out) + "\n")
    write_meta(
        outstem + ".meta",
        os.path.abspath(exe),
        digest,
        name,
        sent,
        [("mode", mode), ("fens", os.path.abspath(fens_path)), ("positions", "200")],
    )
    print(f"wrote {outstem}.txt lines={len(eng.out)}")


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    cmd = sys.argv[1]
    if cmd == "honesty":
        honesty(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "orun":
        orun(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
