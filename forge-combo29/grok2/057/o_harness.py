#!/usr/bin/env python3
"""Depth-12 O-run harness. Usage: o_harness.py <exe> <none|false|true> <fens> <out_prefix>"""
import hashlib
import queue
import re
import subprocess
import sys
import threading
from pathlib import Path

STOP_MARKERS = ("unknown option", "invalid value", "invalid FEN", "illegal move")
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


def main():
    if len(sys.argv) != 5:
        sys.exit("usage: o_harness.py <exe> <none|false|true> <fens> <out_prefix>")
    exe, switch, fens_path, prefix = sys.argv[1:]
    if switch not in ("none", "false", "true"):
        sys.exit("switch must be none, false, or true")
    exe_path = str(Path(exe).resolve())
    sha = hashlib.sha256(Path(exe_path).read_bytes()).hexdigest()
    fens = [ln.strip() for ln in open(fens_path, encoding="utf-8") if ln.strip()]
    if len(fens) != 200:
        sys.exit(f"STOP expected 200 fens, got {len(fens)}")
    proc = subprocess.Popen(
        [exe_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    lines = queue.Queue()

    def reader():
        assert proc.stdout is not None
        for line in proc.stdout:
            lines.put(line)
        lines.put(None)

    threading.Thread(target=reader, daemon=True).start()
    raw = []
    id_name = ""

    def fail(msg):
        Path(prefix + "_raw.txt").write_text("\n".join(raw) + "\n", encoding="utf-8")
        proc.kill()
        sys.exit(msg)

    def send(line):
        raw.append(">> " + line)
        assert proc.stdin is not None
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def take(timeout):
        try:
            line = lines.get(timeout=timeout)
        except queue.Empty:
            fail(f"STOP timeout after {timeout}s")
        if line is None:
            fail("STOP engine closed stdout")
        line = line.rstrip("\r\n")
        raw.append(line)
        nonlocal_id(line)
        for marker in STOP_MARKERS:
            if marker in line:
                fail(f"STOP {line}")
        return line

    def nonlocal_id(line):
        nonlocal id_name
        if line.startswith("id name ") and not id_name:
            id_name = line[len("id name "):]

    def read_until(ok, timeout=180):
        while True:
            line = take(timeout)
            if line == ok or line.startswith(ok + " "):
                return line

    options = [
        "setoption name Threads value 1",
        "setoption name Hash value 16",
        *S14,
    ]
    if switch != "none":
        options.append(f"setoption name IdeaK4 value {switch}")

    send("uci")
    read_until("uciok")
    for opt in options:
        send(opt)
        send("isready")
        read_until("readyok")

    rows = []
    for i, fen in enumerate(fens, start=1):
        send("ucinewgame")
        send("isready")
        read_until("readyok")
        send("position fen " + fen)
        send("isready")
        read_until("readyok")
        send("go depth 12")
        last_info = ""
        while True:
            line = take(180)
            if line.startswith("info "):
                last_info = line
            if line.startswith("bestmove "):
                break
        match = re.search(r" nodes (\d+)", last_info)
        if not match:
            fail(f"STOP no nodes on last info of position {i}: {last_info}")
        nodes = int(match.group(1))
        rows.append(f"{i} {nodes}")
        if i <= 3 or i % 50 == 0:
            print(f"pos {i} nodes {nodes}", file=sys.stderr, flush=True)

    send("quit")
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()

    Path(prefix + "_raw.txt").write_text("\n".join(raw) + "\n", encoding="utf-8")
    Path(prefix + "_rows.txt").write_text("\n".join(rows) + "\n", encoding="utf-8")
    meta = [
        f"exe: {exe_path}",
        f"sha256: {sha}",
        f"id name: {id_name}",
        "options:",
        *options,
        "",
    ]
    Path(prefix + ".meta").write_text("\n".join(meta), encoding="utf-8")
    print(f"wrote {prefix} positions {len(rows)} sum {sum(int(r.split()[1]) for r in rows)}")


if __name__ == "__main__":
    main()
