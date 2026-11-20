#!/usr/bin/env python3
"""UCI harness for seat 092.

One engine process per run. After every setoption and every position command
this reads every line until readyok. It stops on unknown option, invalid
value, invalid FEN, or illegal move. Honesty mode sends no setoption.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import time

BAD_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")

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


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_fens(path: str, limit: int | None) -> list[str]:
    fens: list[str] = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text or text.startswith("#"):
                continue
            # EPD may carry trailing opcodes. A FEN has six fields.
            parts = text.split()
            if len(parts) >= 6:
                fen = " ".join(parts[:6])
            else:
                fen = text
            fens.append(fen)
            if limit is not None and len(fens) >= limit:
                break
    return fens


class Engine:
    def __init__(self, exe: str) -> None:
        self.exe = os.path.abspath(exe)
        self.proc = subprocess.Popen(
            [self.exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.transcript: list[str] = []
        self.options_sent: list[str] = []
        self.id_name = ""

    def send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.transcript.append(">> " + line)
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_line(self, timeout: float) -> str:
        assert self.proc.stdout is not None
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            assert self.proc.stdout is not None
            line = self.proc.stdout.readline()
            if line == "" and self.proc.poll() is not None:
                raise SystemExit("STOP engine exited")
            if line:
                text = line.rstrip("\n")
                self.transcript.append(text)
                for mark in BAD_MARKS:
                    if mark in text:
                        raise SystemExit(f"STOP {mark}: {text}")
                return text
            time.sleep(0.01)
        raise SystemExit(f"STOP timeout after {timeout}s waiting for the engine")

    def read_until(self, token: str, timeout: float) -> None:
        while True:
            text = self.read_line(timeout)
            if text == token or text.startswith(token + " "):
                return

    def ready(self, timeout: float = 30.0) -> None:
        self.send("isready")
        self.read_until("readyok", timeout)

    def close(self) -> None:
        if self.proc.poll() is None:
            try:
                self.send("quit")
            except BrokenPipeError:
                pass
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()

    def handshake(self) -> None:
        self.send("uci")
        while True:
            text = self.read_line(30)
            if text.startswith("id name "):
                self.id_name = text[len("id name ") :]
            if text == "uciok":
                break
        self.ready()


def write_meta(path: str, engine: Engine) -> None:
    lines = [
        f"exe {engine.exe}",
        f"sha256 {sha256_file(engine.exe)}",
        f"id_name {engine.id_name}",
        "options_sent",
    ]
    lines.extend(engine.options_sent)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def setoption(engine: Engine, name: str, value: str) -> None:
    line = f"setoption name {name} value {value}"
    engine.options_sent.append(line)
    engine.send(line)
    engine.ready()


def apply_measured_options(engine: Engine, switch: str | None) -> None:
    setoption(engine, "Threads", "1")
    setoption(engine, "Hash", "16")
    for name, value in S14:
        setoption(engine, name, value)
    if switch is not None:
        setoption(engine, "HindsightDepth", switch)


def nodes_of(transcript_tail: list[str]) -> tuple[int, int]:
    depth = -1
    nodes = -1
    for text in transcript_tail:
        if not text.startswith("info ") or " nodes " not in text:
            continue
        parts = text.split()
        if "depth" in parts:
            depth = int(parts[parts.index("depth") + 1])
        if "nodes" in parts:
            nodes = int(parts[parts.index("nodes") + 1])
    if nodes < 0:
        raise SystemExit("STOP no nodes on the info line")
    return depth, nodes


def search_fens(engine: Engine, fens: list[str], depth: int, out_path: str) -> None:
    rows: list[str] = []
    for index, fen in enumerate(fens):
        start = len(engine.transcript)
        engine.send("ucinewgame")
        engine.ready()
        engine.send(f"position fen {fen}")
        engine.ready()
        engine.send(f"go depth {depth}")
        engine.read_until("bestmove", 180)
        got_depth, nodes = nodes_of(engine.transcript[start:])
        if got_depth != depth:
            raise SystemExit(f"STOP depth {got_depth} != {depth} on fen {index}")
        rows.append(f"{nodes}\t{fen}")
        if (index + 1) % 25 == 0:
            print(f"searched {index + 1}/{len(fens)}", file=sys.stderr, flush=True)
    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(rows) + "\n")
    print(f"sum {sum(int(row.split(chr(9), 1)[0]) for row in rows)} positions {len(rows)}")


def honesty(exe: str, out_dir: str, tag: str = "") -> None:
    jobs = [
        ("bench11", "bench 11", "312866"),
        ("bench13", "bench 13", "862329"),
        ("bench16", "bench 16", "3024920"),
        ("perft5", "go perft 5", "4865609"),
    ]
    # Identity is read from its own process so the measured process sends no uci.
    probe = Engine(exe)
    try:
        probe.handshake()
    finally:
        probe.close()
    failed = False
    for name, command, expected in jobs:
        engine = Engine(exe)
        engine.id_name = probe.id_name
        try:
            engine.send(command)
            if command.startswith("bench"):
                while True:
                    text = engine.read_line(180)
                    if text.startswith("info string bench "):
                        break
            else:
                while True:
                    text = engine.read_line(180)
                    if text.startswith("nodes "):
                        break
        finally:
            engine.close()
        raw_path = os.path.join(out_dir, f"honesty_{tag}{name}.txt")
        meta_path = os.path.join(out_dir, f"honesty_{tag}{name}.meta")
        with open(raw_path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(engine.transcript) + "\n")
        write_meta(meta_path, engine)
        nodes = ""
        for text in engine.transcript:
            if " nodes " in text or text.startswith("nodes "):
                parts = text.split()
                if "nodes" in parts:
                    nodes = parts[parts.index("nodes") + 1]
        status = "ok" if nodes == expected else "MISMATCH"
        if status != "ok":
            failed = True
        print(f"{name} nodes {nodes} expected {expected} {status}")
    if failed:
        raise SystemExit(1)


def uci_dump(exe: str, out_path: str) -> None:
    engine = Engine(exe)
    try:
        engine.handshake()
    finally:
        engine.close()
    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(engine.transcript) + "\n")
    write_meta(out_path + ".meta", engine)
    for text in engine.transcript:
        if "HindsightDepth" in text:
            print(text)


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit(
            "usage: harness.py honesty|uci|search <exe> [out] [fens] [depth] [limit] [switch]"
        )
    mode = sys.argv[1]
    exe = sys.argv[2]
    if mode == "honesty":
        tag = sys.argv[4] if len(sys.argv) > 4 else ""
        honesty(exe, sys.argv[3], tag)
        return
    if mode == "uci":
        uci_dump(exe, sys.argv[3])
        return
    if mode != "search":
        raise SystemExit(f"unknown mode {mode}")
    out_path, fen_path, depth_s, limit_s, switch = sys.argv[3:8]
    limit = None if limit_s == "-" else int(limit_s)
    switch_value = None if switch == "-" else switch
    fens = load_fens(fen_path, limit)
    engine = Engine(exe)
    try:
        engine.handshake()
        apply_measured_options(engine, switch_value)
        search_fens(engine, fens, int(depth_s), out_path)
    finally:
        engine.close()
        write_meta(out_path + ".meta", engine)
        raw_path = out_path + ".raw"
        with open(raw_path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(engine.transcript) + "\n")


if __name__ == "__main__":
    main()
