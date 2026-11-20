#!/usr/bin/env python3
"""UCI harness for seat 079. Writes raw engine text and a .meta beside it.

A fresh process is used for each honesty command. A depth run keeps one
process and sends ucinewgame before every go. After every setoption and
every position the runner waits for readyok. It stops on unknown option,
invalid value, invalid FEN, or illegal move.
"""

import hashlib
import os
import re
import select
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
    ("Threads", "1"),
    ("Hash", "16"),
]

BAD = ("unknown option", "invalid value", "invalid fen", "illegal move")
NODE_RE = re.compile(r"\bnodes (\d+)\b")


class Stop(Exception):
    pass


class Engine:
    def __init__(self, exe: str):
        self.exe = str(Path(exe).resolve())
        self.proc = subprocess.Popen(
            [self.exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.lines: list[str] = []
        self._pending = b""
        assert self.proc.stdout is not None
        self._fd = self.proc.stdout.fileno()
        os.set_blocking(self._fd, False)

    def send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, marker: str, timeout: float) -> str:
        deadline = time.time() + timeout
        while time.time() < deadline:
            while b"\n" in self._pending:
                raw, self._pending = self._pending.split(b"\n", 1)
                line = raw.decode("utf-8", "replace").rstrip("\r")
                self.lines.append(line)
                low = line.lower()
                for bad in BAD:
                    if bad in low:
                        raise Stop(line)
                if marker in line:
                    return line
            if self.proc.poll() is not None:
                try:
                    while True:
                        chunk = os.read(self._fd, 1 << 16)
                        if not chunk:
                            break
                        self._pending += chunk
                except BlockingIOError:
                    pass
                if b"\n" not in self._pending:
                    break
                continue
            remain = max(0.0, deadline - time.time())
            readable, _, _ = select.select([self._fd], [], [], min(0.5, remain))
            if not readable:
                continue
            try:
                chunk = os.read(self._fd, 1 << 16)
            except BlockingIOError:
                continue
            if chunk == b"":
                break
            self._pending += chunk
        raise Stop("timeout waiting for " + marker + " last=" + " | ".join(self.lines[-6:]))

    def close(self) -> None:
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()


def sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_meta(path: Path, exe: str, id_name: str, options: list[str], extra: list[str]) -> None:
    body = [
        "exe " + str(Path(exe).resolve()),
        "sha256 " + sha256(exe),
        "id_name " + id_name,
        "options_sent " + str(len(options)),
    ]
    body.extend("option " + item for item in options)
    body.extend(extra)
    path.write_text("\n".join(body) + "\n", encoding="utf-8")


def handshake(engine: Engine) -> str:
    engine.send("uci")
    engine.read_until("uciok", 30.0)
    id_name = ""
    for line in engine.lines:
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
    if not id_name:
        raise Stop("no id name")
    return id_name


def ready(engine: Engine) -> None:
    engine.send("isready")
    engine.read_until("readyok", 120.0)


def apply_options(engine: Engine, options: list[tuple[str, str]]) -> list[str]:
    sent = []
    for name, value in options:
        line = f"setoption name {name} value {value}"
        engine.send(line)
        sent.append(line)
        ready(engine)
    return sent


def load_fens(path: Path) -> list[str]:
    fens = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        text = raw.strip()
        if not text or text.startswith("#"):
            continue
        fens.append(text)
    return fens


def last_nodes(lines: list[str]) -> int:
    found = None
    for line in lines:
        match = NODE_RE.search(line)
        if match:
            found = int(match.group(1))
    if found is None:
        raise Stop("no nodes line")
    return found


def cmd_honesty(exe: str, out_dir: Path, tag: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = [
        ("bench11", "bench 11"),
        ("bench13", "bench 13"),
        ("bench16", "bench 16"),
        ("perft5", "go perft 5"),
    ]
    summary = []
    for job, command in jobs:
        engine = Engine(exe)
        try:
            id_name = handshake(engine)
            before = len(engine.lines)
            engine.send(command)
            if command.startswith("bench"):
                engine.read_until("info string bench", 300.0)
            else:
                engine.read_until("nodes ", 120.0)
            chunk = engine.lines[before:]
            nodes = last_nodes(chunk)
            raw_path = out_dir / f"honesty_{tag}_{job}.txt"
            raw_path.write_text("\n".join(engine.lines) + "\n", encoding="utf-8")
            write_meta(
                out_dir / f"honesty_{tag}_{job}.meta",
                exe,
                id_name,
                [],
                ["command " + command, "nodes " + str(nodes)],
            )
            summary.append(f"{command} nodes {nodes}")
            print(summary[-1], flush=True)
        finally:
            engine.close()
    (out_dir / f"HONESTY_{tag.upper()}.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")


def cmd_depth(exe: str, fens_path: Path, depth: int, out_stem: Path, extra: list[tuple[str, str]]) -> None:
    fens = load_fens(fens_path)
    engine = Engine(exe)
    failed = True
    try:
        id_name = handshake(engine)
        options = S14 + extra
        sent = apply_options(engine, options)
        nodes_out = []
        raw_parts = ["\n".join(engine.lines)]
        for index, fen in enumerate(fens):
            engine.send("ucinewgame")
            ready(engine)
            engine.send("position fen " + fen)
            ready(engine)
            before = len(engine.lines)
            engine.send(f"go depth {depth}")
            engine.read_until("bestmove ", 180.0)
            chunk = engine.lines[before:]
            nodes = last_nodes(chunk)
            nodes_out.append(str(nodes))
            raw_parts.append("\n".join(chunk))
            if (index + 1) % 50 == 0 or index + 1 == len(fens):
                print(f"{out_stem.name} {index + 1}/{len(fens)} nodes {nodes}", flush=True)
        out_stem.parent.mkdir(parents=True, exist_ok=True)
        (out_stem.parent / (out_stem.name + ".nodes")).write_text("\n".join(nodes_out) + "\n", encoding="utf-8")
        (out_stem.parent / (out_stem.name + ".raw.txt")).write_text("\n".join(raw_parts) + "\n", encoding="utf-8")
        write_meta(
            out_stem.parent / (out_stem.name + ".meta"),
            exe,
            id_name,
            sent,
            [
                "fen_file " + str(fens_path),
                "depth " + str(depth),
                "positions " + str(len(fens)),
                "node_sum " + str(sum(int(item) for item in nodes_out)),
            ],
        )
        print("SUM", out_stem.name, sum(int(item) for item in nodes_out), flush=True)
        failed = False
    finally:
        if failed:
            out_stem.parent.mkdir(parents=True, exist_ok=True)
            (out_stem.parent / (out_stem.name + ".partial.txt")).write_text(
                "\n".join(engine.lines) + "\n", encoding="utf-8"
            )
        engine.close()


def main() -> None:
    if len(sys.argv) < 3:
        print("usage: harness.py honesty EXE OUTDIR TAG | depth EXE FENS DEPTH OUTSTEM [Name=Value ...]", file=sys.stderr)
        sys.exit(2)
    mode = sys.argv[1]
    if mode == "honesty":
        cmd_honesty(sys.argv[2], Path(sys.argv[3]), sys.argv[4])
        return
    if mode == "depth":
        extra = []
        for item in sys.argv[6:]:
            name, value = item.split("=", 1)
            extra.append((name, value))
        cmd_depth(sys.argv[2], Path(sys.argv[3]), int(sys.argv[4]), Path(sys.argv[5]), extra)
        return
    print("unknown mode", mode, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except Stop as exc:
        print("STOP", exc, file=sys.stderr)
        sys.exit(1)
