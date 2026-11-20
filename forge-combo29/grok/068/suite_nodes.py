#!/usr/bin/env python3
"""Fixed-depth node rows. One process. S14, then Threads 1, Hash 16.
ucinewgame + isready before every go. isready after every setoption and position.
Stops on unknown option, invalid value, invalid FEN, illegal move.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

STOP_MARKERS = ("unknown option", "invalid value", "invalid FEN", "illegal move")
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


class Engine:
    def __init__(self, exe: Path, err_path: Path) -> None:
        self.exe = exe
        self.err_handle = err_path.open("w")
        self.proc = subprocess.Popen(
            [str(exe)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=self.err_handle,
            text=True,
            bufsize=1,
        )
        self.log: list[str] = []
        self.options_sent: list[str] = []

    def send(self, line: str) -> None:
        self.log.append(">> " + line)
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, done) -> list[str]:
        assert self.proc.stdout is not None
        lines: list[str] = []
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                raise SystemExit("engine closed stdout\n" + "\n".join(self.log[-30:]))
            line = line.rstrip("\r\n")
            self.log.append(line)
            lines.append(line)
            low = line.lower()
            for marker in STOP_MARKERS:
                if marker.lower() in low:
                    raise SystemExit(f"STOP {marker}: {line}")
            if done(line):
                return lines

    def ready(self) -> None:
        self.send("isready")
        self.read_until(lambda text: text == "readyok")

    def setoption(self, name: str, value: str) -> None:
        command = f"setoption name {name} value {value}"
        self.send(command)
        self.options_sent.append(command)
        self.ready()

    def close(self) -> None:
        try:
            self.send("quit")
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()
        self.err_handle.close()


def fen_of(line: str) -> str:
    text = line.strip()
    if not text or text.startswith("#"):
        return ""
    return text.split(";")[0].strip()


def last_info(lines: list[str]) -> tuple[str, str]:
    depth = "MISSING"
    nodes = "MISSING"
    for line in lines:
        if not line.startswith("info ") or " nodes " not in line or " depth " not in line:
            continue
        parts = line.split()
        if "depth" in parts and "nodes" in parts:
            depth = parts[parts.index("depth") + 1]
            nodes = parts[parts.index("nodes") + 1]
    return depth, nodes


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    if len(sys.argv) != 6:
        print("usage: suite_nodes.py EXE FENS DEPTH OUTSTEM EXTRA_SETOPTIONS", file=sys.stderr)
        print("EXTRA_SETOPTIONS is a file of 'name value' lines, or - for none", file=sys.stderr)
        return 2
    exe = Path(sys.argv[1]).resolve()
    fens = Path(sys.argv[2]).resolve()
    depth = int(sys.argv[3])
    out_stem = Path(sys.argv[4]).resolve()
    extra_path = sys.argv[5]
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    positions = [fen_of(line) for line in fens.read_text().splitlines()]
    positions = [fen for fen in positions if fen]
    engine = Engine(exe, Path(str(out_stem) + ".stderr"))
    try:
        engine.send("uci")
        uci_lines = engine.read_until(lambda text: text == "uciok")
        name = ""
        for line in uci_lines:
            if line.startswith("id name "):
                name = line[len("id name ") :]
        for opt_name, opt_value in S14:
            engine.setoption(opt_name, opt_value)
        if extra_path != "-":
            for raw in Path(extra_path).read_text().splitlines():
                text = raw.strip()
                if not text or text.startswith("#"):
                    continue
                opt_name, opt_value = text.split(None, 1)
                engine.setoption(opt_name, opt_value)
        rows: list[str] = []
        total = 0
        for index, fen in enumerate(positions, start=1):
            engine.send("ucinewgame")
            engine.ready()
            engine.send("position fen " + fen)
            engine.ready()
            engine.send(f"go depth {depth}")
            played = engine.read_until(lambda text: text.startswith("bestmove "))
            got_depth, nodes = last_info(played)
            if got_depth != str(depth) or not nodes.isdigit():
                raise SystemExit(
                    f"STOP bad search result fen {index} depth {got_depth} nodes {nodes}"
                )
            total += int(nodes)
            rows.append(f"{index} {nodes} {got_depth} {fen}")
            if index % 25 == 0:
                print(f"{index} sum {total}", flush=True)
    finally:
        log_path = Path(str(out_stem) + ".log")
        log_path.write_text("\n".join(engine.log) + "\n")
        engine.close()
    raw_path = Path(str(out_stem) + ".txt")
    raw_path.write_text("\n".join(rows) + f"\nSUM {total}\n")
    meta = [
        f"exe {exe}",
        f"sha256 {sha256(exe)}",
        f"id_name {name}",
        f"fens {fens}",
        f"depth {depth}",
        f"positions {len(positions)}",
        f"sum {total}",
        "options_sent",
        *engine.options_sent,
    ]
    Path(str(out_stem) + ".meta").write_text("\n".join(meta) + "\n")
    print(f"SUM {total} positions {len(positions)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
