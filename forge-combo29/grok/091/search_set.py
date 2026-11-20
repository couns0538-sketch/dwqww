#!/usr/bin/env python3
"""Depth search of a FEN list. One engine process. Raw stdout is the evidence."""
import hashlib
import os
import pathlib
import select
import subprocess
import sys
import time

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")

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
        if not text or text.startswith("#"):
            continue
        fens.append(text.split(";")[0].strip())
    return fens


class Engine:
    def __init__(self, exe):
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        self.stdout_fd = self.proc.stdout.fileno()
        self.pending = b""
        self.lines = []

    def send(self, line):
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def read_until(self, kind, timeout):
        deadline = time.time() + timeout
        got = []
        while time.time() < deadline:
            if self.proc.poll() is not None and not self.pending:
                break
            ready, _, _ = select.select([self.stdout_fd], [], [], 0.25)
            if not ready:
                continue
            chunk = os.read(self.stdout_fd, 1 << 16)
            if not chunk:
                break
            self.pending += chunk
            while b"\n" in self.pending:
                raw, self.pending = self.pending.split(b"\n", 1)
                line = raw.decode("utf-8", "replace").rstrip("\r")
                got.append(line)
                self.lines.append(line)
                for phrase in BAD:
                    if phrase in line:
                        raise RuntimeError(line)
                if kind == "uciok" and line == "uciok":
                    return got
                if kind == "readyok" and line == "readyok":
                    return got
                if kind == "bestmove" and line.startswith("bestmove "):
                    return got
        raise TimeoutError(f"timed out waiting for {kind}; last={got[-3:]}")

    def close(self):
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()
        err = self.proc.stderr.read().decode("utf-8", "replace")
        return err


def main():
    if len(sys.argv) < 5:
        print("usage: search_set.py EXE OUTSTEM FENFILE DEPTH [extra setoption ...]", file=sys.stderr)
        return 2
    exe = str(pathlib.Path(sys.argv[1]).resolve())
    out_stem = pathlib.Path(sys.argv[2])
    fen_file = pathlib.Path(sys.argv[3])
    depth = int(sys.argv[4])
    extras = sys.argv[5:]
    fens = load_fens(fen_file)
    options = [
        "setoption name Hash value 16",
        "setoption name Threads value 1",
        *S14,
        *extras,
    ]
    engine = Engine(exe)
    id_name = ""
    try:
        engine.send("uci")
        uci_lines = engine.read_until("uciok", 30)
        for line in uci_lines:
            if line.startswith("id name "):
                id_name = line[len("id name "):]
        engine.send("isready")
        engine.read_until("readyok", 30)
        for option in options:
            engine.send(option)
            engine.send("isready")
            engine.read_until("readyok", 30)
        for fen in fens:
            engine.send("ucinewgame")
            engine.send("isready")
            engine.read_until("readyok", 30)
            engine.send(f"position fen {fen}")
            engine.send("isready")
            engine.read_until("readyok", 30)
            engine.send(f"go depth {depth}")
            engine.read_until("bestmove", 120)
        failed = None
    except Exception as exc:
        failed = exc
    finally:
        stderr = engine.close()
    raw_path = out_stem.with_suffix(".txt")
    meta_path = pathlib.Path(str(out_stem) + ".meta")
    err_path = pathlib.Path(str(out_stem) + ".stderr")
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text("\n".join(engine.lines) + ("\n" if engine.lines else ""))
    err_path.write_text(stderr or "")
    meta = [
        f"exe={exe}",
        f"sha256={sha256_file(exe)}",
        f"id_name={id_name}",
        f"fen_file={fen_file.resolve()}",
        f"fen_sha256={sha256_file(fen_file)}",
        f"fen_count={len(fens)}",
        f"depth={depth}",
        "options_sent:",
        *options,
        "",
    ]
    meta_path.write_text("\n".join(meta))
    print(f"positions {len(fens)} lines {len(engine.lines)} raw {raw_path}")
    if failed is not None:
        print(f"HARNESS STOP {failed}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"HARNESS STOP {exc}", file=sys.stderr)
        sys.exit(1)
