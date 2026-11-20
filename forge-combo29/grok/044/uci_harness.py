#!/usr/bin/env python3
"""UCI harness for Forge honesty checks and fixed-depth node counts.

One engine process per honesty command, with no setoption.
A measured set sends S14 (and any extra options) in the given order, then
isready after every setoption and every position. ucinewgame + isready comes
before every go, and before the position so the FEN is the one searched.
"""

import hashlib
import subprocess
import sys
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


class HarnessError(RuntimeError):
    pass


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_id_name(exe):
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None
    proc.stdin.write("uci\n")
    proc.stdin.flush()
    name = ""
    for line in proc.stdout:
        line = line.rstrip("\n")
        if line.startswith("id name "):
            name = line[len("id name ") :]
        if line == "uciok":
            break
    proc.stdin.write("quit\n")
    proc.stdin.flush()
    proc.wait(timeout=30)
    if not name:
        raise HarnessError("uci did not report id name")
    return name


def write_meta(path, exe, command, options):
    text = [
        f"exe={exe}",
        f"sha256={sha256_file(exe)}",
        f"id_name={read_id_name(exe)}",
        f"command={command}",
        "options_sent:",
    ]
    if not options:
        text.append("(none)")
    else:
        text.extend(f"setoption name {name} value {value}" for name, value in options)
    Path(path).write_text("\n".join(text) + "\n", encoding="utf-8")


def _check_line(line):
    for mark in STOP_MARKS:
        if mark in line:
            raise HarnessError(f"stop mark {mark!r} in line: {line}")


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

    def send(self, line):
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, done):
        assert self.proc.stdout is not None
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                raise HarnessError("engine closed stdout early")
            line = line.rstrip("\n")
            self.lines.append(line)
            _check_line(line)
            if done(line):
                return line

    def ready(self):
        self.send("isready")
        self.read_until(lambda line: line == "readyok")

    def close(self):
        if self.proc.poll() is None:
            try:
                self.send("quit")
            except BrokenPipeError:
                pass
            self.proc.wait(timeout=30)


def honesty_one(exe, command, out_path, meta_path):
    """Fresh process. The only command before quit is `command` (no setoption)."""
    engine = Engine(exe)
    try:
        engine.send(command)
        if command.startswith("bench"):
            engine.read_until(lambda line: line.startswith("info string bench depth "))
        elif command.startswith("go perft"):
            engine.read_until(lambda line: line.startswith("nodes "))
        else:
            raise HarnessError(f"unsupported honesty command {command}")
    finally:
        engine.close()
    Path(out_path).write_text("\n".join(engine.lines) + "\n", encoding="utf-8")
    write_meta(meta_path, exe, command, [])


def load_fens(path):
    fens = []
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        parts = raw.split()
        if len(parts) < 6:
            continue
        fens.append(" ".join(parts[:6]))
    return fens


def nodes_from_info(lines, depth):
    needle = f"info depth {depth} "
    found = None
    for line in lines:
        if line.startswith(needle) and " nodes " in line:
            found = int(line.split(" nodes ", 1)[1].split()[0])
    if found is None:
        raise HarnessError(f"no info depth {depth} nodes line")
    return found


def search_chunk(exe, options, fens, depth, offset):
    engine = Engine(exe)
    rows = []
    raw_blocks = []
    try:
        for name, value in options:
            engine.send(f"setoption name {name} value {value}")
            engine.ready()
        for index, fen in enumerate(fens):
            start = len(engine.lines)
            engine.send("ucinewgame")
            engine.ready()
            engine.send(f"position fen {fen}")
            engine.ready()
            engine.send(f"go depth {depth}")
            engine.read_until(lambda line: line.startswith("bestmove "))
            block = engine.lines[start:]
            nodes = nodes_from_info(block, depth)
            rows.append((offset + index, nodes, fen))
            raw_blocks.append("\n".join(block))
    finally:
        engine.close()
    return rows, raw_blocks


def search_set(exe, options, fen_path, depth, out_prefix, workers):
    fens = load_fens(fen_path)
    if workers < 1:
        workers = 1
    chunks = [[] for _ in range(workers)]
    for i, fen in enumerate(fens):
        chunks[i % workers].append((i, fen))
    # Keep each worker's positions in order, but the engine sees them as a list.
    jobs = []
    for chunk in chunks:
        if not chunk:
            continue
        jobs.append((exe, options, [fen for _, fen in chunk], depth, [i for i, _ in chunk]))

    from concurrent.futures import ThreadPoolExecutor

    results = []

    def run_job(job):
        exe_path, opts, fen_list, dep, indices = job
        rows, blocks = search_chunk(exe_path, opts, fen_list, dep, 0)
        paired = []
        for (idx, _nodes, _fen), (row, block) in zip(
            [(i, None, fens[i]) for i in indices], zip(rows, blocks)
        ):
            paired.append((idx, row[1], fens[idx], block))
        return paired

    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        for paired in pool.map(run_job, jobs):
            results.extend(paired)
    results.sort(key=lambda item: item[0])
    if [item[0] for item in results] != list(range(len(fens))):
        raise HarnessError("position coverage is not 0..n-1")
    raw_path = Path(str(out_prefix) + ".raw")
    nodes_path = Path(str(out_prefix) + ".nodes")
    meta_path = Path(str(out_prefix) + ".meta")
    raw_parts = []
    node_lines = []
    total = 0
    for index, nodes, fen, block in results:
        raw_parts.append(f"### position {index}\n{block}")
        node_lines.append(f"{index} {nodes}")
        total += nodes
    raw_path.write_text("\n".join(raw_parts) + "\n", encoding="utf-8")
    nodes_path.write_text("\n".join(node_lines) + "\n", encoding="utf-8")
    write_meta(meta_path, exe, f"go depth {depth} positions={fen_path} count={len(fens)}", options)
    print(f"positions {len(fens)} nodes {total} file {nodes_path}")
    return total


def main(argv):
    if len(argv) < 2:
        print("usage: uci_harness.py honesty|search ...", file=sys.stderr)
        return 2
    mode = argv[1]
    if mode == "honesty":
        exe, command, out_path, meta_path = argv[2], argv[3], argv[4], argv[5]
        honesty_one(exe, command, out_path, meta_path)
        text = Path(out_path).read_text(encoding="utf-8").strip()
        print(text.splitlines()[-1])
        return 0
    if mode == "search":
        # search EXE FEN DEPTH OUT_PREFIX WORKERS [Name=Value ...]
        exe, fen_path, depth, out_prefix, workers = argv[2], argv[3], int(argv[4]), argv[5], int(argv[6])
        options = list(S14)
        for item in argv[7:]:
            name, value = item.split("=", 1)
            options.append((name, value))
        search_set(exe, options, fen_path, depth, out_prefix, workers)
        return 0
    print(f"unknown mode {mode}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except HarnessError as exc:
        print(f"HARNESS FAIL {exc}", file=sys.stderr)
        sys.exit(1)
