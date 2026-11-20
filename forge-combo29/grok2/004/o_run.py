#!/usr/bin/env python3
"""Depth-12 node count over first200.fens with S14, Threads 1, Hash 16.

Usage: python3 o_run.py <exe> <fens> <outdir> <tag> [SwitchName true|false]
Sends ucinewgame and isready before every position. Stops on a refused option,
an invalid FEN, or an illegal move. One row per position: number and the nodes
of the last info line before bestmove.
"""
import hashlib
import queue
import subprocess
import sys
import threading
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
    ("Threads", "1"),
    ("Hash", "16"),
]


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
        self.raw = []
        self.id_name = ""
        self.lines = queue.Queue()
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self.lines.put(line)
        self.lines.put(None)

    def send(self, line):
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, pred, timeout):
        while True:
            try:
                line = self.lines.get(timeout=timeout)
            except queue.Empty:
                raise SystemExit(f"STOP: timeout after {timeout}s")
            if line is None:
                raise SystemExit(f"STOP: engine exited {self.proc.poll()}")
            self.raw.append(line)
            for mark in STOP_MARKS:
                if mark in line:
                    raise SystemExit(f"STOP: {line.rstrip()}")
            if line.startswith("id name "):
                self.id_name = line[len("id name ") :].rstrip("\r\n")
            if pred(line):
                return line

    def close(self):
        try:
            self.send("quit")
        except OSError:
            pass
        try:
            self.proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def nodes_of(info_line):
    token = " nodes "
    start = info_line.rfind(token)
    if start < 0:
        raise SystemExit(f"STOP: info line has no nodes: {info_line.rstrip()}")
    rest = info_line[start + len(token) :].split()
    if not rest or not rest[0].isdigit():
        raise SystemExit(f"STOP: nodes field missing: {info_line.rstrip()}")
    return int(rest[0])


def main():
    if len(sys.argv) not in (5, 7):
        raise SystemExit("usage: o_run.py <exe> <fens> <outdir> <tag> [SwitchName true|false]")
    exe = sys.argv[1]
    fens = Path(sys.argv[2]).read_text(encoding="utf-8").splitlines()
    fens = [line.strip() for line in fens if line.strip()]
    outdir = Path(sys.argv[3])
    tag = sys.argv[4]
    switch = None
    if len(sys.argv) == 7:
        switch = (sys.argv[5], sys.argv[6])
        if switch[1] not in ("true", "false"):
            raise SystemExit("STOP: switch value must be true or false")
    outdir.mkdir(parents=True, exist_ok=True)
    options = list(S14)
    if switch is not None:
        options.append(switch)
    option_lines = [f"setoption name {name} value {value}" for name, value in options]

    engine = Engine(exe)
    rows = []
    try:
        engine.send("uci")
        engine.read_until(lambda line: line.startswith("uciok"), 30)
        for line in option_lines:
            engine.send(line)
            engine.send("isready")
            engine.read_until(lambda ready: ready.startswith("readyok"), 30)
        for index, fen in enumerate(fens, start=1):
            engine.send("ucinewgame")
            engine.send("isready")
            engine.read_until(lambda ready: ready.startswith("readyok"), 30)
            engine.send(f"position fen {fen}")
            engine.send("isready")
            engine.read_until(lambda ready: ready.startswith("readyok"), 30)
            engine.send("go depth 12")
            last_info = None
            while True:
                line = engine.read_until(lambda text: text.startswith("info ") or text.startswith("bestmove "), 120)
                if line.startswith("bestmove "):
                    break
                last_info = line
            if last_info is None:
                raise SystemExit(f"STOP: no info line before bestmove at position {index}")
            rows.append(f"{index} {nodes_of(last_info)}")
            if index % 25 == 0:
                print(f"{tag} {index}/{len(fens)}", flush=True)
    finally:
        engine.close()
        (outdir / f"{tag}.raw").write_text("".join(engine.raw), encoding="utf-8")
        (outdir / f"{tag}.rows").write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")
        meta = [
            f"exe={engine.exe}",
            f"sha256={sha256_file(engine.exe)}",
            f"id_name={engine.id_name}",
            f"positions={len(rows)}",
        ]
        meta.extend(f"option={line}" for line in option_lines)
        (outdir / f"{tag}.meta").write_text("\n".join(meta) + "\n", encoding="utf-8")
    print(f"{tag} done {len(rows)}")


if __name__ == "__main__":
    main()
