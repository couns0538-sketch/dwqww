#!/usr/bin/env python3
"""Run one search set under a sanitizer build and keep stdout, stderr, and nm proof.

Same runner for the real build and for the one-bug scratch build.
"""
import hashlib
import os
import pathlib
import select
import subprocess
import sys
import time

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")
S14 = [
    "setoption name Hash value 16",
    "setoption name Threads value 1",
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


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_fens(path):
    fens = []
    for line in pathlib.Path(path).read_text().splitlines():
        text = line.strip()
        if text and not text.startswith("#"):
            fens.append(text.split(";")[0].strip())
    return fens


def nm_asan_count(exe):
    proc = subprocess.run(["nm", "-C", exe], text=True, capture_output=True, check=False)
    return sum(1 for line in proc.stdout.splitlines() if "__asan_" in line)


class Engine:
    def __init__(self, exe):
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        self.fd = self.proc.stdout.fileno()
        self.err_fd = self.proc.stderr.fileno()
        self.pending = b""
        self.err_pending = b""
        self.lines = []
        self.stderr_parts = []

    def send(self, line):
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def pump_err(self):
        while True:
            ready, _, _ = select.select([self.err_fd], [], [], 0)
            if not ready:
                return
            chunk = os.read(self.err_fd, 1 << 16)
            if not chunk:
                return
            self.stderr_parts.append(chunk)

    def read_until(self, kind, timeout):
        deadline = time.time() + timeout
        while time.time() < deadline:
            self.pump_err()
            if self.proc.poll() is not None and not self.pending:
                self.pump_err()
                raise RuntimeError(f"engine exited {self.proc.returncode} waiting for {kind}")
            ready, _, _ = select.select([self.fd], [], [], 0.25)
            if not ready:
                continue
            chunk = os.read(self.fd, 1 << 16)
            if not chunk:
                raise RuntimeError(f"stdout closed waiting for {kind}")
            self.pending += chunk
            while b"\n" in self.pending:
                raw, self.pending = self.pending.split(b"\n", 1)
                line = raw.decode("utf-8", "replace").rstrip("\r")
                self.lines.append(line)
                for phrase in BAD:
                    if phrase in line:
                        raise RuntimeError(line)
                if kind == "uciok" and line == "uciok":
                    return
                if kind == "readyok" and line == "readyok":
                    return
                if kind == "bestmove" and line.startswith("bestmove "):
                    return
        raise TimeoutError(f"timed out waiting for {kind}")

    def close(self):
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()
            self.proc.wait(timeout=5)
        self.pump_err()
        leftover = self.proc.stderr.read() if self.proc.stderr else b""
        if leftover:
            self.stderr_parts.append(leftover)
        return b"".join(self.stderr_parts).decode("utf-8", "replace")


def main():
    if len(sys.argv) < 5:
        print("usage: asan_run.py EXE OUTSTEM FENFILE DEPTH [extra setoption ...]", file=sys.stderr)
        return 2
    exe = str(pathlib.Path(sys.argv[1]).resolve())
    out_stem = pathlib.Path(sys.argv[2])
    fen_file = pathlib.Path(sys.argv[3])
    depth = int(sys.argv[4])
    extras = sys.argv[5:]
    fens = load_fens(fen_file)
    options = [*S14, *extras]
    asan_count = nm_asan_count(exe)
    engine = Engine(exe)
    id_name = ""
    failed = None
    try:
        engine.send("uci")
        engine.read_until("uciok", 60)
        for line in engine.lines:
            if line.startswith("id name "):
                id_name = line[len("id name "):]
        engine.send("isready")
        engine.read_until("readyok", 60)
        for option in options:
            engine.send(option)
            engine.send("isready")
            engine.read_until("readyok", 60)
        for fen in fens:
            engine.send("ucinewgame")
            engine.send("isready")
            engine.read_until("readyok", 60)
            engine.send(f"position fen {fen}")
            engine.send("isready")
            engine.read_until("readyok", 60)
            engine.send(f"go depth {depth}")
            engine.read_until("bestmove", 180)
    except Exception as exc:
        failed = exc
    stderr = engine.close()
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    raw_path = out_stem.with_suffix(".txt")
    err_path = pathlib.Path(str(out_stem) + ".stderr")
    meta_path = pathlib.Path(str(out_stem) + ".meta")
    raw_path.write_text("\n".join(engine.lines) + ("\n" if engine.lines else ""))
    err_path.write_text(stderr)
    san_lines = [line for line in stderr.splitlines() if "Sanitizer" in line or "runtime error" in line]
    meta = [
        f"exe={exe}",
        f"sha256={sha256_file(exe)}",
        f"id_name={id_name}",
        f"nm_asan_count={asan_count}",
        f"fen_file={fen_file.resolve()}",
        f"fen_count={len(fens)}",
        f"depth={depth}",
        f"sanitizer_lines={len(san_lines)}",
        "options_sent:",
        *options,
        "",
    ]
    meta_path.write_text("\n".join(meta))
    print(f"nm_asan_count={asan_count}")
    print(f"sanitizer_lines={len(san_lines)}")
    for line in san_lines[:20]:
        print(line)
    if failed is not None:
        print(f"RUNNER_NOTE {failed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
