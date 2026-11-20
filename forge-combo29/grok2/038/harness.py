#!/usr/bin/env python3
"""UCI harness for grok2 seat 038 arm 8. Writes raw engine stdout and a .meta beside it.

Honesty: one fresh process per command, no setoption.
O runs: Threads 1, Hash 16, S14 in the brief's order, then the switch, then
ucinewgame + isready and position + isready before every go depth 12.
Stops on unknown option, invalid value, invalid FEN, or illegal move.
"""
import hashlib
import selectors
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FENS = Path.home() / "first200.fens"
EXE_B = Path("/tmp/forge-build/base/forge")
EXE_P = Path("/tmp/forge-build/work/forge")
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


class Stop(Exception):
    pass


class Engine:
    def __init__(self, exe: Path):
        self.exe = exe
        self.lines: list[str] = []
        self.options_sent: list[str] = []
        self.id_name = ""
        self.pending = b""
        self.proc = subprocess.Popen(
            [str(exe)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )

    def send(self, cmd: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write((cmd + "\n").encode())
        self.proc.stdin.flush()

    def read_until(self, pred, timeout: float) -> str:
        assert self.proc.stdout is not None
        sel = selectors.DefaultSelector()
        sel.register(self.proc.stdout, selectors.EVENT_READ)
        try:
            while True:
                while b"\n" in self.pending:
                    raw, self.pending = self.pending.split(b"\n", 1)
                    line = raw.decode("utf-8", "replace").rstrip("\r")
                    self.lines.append(line)
                    for phrase in STOP_PHRASES:
                        if phrase in line:
                            raise Stop(line)
                    if pred(line):
                        return line
                events = sel.select(timeout)
                if not events:
                    raise Stop(f"timeout after {timeout}s, last line: {self.lines[-1] if self.lines else '<none>'}")
                chunk = self.proc.stdout.read1(65536) if hasattr(self.proc.stdout, "read1") else self.proc.stdout.read(65536)
                if chunk == b"":
                    raise Stop("engine closed stdout")
                self.pending += chunk
        finally:
            sel.close()

    def uci(self) -> None:
        self.send("uci")
        self.read_until(lambda line: line == "uciok", 30)
        for line in self.lines:
            if line.startswith("id name "):
                self.id_name = line[len("id name ") :]

    def isready(self) -> None:
        self.send("isready")
        self.read_until(lambda line: line == "readyok", 60)

    def setoption(self, name: str, value: str) -> None:
        cmd = f"setoption name {name} value {value}"
        self.options_sent.append(cmd)
        self.send(cmd)
        self.isready()

    def close(self) -> None:
        if self.proc.poll() is None:
            try:
                self.send("quit")
            except BrokenPipeError:
                pass
            try:
                self.proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=10)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_pair(stem: str, engine: Engine) -> None:
    raw = HERE / f"{stem}.txt"
    meta = HERE / f"{stem}.meta"
    raw.write_text("\n".join(engine.lines) + "\n", encoding="utf-8")
    option_text = "\n".join(engine.options_sent) if engine.options_sent else "(none)"
    meta.write_text(
        "\n".join(
            [
                f"exe: {engine.exe}",
                f"sha256: {sha256_file(engine.exe)}",
                f"id name: {engine.id_name}",
                "options:",
                option_text,
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"wrote {raw.name} lines={len(engine.lines)} id={engine.id_name}")


def honesty_one(label: str, exe: Path, command: str, done) -> None:
    engine = Engine(exe)
    try:
        engine.uci()
        engine.send(command)
        engine.read_until(done, 300)
        write_pair(label, engine)
    finally:
        engine.close()


def honesty() -> None:
    jobs = [
        ("bench11", "bench 11", lambda line: line.startswith("info string bench depth 11 ")),
        ("bench13", "bench 13", lambda line: line.startswith("info string bench depth 13 ")),
        ("bench16", "bench 16", lambda line: line.startswith("info string bench depth 16 ")),
        ("perft5", "go perft 5", lambda line: line.startswith("nodes ")),
    ]
    which = sys.argv[2] if len(sys.argv) > 2 else "all"
    targets = [("B", EXE_B), ("P", EXE_P)]
    if which != "all":
        targets = [t for t in targets if t[0] == which]
        if not targets:
            raise SystemExit(f"unknown honesty target {which}")
    for tag, exe in targets:
        for stem, command, done in jobs:
            print(f"honesty {tag} {command}", flush=True)
            honesty_one(f"honesty_{tag}_{stem}", exe, command, done)


def orun(kind: str) -> None:
    if kind == "B":
        exe = EXE_B
        switch = None
        stem = "o_B"
    elif kind == "off":
        exe = EXE_P
        switch = "false"
        stem = "o_P_off"
    elif kind == "on":
        exe = EXE_P
        switch = "true"
        stem = "o_P_on"
    else:
        raise SystemExit(f"unknown orun {kind}")
    fens = [line.strip() for line in FENS.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(fens) != 200:
        raise SystemExit(f"expected 200 fens, got {len(fens)}")
    engine = Engine(exe)
    try:
        engine.uci()
        engine.isready()
        engine.setoption("Threads", "1")
        engine.setoption("Hash", "16")
        for name, value in S14:
            engine.setoption(name, value)
        if switch is not None:
            engine.setoption("IdeaK4", switch)
        for index, fen in enumerate(fens, start=1):
            engine.send("ucinewgame")
            engine.isready()
            engine.send(f"position fen {fen}")
            engine.isready()
            engine.send("go depth 12")
            engine.read_until(lambda line: line.startswith("bestmove "), 180)
            if index % 20 == 0:
                print(f"{stem} {index}/200", flush=True)
        write_pair(stem, engine)
    finally:
        engine.close()


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: harness.py honesty [B|P] | harness.py orun B|off|on")
    cmd = sys.argv[1]
    if cmd == "honesty":
        honesty()
    elif cmd == "orun":
        orun(sys.argv[2])
    else:
        raise SystemExit(f"unknown command {cmd}")


if __name__ == "__main__":
    try:
        main()
    except Stop as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        sys.exit(1)
