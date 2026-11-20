#!/usr/bin/env python3
"""One engine process. S14, Threads 1, Hash 16. ucinewgame + isready before every go.
Stops on unknown option, invalid value, invalid FEN, illegal move.
Last info-line nodes of each search are written, one per position.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

STOP = ("unknown option", "invalid value", "invalid fen", "illegal move")
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


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_fens(path: Path) -> list[str]:
    fens = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # EPD may carry an opcode after the 6 FEN fields.
        parts = line.split()
        if len(parts) < 4:
            raise SystemExit(f"bad fen line: {line}")
        fens.append(" ".join(parts[:6]) if len(parts) >= 6 else line)
    return fens


class Engine:
    def __init__(self, exe: Path, raw):
        self.proc = subprocess.Popen(
            [str(exe)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.raw = raw

    def send(self, line: str) -> None:
        self.raw.write(">> " + line + "\n")
        self.raw.flush()
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, predicate) -> list[str]:
        assert self.proc.stdout is not None
        got = []
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                self.raw.write("# EOF\n")
                raise SystemExit("engine closed stdout")
            self.raw.write(line)
            self.raw.flush()
            stripped = line.strip()
            low = stripped.lower()
            for token in STOP:
                if token in low:
                    raise SystemExit(f"STOP {stripped}")
            got.append(stripped)
            if predicate(stripped):
                return got

    def ready(self) -> None:
        self.send("isready")
        self.read_until(lambda s: s == "readyok")

    def close(self) -> None:
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def nodes_of(lines: list[str]) -> int:
    nodes = None
    for line in lines:
        if line.startswith("info depth ") and " nodes " in line:
            parts = line.split()
            nodes = int(parts[parts.index("nodes") + 1])
    if nodes is None:
        raise SystemExit("no info nodes before bestmove")
    return nodes


def main() -> None:
    exe = Path(sys.argv[1])
    fen_path = Path(sys.argv[2])
    depth = int(sys.argv[3])
    raw_path = Path(sys.argv[4])
    meta_path = Path(sys.argv[5])
    nodes_path = Path(sys.argv[6])
    fens = load_fens(fen_path)
    id_name = "MISSING"
    probe = subprocess.run([str(exe)], input="uci\nquit\n", text=True, capture_output=True, check=False)
    for line in probe.stdout.splitlines():
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
            break
    option_lines = [f"setoption name {n} value {v}" for n, v in S14]
    meta_path.write_text(
        f"exe={exe}\n"
        f"sha256={sha256(exe)}\n"
        f"id_name={id_name}\n"
        f"depth={depth}\n"
        f"fen_file={fen_path}\n"
        f"positions={len(fens)}\n"
        + "".join(f"option={line}\n" for line in option_lines)
    )
    nodes = []
    with raw_path.open("w") as raw:
        eng = Engine(exe, raw)
        try:
            for line in option_lines:
                eng.send(line)
                eng.ready()
            for index, fen in enumerate(fens):
                eng.send("ucinewgame")
                eng.ready()
                eng.send(f"position fen {fen}")
                eng.ready()
                eng.send(f"go depth {depth}")
                lines = eng.read_until(lambda s: s.startswith("bestmove "))
                count = nodes_of(lines)
                nodes.append(count)
                if index < 3 or index + 1 == len(fens):
                    print(f"{index + 1} {count} running {sum(nodes)}", flush=True)
        finally:
            eng.close()
    nodes_path.write_text("".join(f"{n}\n" for n in nodes))
    print(f"SUM {sum(nodes)} N {len(nodes)}", flush=True)


if __name__ == "__main__":
    main()
