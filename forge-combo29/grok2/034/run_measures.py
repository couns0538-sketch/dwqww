#!/usr/bin/env python3
"""Honesty benches and the depth-12 O runs. Raw engine stdout plus a .meta file.

Honesty: one fresh process per command, uci handshake only, no setoption.
O: Threads 1, Hash 16, S14 in the brief's order, then the switch if given.
After every setoption and every position: isready, read through readyok.
Stops on unknown option, invalid value, invalid FEN, illegal move.
"""
import hashlib
import select
import subprocess
import sys
import time
from pathlib import Path

STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")

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


class StopMark(Exception):
    pass


class Engine:
    def __init__(self, exe):
        self.exe = str(Path(exe).resolve())
        self.proc = subprocess.Popen(
            [self.exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        self.buf = b""
        self.lines = []
        self.id_name = ""

    def _read_line(self, timeout):
        deadline = time.time() + timeout
        while b"\n" not in self.buf:
            remain = deadline - time.time()
            if remain <= 0:
                raise TimeoutError("engine timeout tail=" + repr(self.buf[-300:]))
            ready, _, _ = select.select([self.proc.stdout], [], [], min(remain, 1.0))
            if not ready:
                if self.proc.poll() is not None:
                    raise RuntimeError(
                        f"engine exited {self.proc.returncode} tail={self.buf!r}"
                    )
                continue
            chunk = os_read(self.proc.stdout)
            if chunk == b"":
                raise RuntimeError("engine stdout closed")
            self.buf += chunk
        raw, self.buf = self.buf.split(b"\n", 1)
        text = raw.decode("utf-8", "replace").rstrip("\r")
        self.lines.append(text)
        for mark in STOP_MARKS:
            if mark in text:
                raise StopMark(text)
        return text

    def send(self, cmd):
        self.proc.stdin.write((cmd + "\n").encode())
        self.proc.stdin.flush()

    def read_until(self, pred, timeout):
        while True:
            line = self._read_line(timeout)
            if pred(line):
                return line

    def quit(self):
        if self.proc.poll() is None:
            try:
                self.send("quit")
                self.proc.wait(timeout=10)
            except Exception:
                self.proc.kill()
                self.proc.wait(timeout=5)


def os_read(stream):
    return stream.read(4096)


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_meta(path, exe, id_name, options):
    lines = [
        f"exe {exe}",
        f"sha256 {sha256_file(exe)}",
        f"id name {id_name}",
    ]
    for option in options:
        lines.append(f"option {option}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def handshake(eng):
    eng.send("uci")
    while True:
        line = eng._read_line(60)
        if line.startswith("id name "):
            eng.id_name = line[len("id name ") :]
        if line == "uciok":
            break
    eng.send("isready")
    eng.read_until(lambda line: line == "readyok", 60)


def setoption(eng, name, value, sent):
    cmd = f"setoption name {name} value {value}"
    eng.send(cmd)
    sent.append(cmd)
    eng.send("isready")
    eng.read_until(lambda line: line == "readyok", 60)


def save(eng, out_dir, stem, options):
    out_dir = Path(out_dir)
    (out_dir / f"{stem}.txt").write_text("\n".join(eng.lines) + "\n", encoding="utf-8")
    write_meta(out_dir / f"{stem}.meta", eng.exe, eng.id_name, options)


def honesty(exe, out_dir, tag):
    commands = [
        ("bench11", "bench 11", lambda line: line.startswith("info string bench ")),
        ("bench13", "bench 13", lambda line: line.startswith("info string bench ")),
        ("bench16", "bench 16", lambda line: line.startswith("info string bench ")),
        ("perft5", "go perft 5", lambda line: line.startswith("nodes ")),
    ]
    for name, cmd, done in commands:
        eng = Engine(exe)
        try:
            handshake(eng)
            eng.send(cmd)
            eng.read_until(done, 300)
            print(f"honesty {tag} {name} ok", flush=True)
        finally:
            save(eng, out_dir, f"honesty_{tag}_{name}", [])
            eng.quit()


def o_run(exe, fens_path, out_dir, tag, switch, switch_value):
    fens = [line.strip() for line in open(fens_path, encoding="utf-8") if line.strip()]
    eng = Engine(exe)
    sent = []
    try:
        handshake(eng)
        setoption(eng, "Threads", "1", sent)
        setoption(eng, "Hash", "16", sent)
        for name, value in S14:
            setoption(eng, name, value, sent)
        if switch:
            setoption(eng, switch, switch_value, sent)
        for index, fen in enumerate(fens, 1):
            eng.send("ucinewgame")
            eng.send("isready")
            eng.read_until(lambda line: line == "readyok", 60)
            eng.send("position fen " + fen)
            eng.send("isready")
            eng.read_until(lambda line: line == "readyok", 60)
            eng.send("go depth 12")
            eng.read_until(lambda line: line.startswith("bestmove "), 180)
            if index % 25 == 0:
                print(f"{tag} {index}/{len(fens)}", flush=True)
        print(f"{tag} done {len(fens)}", flush=True)
    finally:
        save(eng, out_dir, f"o_{tag}", sent)
        eng.quit()


def main():
    mode = sys.argv[1]
    if mode == "honesty":
        honesty(sys.argv[2], sys.argv[3], sys.argv[4])
    elif mode == "o":
        switch = sys.argv[6] if len(sys.argv) > 6 else None
        value = sys.argv[7] if len(sys.argv) > 7 else None
        o_run(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], switch, value)
    else:
        sys.exit("usage: run_measures.py honesty|o ...")


if __name__ == "__main__":
    main()
