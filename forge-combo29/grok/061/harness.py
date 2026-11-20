#!/usr/bin/env python3
"""UCI harness. One process per honesty line. Depth sets reuse one process
and send ucinewgame before every go. Stops on unknown option, invalid value,
invalid FEN, or illegal move."""

import argparse
import hashlib
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

STOP_PHRASES = ("unknown option", "invalid value", "invalid FEN", "illegal move")

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


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def asan_symbol_count(exe):
    listed = subprocess.run(["nm", "-C", exe], capture_output=True, text=True, check=False)
    return sum(1 for line in listed.stdout.splitlines() if "__asan_" in line)


def load_positions(path):
    positions = []
    for raw in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 6 and parts[1] in ("w", "b") and parts[4].isdigit():
            positions.append(" ".join(parts[:6]))
        elif len(parts) >= 4 and parts[1] in ("w", "b"):
            positions.append(" ".join(parts[:4]) + " 0 1")
        else:
            positions.append(line)
    return positions


class Engine:
    def __init__(self, exe):
        self.exe = str(Path(exe).resolve())
        self.transcript = []
        self.stderr = []
        self.options = []
        self.id_name = ""
        self.stopped = ""
        self.timed_out = False
        self.queue = queue.Queue()
        self.err_queue = queue.Queue()
        self.proc = subprocess.Popen(
            [self.exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.out_thread = threading.Thread(target=self._pump, args=(self.proc.stdout, self.queue), daemon=True)
        self.err_thread = threading.Thread(target=self._pump, args=(self.proc.stderr, self.err_queue), daemon=True)
        self.out_thread.start()
        self.err_thread.start()

    @staticmethod
    def _pump(pipe, sink):
        for line in pipe:
            sink.put(line.rstrip("\r\n"))
        sink.put(None)

    def _drain_stderr(self):
        while True:
            try:
                line = self.err_queue.get_nowait()
            except queue.Empty:
                return
            if line is None:
                return
            self.stderr.append(line)
            self.transcript.append("[stderr] " + line)

    def send(self, line):
        self.transcript.append(">>> " + line)
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, predicate, timeout):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self._drain_stderr()
            try:
                line = self.queue.get(timeout=0.2)
            except queue.Empty:
                if self.proc.poll() is not None and self.queue.empty():
                    self._drain_stderr()
                    return False
                continue
            if line is None:
                self._drain_stderr()
                return False
            self.transcript.append(line)
            if line.startswith("id name ") and not self.id_name:
                self.id_name = line[len("id name ") :]
            for phrase in STOP_PHRASES:
                if phrase in line:
                    self.stopped = line
                    return False
            if predicate(line):
                self._drain_stderr()
                return True
        self.timed_out = True
        self._drain_stderr()
        return False

    def ready(self, timeout=30):
        self.send("isready")
        return self.read_until(lambda line: line.strip() == "readyok", timeout)

    def setoption(self, name, value, timeout=30):
        command = f"setoption name {name} value {value}"
        self.options.append(command)
        self.send(command)
        return self.ready(timeout)

    def close(self):
        if self.proc.poll() is None:
            try:
                self.send("quit")
            except BrokenPipeError:
                pass
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self._drain_stderr()


def write_pair(out_path, engine):
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(engine.transcript) + "\n", encoding="utf-8")
    meta = [
        f"exe={engine.exe}",
        f"sha256={sha256_file(engine.exe)}",
        f"id_name={engine.id_name}",
        f"asan_symbols={asan_symbol_count(engine.exe)}",
        f"stopped={engine.stopped}",
        f"timed_out={engine.timed_out}",
        "options:",
    ]
    meta.extend(engine.options if engine.options else ["(none)"])
    if engine.stderr:
        meta.append("stderr:")
        meta.extend(engine.stderr)
    out.with_suffix(out.suffix + ".meta").write_text("\n".join(meta) + "\n", encoding="utf-8")


def handshake(engine, timeout):
    engine.send("uci")
    if not engine.read_until(lambda line: line.strip() == "uciok", timeout):
        return False
    return engine.ready(timeout)


def run_honesty(exe, out_dir):
    out_dir = Path(out_dir)
    jobs = [
        ("bench11", ["bench 11"], lambda line: line.startswith("info string bench ")),
        ("bench13", ["bench 13"], lambda line: line.startswith("info string bench ")),
        ("bench16", ["bench 16"], lambda line: line.startswith("info string bench ")),
        ("perft5", ["go perft 5"], lambda line: line.startswith("nodes ")),
    ]
    failed = False
    for name, commands, predicate in jobs:
        engine = Engine(exe)
        ok = handshake(engine, 60)
        for command in commands:
            if not ok:
                break
            engine.send(command)
            ok = engine.read_until(predicate, 180)
        engine.close()
        write_pair(out_dir / f"honesty_{name}.txt", engine)
        if engine.stopped or engine.timed_out or not ok:
            failed = True
            print(f"FAIL {name} stopped={engine.stopped} timeout={engine.timed_out}", file=sys.stderr)
        else:
            print(f"OK {name}")
    return 1 if failed else 0


def run_depth(exe, fens, depth, out_path, use_s14, idea, limit):
    positions = load_positions(fens)
    if limit:
        positions = positions[:limit]
    engine = Engine(exe)
    ok = handshake(engine, 60)
    if ok:
        ok = engine.setoption("Threads", "1") and engine.setoption("Hash", "16")
    if ok and use_s14:
        for name, value in S14:
            if not engine.setoption(name, value):
                ok = False
                break
    if ok and idea is not None:
        ok = engine.setoption("IdeaS25", "true" if idea else "false")
    for fen in positions:
        if not ok:
            break
        engine.send("ucinewgame")
        if not engine.ready(60):
            ok = False
            break
        engine.send("position fen " + fen)
        if not engine.ready(60):
            ok = False
            break
        engine.send(f"go depth {depth}")
        if not engine.read_until(lambda line: line.startswith("bestmove "), 180):
            ok = False
            break
    engine.close()
    write_pair(out_path, engine)
    if engine.stopped or engine.timed_out or not ok:
        print(f"FAIL depth stopped={engine.stopped} timeout={engine.timed_out}", file=sys.stderr)
        return 1
    print(f"OK depth positions={len(positions)}")
    return 0


def run_options(exe, out_path):
    engine = Engine(exe)
    ok = handshake(engine, 60)
    engine.close()
    write_pair(out_path, engine)
    return 0 if ok and not engine.stopped else 1


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    honesty = sub.add_parser("honesty")
    honesty.add_argument("--exe", required=True)
    honesty.add_argument("--out-dir", required=True)
    depth = sub.add_parser("depth")
    depth.add_argument("--exe", required=True)
    depth.add_argument("--fens", required=True)
    depth.add_argument("--depth", type=int, required=True)
    depth.add_argument("--out", required=True)
    depth.add_argument("--s14", action="store_true")
    depth.add_argument("--idea", choices=("true", "false"))
    depth.add_argument("--limit", type=int, default=0)
    options = sub.add_parser("options")
    options.add_argument("--exe", required=True)
    options.add_argument("--out", required=True)
    args = parser.parse_args()
    if args.cmd == "honesty":
        return run_honesty(args.exe, args.out_dir)
    if args.cmd == "depth":
        idea = None if args.idea is None else args.idea == "true"
        return run_depth(args.exe, args.fens, args.depth, args.out, args.s14, idea, args.limit)
    return run_options(args.exe, args.out)


if __name__ == "__main__":
    sys.exit(main())
