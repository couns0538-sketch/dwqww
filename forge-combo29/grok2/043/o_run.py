#!/usr/bin/env python3
"""o_run.py EXE FENS OUTSTEM [SWITCH true|false]

Depth-12 node counts on each FEN. S14, Threads 1 and Hash 16 are sent in that
order. SWITCH, when given, is sent after them. isready is read to readyok
after every setoption and every position. Stops on unknown option, invalid
value, invalid FEN or illegal move.
"""
import hashlib
import os
import select
import subprocess
import sys
import time
from pathlib import Path

S14 = (
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
)

STOPS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


class Engine:
    def __init__(self, exe):
        self.exe = exe
        self.err_path = None
        self.proc = None
        self.buf = b""

    def start(self, err_path):
        self.err_path = open(err_path, "wb")
        self.proc = subprocess.Popen(
            [self.exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=self.err_path,
            bufsize=0,
        )

    def send(self, line):
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def read_until(self, done, timeout):
        lines = []
        deadline = time.monotonic() + timeout
        fd = self.proc.stdout.fileno()
        while True:
            if self.proc.poll() is not None and not self.buf:
                raise SystemExit(f"STOP: engine exited rc={self.proc.returncode} during read")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise SystemExit("STOP: timeout waiting for engine")
            ready, _, _ = select.select([fd], [], [], min(1.0, remaining))
            if not ready:
                continue
            chunk = os.read(fd, 1 << 16)
            if not chunk:
                if self.proc.poll() is not None:
                    raise SystemExit(f"STOP: engine exited rc={self.proc.returncode}")
                continue
            self.buf += chunk
            while b"\n" in self.buf:
                raw, self.buf = self.buf.split(b"\n", 1)
                line = raw.decode("utf-8", "replace").rstrip("\r")
                lines.append(line)
                for needle in STOPS:
                    if needle in line:
                        raise SystemExit(f"STOP: {line}")
                if done(line):
                    return lines

    def close(self):
        if self.proc is None:
            return
        if self.proc.poll() is None:
            try:
                self.send("quit")
            except BrokenPipeError:
                pass
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        if self.err_path is not None:
            self.err_path.close()


def nodes_of(lines):
    last = None
    for line in lines:
        if line.startswith("info depth ") and " nodes " in line:
            last = line
    if last is None:
        raise SystemExit("STOP: no info depth line before bestmove")
    parts = last.split()
    idx = parts.index("nodes")
    return int(parts[idx + 1]), last


def main():
    if len(sys.argv) not in (4, 6):
        sys.exit("usage: o_run.py EXE FENS OUTSTEM [SWITCH true|false]")
    exe = str(Path(sys.argv[1]).resolve())
    fens = Path(sys.argv[2]).read_text(encoding="utf-8").splitlines()
    fens = [line.strip() for line in fens if line.strip()]
    outstem = Path(sys.argv[3])
    switch = None
    if len(sys.argv) == 6:
        if sys.argv[4] != "SWITCH":
            sys.exit("expected SWITCH true|false")
        switch = sys.argv[5]
        if switch not in ("true", "false"):
            sys.exit("switch value must be true or false")
    options = [f"setoption name {name} value {value}" for name, value in S14]
    if switch is not None:
        options.append(f"setoption name IdeaB8 value {switch}")
    engine = Engine(exe)
    transcript = []
    rows = []
    try:
        engine.start(str(outstem) + ".err")
        engine.send("uci")
        got = engine.read_until(lambda line: line == "uciok", 30)
        transcript.extend(got)
        id_name = next((line for line in got if line.startswith("id name ")), "")
        for option in options:
            engine.send(option)
            engine.send("isready")
            transcript.extend(engine.read_until(lambda line: line == "readyok", 30))
        for number, fen in enumerate(fens, 1):
            engine.send("ucinewgame")
            engine.send("isready")
            transcript.extend(engine.read_until(lambda line: line == "readyok", 30))
            engine.send(f"position fen {fen}")
            engine.send("isready")
            transcript.extend(engine.read_until(lambda line: line == "readyok", 30))
            engine.send("go depth 12")
            got = engine.read_until(lambda line: line.startswith("bestmove "), 180)
            transcript.extend(got)
            nodes, info = nodes_of(got)
            rows.append((number, nodes, info))
            if number % 20 == 0 or number == 1:
                print(f"{outstem.name} {number}/{len(fens)} nodes {nodes}", flush=True)
    finally:
        engine.close()
    outstem.parent.mkdir(parents=True, exist_ok=True)
    (Path(str(outstem) + ".txt")).write_text("\n".join(transcript) + "\n", encoding="utf-8")
    (Path(str(outstem) + ".rows")).write_text(
        "".join(f"{number}\t{nodes}\n" for number, nodes, _info in rows),
        encoding="utf-8",
    )
    (Path(str(outstem) + ".meta")).write_text(
        "\n".join(
            [
                f"exe: {exe}",
                f"sha256: {sha256_file(exe)}",
                f"id name: {id_name}",
                "options:",
                *options,
                f"positions: {len(rows)}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"wrote {len(rows)} rows sum {sum(nodes for _n, nodes, _i in rows)}", flush=True)


if __name__ == "__main__":
    main()
