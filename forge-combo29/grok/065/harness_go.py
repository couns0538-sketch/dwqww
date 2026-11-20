#!/usr/bin/env python3
"""One engine process. S14, then optional IdeaS15, then each FEN at a fixed depth.

After every setoption and every position the harness sends isready and reads
every line up to readyok. It stops on unknown option, invalid value, invalid
FEN, or illegal move. ucinewgame + isready before every go.
"""
import hashlib
import signal
import subprocess
import sys
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
]

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Stop(Exception):
    pass


class Engine:
    def __init__(self, exe: str):
        self.exe = exe
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.lines: list[str] = []

    def send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.lines.append(">> " + line)
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, done, timeout: float) -> list[str]:
        assert self.proc.stdout is not None
        got: list[str] = []

        def on_alarm(signum, frame):
            raise TimeoutError(f"timeout waiting after {self.lines[-1] if self.lines else '?'}")

        old = signal.signal(signal.SIGALRM, on_alarm)
        signal.alarm(max(1, int(timeout)))
        try:
            while True:
                raw = self.proc.stdout.readline()
                if raw == "":
                    raise Stop("engine closed stdout")
                line = raw.rstrip("\n")
                self.lines.append(line)
                got.append(line)
                for bad in BAD:
                    if bad in line:
                        raise Stop(line)
                if done(line):
                    return got
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old)

    def close(self) -> None:
        if self.proc.poll() is None:
            try:
                self.send("quit")
            except Exception:
                pass
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()


def fen_of(line: str) -> str:
    text = line.strip()
    if not text or text.startswith("#"):
        return ""
    parts = text.split()
    if len(parts) < 6:
        raise SystemExit(f"short FEN line: {text}")
    return " ".join(parts[:6])


def nodes_of(info: str) -> int:
    parts = info.split()
    return int(parts[parts.index("nodes") + 1])


def main() -> None:
    if len(sys.argv) not in (7, 8):
        raise SystemExit("usage: harness_go.py EXE FENS DEPTH OUT_PREFIX IDEA limit [OPTION]")
    exe, fen_path, depth_s, prefix, idea, limit_s = sys.argv[1:7]
    optname = sys.argv[7] if len(sys.argv) == 8 else "IdeaS15"
    depth = int(depth_s)
    limit = int(limit_s)
    fens = []
    for line in Path(fen_path).read_text().splitlines():
        fen = fen_of(line)
        if fen:
            fens.append(fen)
    if limit > 0:
        fens = fens[:limit]
    digest = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    eng = Engine(exe)
    options: list[str] = []
    try:
        eng.send("uci")
        id_lines = eng.read_until(lambda s: s == "uciok", 30)
        id_name = next((s for s in id_lines if s.startswith("id name ")), "")
        eng.send("isready")
        eng.read_until(lambda s: s == "readyok", 30)
        for name, value in [("Threads", "1"), ("Hash", "16"), *S14]:
            cmd = f"setoption name {name} value {value}"
            options.append(cmd)
            eng.send(cmd)
            eng.send("isready")
            eng.read_until(lambda s: s == "readyok", 30)
        if idea in ("true", "false"):
            cmd = f"setoption name {optname} value {idea}"
            options.append(cmd)
            eng.send(cmd)
            eng.send("isready")
            eng.read_until(lambda s: s == "readyok", 30)
        rows = []
        for index, fen in enumerate(fens, 1):
            eng.send("ucinewgame")
            eng.send("isready")
            eng.read_until(lambda s: s == "readyok", 60)
            eng.send(f"position fen {fen}")
            eng.send("isready")
            eng.read_until(lambda s: s == "readyok", 30)
            eng.send(f"go depth {depth}")
            got = eng.read_until(lambda s: s.startswith("bestmove "), 180)
            infos = [s for s in got if s.startswith("info depth ")]
            if not infos:
                raise Stop(f"no info depth before bestmove for fen {index}")
            rows.append((index, nodes_of(infos[-1]), got[-1], fen))
            if index % 50 == 0:
                print(f"{prefix} {index}/{len(fens)}", flush=True)
    finally:
        eng.close()
        Path(prefix + ".txt").write_text("\n".join(eng.lines) + "\n")
    meta = "\n".join(
        [
            f"exe={exe}",
            f"sha256={digest}",
            f"id_name={id_name}",
            f"depth={depth}",
            f"positions={len(rows)}",
            f"fen_file={fen_path}",
            "options:",
            *options,
            "",
        ]
    )
    Path(prefix + ".meta").write_text(meta)
    tsv = ["index\tnodes\tbestmove\tfen"]
    for index, nodes, best, fen in rows:
        tsv.append(f"{index}\t{nodes}\t{best}\t{fen}")
    Path(prefix + ".tsv").write_text("\n".join(tsv) + "\n")
    total = sum(nodes for _, nodes, _, _ in rows)
    print(f"SUM {prefix} {total} positions {len(rows)}")


if __name__ == "__main__":
    try:
        main()
    except Stop as exc:
        print(f"STOP {exc}", file=sys.stderr)
        raise SystemExit(2)
