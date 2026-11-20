#!/usr/bin/env python3
"""Fixed-depth node sum. One engine process. S14, then optional extra options.

Stops on unknown option, invalid value, invalid FEN, or illegal move.
Writes the full transcript, a .meta, and a nodes TSV (index, nodes, fen).
"""
import hashlib
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
    ("Threads", "1"),
    ("Hash", "16"),
]

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fen_of(line: str) -> str:
    text = line.strip()
    if not text or text.startswith("#"):
        return ""
    # EPD may append opcodes after six FEN fields.
    parts = text.split()
    if len(parts) >= 6:
        return " ".join(parts[:6])
    return text


class Engine:
    def __init__(self, exe: Path):
        self.proc = subprocess.Popen(
            [str(exe)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.transcript = []
        self.sent = []

    def send(self, cmd: str) -> None:
        self.sent.append(cmd)
        self.transcript.append(">> " + cmd + "\n")
        assert self.proc.stdin is not None
        self.proc.stdin.write(cmd + "\n")
        self.proc.stdin.flush()

    def read_until(self, pred, limit=100000):
        assert self.proc.stdout is not None
        got = []
        while len(got) < limit:
            line = self.proc.stdout.readline()
            if line == "":
                break
            self.transcript.append(line)
            got.append(line)
            lowered = line.lower()
            for bad in BAD:
                if bad.lower() in lowered:
                    raise SystemExit(f"STOP {bad}: {line.rstrip()}")
            if pred(line):
                break
        else:
            raise SystemExit("STOP no reply")
        return got

    def close(self) -> None:
        try:
            self.send("quit")
        except BrokenPipeError:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def main() -> int:
    if len(sys.argv) < 5:
        print("usage: search_set.py EXE FENS DEPTH OUT_PREFIX [Name=value ...]", file=sys.stderr)
        return 2
    exe = Path(sys.argv[1]).resolve()
    fens_path = Path(sys.argv[2]).resolve()
    depth = int(sys.argv[3])
    out_prefix = Path(sys.argv[4]).resolve()
    extra = []
    for item in sys.argv[5:]:
        name, value = item.split("=", 1)
        extra.append((name, value))
    fens = [fen_of(line) for line in fens_path.read_text().splitlines()]
    fens = [fen for fen in fens if fen]
    eng = Engine(exe)
    eng.send("uci")
    uci_lines = eng.read_until(lambda s: s.startswith("uciok"))
    id_name = ""
    for line in uci_lines:
        if line.startswith("id name "):
            id_name = line[len("id name ") :].rstrip("\n")
    eng.send("isready")
    eng.read_until(lambda s: s.startswith("readyok"))
    for name, value in S14 + extra:
        eng.send(f"setoption name {name} value {value}")
        eng.send("isready")
        eng.read_until(lambda s: s.startswith("readyok"))
    rows = []
    for index, fen in enumerate(fens, start=1):
        eng.send("ucinewgame")
        eng.send("isready")
        eng.read_until(lambda s: s.startswith("readyok"))
        eng.send(f"position fen {fen}")
        eng.send("isready")
        eng.read_until(lambda s: s.startswith("readyok"))
        eng.send(f"go depth {depth}")
        chunk = eng.read_until(lambda s: s.startswith("bestmove "))
        nodes = None
        for line in chunk:
            if " nodes " in line and line.startswith("info "):
                parts = line.split()
                nodes = int(parts[parts.index("nodes") + 1])
        if nodes is None:
            raise SystemExit(f"STOP no nodes for position {index}")
        rows.append((index, nodes, fen))
        if index % 50 == 0:
            print(f"{index} {nodes}", flush=True)
    eng.close()
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    out_prefix.with_suffix(".txt").write_text("".join(eng.transcript))
    tsv = out_prefix.with_suffix(".tsv")
    tsv.write_text("".join(f"{i}\t{n}\t{fen}\n" for i, n, fen in rows))
    total = sum(n for _, n, _ in rows)
    meta = Path(str(out_prefix) + ".meta")
    meta.write_text(
        "\n".join(
            [
                f"exe={exe}",
                f"sha256={sha256(exe)}",
                f"id_name={id_name}",
                "options_sent:",
                *[c for c in eng.sent if c.startswith("setoption ")],
                f"depth={depth}",
                f"positions={len(rows)}",
                f"sum={total}",
                f"first3={' / '.join(str(n) for _, n, _ in rows[:3])}",
                f"fens={fens_path}",
                "",
            ]
        )
    )
    print(f"sum {total} first3 {' / '.join(str(n) for _, n, _ in rows[:3])} n {len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
