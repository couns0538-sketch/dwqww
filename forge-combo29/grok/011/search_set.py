#!/usr/bin/env python3
"""Measured fixed-depth searches. One engine process. isready after every setoption and position."""
import hashlib
import subprocess
import sys
import time
from pathlib import Path

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
    ("Hash", "16"),
    ("Threads", "1"),
]

STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def die(msg):
    print(msg, file=sys.stderr)
    raise SystemExit(2)


def fen_of(line):
    text = line.strip()
    if not text or text.startswith("#"):
        return None
    parts = text.split()
    if len(parts) < 4:
        die(f"STOP invalid FEN short line {text}")
    if len(parts) >= 6 and parts[1] in ("w", "b"):
        return " ".join(parts[:6])
    return " ".join(parts[:4])


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

    def send(self, line):
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, done, timeout):
        lines = []
        deadline = time.monotonic() + timeout
        while True:
            if time.monotonic() > deadline:
                die("STOP timeout waiting for engine")
            line = self.proc.stdout.readline()
            if line == "":
                die("STOP engine closed stdout")
            line = line.rstrip("\r\n")
            lines.append(line)
            for mark in STOP_MARKS:
                if mark in line:
                    die("STOP " + line)
            if done(line):
                return lines

    def close(self):
        try:
            self.send("quit")
        except BrokenPipeError:
            pass
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def nodes_at_depth(lines, depth):
    prefix = f"info depth {depth} "
    found = None
    for line in lines:
        if not line.startswith(prefix):
            continue
        parts = line.split()
        if "nodes" not in parts:
            continue
        found = int(parts[parts.index("nodes") + 1])
    return found


def main():
    if len(sys.argv) != 6:
        die("usage: search_set.py EXE OUTPREFIX FENFILE DEPTH SWITCH")
    exe, out_prefix, fen_file, depth_s, switch = sys.argv[1:]
    depth = int(depth_s)
    if switch not in ("none", "off", "on"):
        die("SWITCH must be none, off, or on")
    fens = []
    for line in Path(fen_file).read_text().splitlines():
        fen = fen_of(line)
        if fen is not None:
            fens.append(fen)
    if not fens:
        die("STOP no fens")
    exe_path = Path(exe).resolve()
    digest = hashlib.sha256(exe_path.read_bytes()).hexdigest()
    out_raw = Path(out_prefix + ".txt")
    out_meta = Path(out_prefix + ".meta")
    out_rows = Path(out_prefix + ".rows")
    engine = Engine(exe_path)
    raw = []
    rows = []
    id_name = ""
    option_lines = []
    try:
        engine.send("uci")
        hello = engine.read_until(lambda s: s == "uciok", 30)
        raw.extend(hello)
        for line in hello:
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
        for name, value in S14:
            command = f"setoption name {name} value {value}"
            option_lines.append(command)
            engine.send(command)
            engine.send("isready")
            ready = engine.read_until(lambda s: s == "readyok", 30)
            raw.append(">> " + command)
            raw.extend(ready)
        if switch != "none":
            value = "true" if switch == "on" else "false"
            command = f"setoption name IdeaS25 value {value}"
            option_lines.append(command)
            engine.send(command)
            engine.send("isready")
            ready = engine.read_until(lambda s: s == "readyok", 30)
            raw.append(">> " + command)
            raw.extend(ready)
        rows = []
        for index, fen in enumerate(fens):
            engine.send("ucinewgame")
            engine.send("isready")
            ready = engine.read_until(lambda s: s == "readyok", 30)
            raw.append(">> ucinewgame")
            raw.extend(ready)
            pos = f"position fen {fen}"
            engine.send(pos)
            engine.send("isready")
            ready = engine.read_until(lambda s: s == "readyok", 30)
            raw.append(">> " + pos)
            raw.extend(ready)
            go = f"go depth {depth}"
            engine.send(go)
            played = engine.read_until(lambda s: s.startswith("bestmove "), 180)
            raw.append(">> " + go)
            raw.extend(played)
            got = nodes_at_depth(played, depth)
            if got is None:
                die(f"STOP no depth {depth} nodes at index {index}")
            rows.append(got)
            if index < 3 or (index + 1) % 50 == 0 or index + 1 == len(fens):
                print(f"pos {index + 1}/{len(fens)} nodes {got} sum {sum(rows)}", flush=True)
    finally:
        engine.close()
        out_raw.write_text("\n".join(raw) + "\n")
        out_rows.write_text("\n".join(str(n) for n in rows) + "\n")
        meta = [
            f"exe {exe_path}",
            f"sha256 {digest}",
            f"id_name {id_name}",
            "options",
            *option_lines,
            f"depth {depth}",
            f"switch {switch}",
            f"fens {fen_file}",
            f"count {len(rows)}",
        ]
        out_meta.write_text("\n".join(meta) + "\n")
    print(f"SUM {sum(rows)} COUNT {len(rows)} FIRST {' '.join(str(n) for n in rows[:3])}")


if __name__ == "__main__":
    main()
