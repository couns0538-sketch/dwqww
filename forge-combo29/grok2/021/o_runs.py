#!/usr/bin/env python3
"""Depth-12 node counts on first200.fens. One engine process, S14 before every search."""
import hashlib
import select
import subprocess
import sys
import time
from pathlib import Path

S14 = [
    ("Threads", "1"),
    ("Hash", "16"),
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
STOP = ("unknown option", "invalid value", "invalid FEN", "illegal move")
OUT = Path(__file__).resolve().parent
FENS = Path.home() / "first200.fens"


class Engine:
    def __init__(self, path):
        self.path = path
        self.proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        self.pending = b""
        self.raw = []

    def send(self, line):
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def readline(self, timeout):
        deadline = time.time() + timeout
        while b"\n" not in self.pending:
            remain = deadline - time.time()
            if remain <= 0:
                raise TimeoutError(self.pending[:240])
            ready, _, _ = select.select([self.proc.stdout], [], [], remain)
            if not ready:
                raise TimeoutError(self.pending[:240])
            chunk = self.proc.stdout.read(65536)
            if chunk == b"":
                raise EOFError(self.pending[:240])
            self.pending += chunk
        line, self.pending = self.pending.split(b"\n", 1)
        text = line.decode("utf-8", "replace")
        self.raw.append(text)
        for bad in STOP:
            if bad in text:
                raise SystemExit(f"STOP {text}")
        return text

    def until(self, pred, timeout):
        got = []
        while True:
            line = self.readline(timeout)
            got.append(line)
            if pred(line):
                return got

    def close(self):
        try:
            self.send("quit")
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    tag, exe, switch = sys.argv[1], sys.argv[2], sys.argv[3]
    fens = FENS.read_text(encoding="utf-8").splitlines()
    if len(fens) != 200:
        raise SystemExit(f"expected 200 fens, got {len(fens)}")
    options = list(S14)
    if switch != "none":
        options.append(("IdeaB1", switch))
    eng = Engine(exe)
    try:
        eng.send("uci")
        hello = eng.until(lambda line: line == "uciok", 30)
        name = next((line[8:] for line in hello if line.startswith("id name ")), "")
        eng.send("isready")
        eng.until(lambda line: line == "readyok", 30)
        rows = []
        for i, fen in enumerate(fens, start=1):
            eng.send("ucinewgame")
            eng.send("isready")
            eng.until(lambda line: line == "readyok", 30)
            for opt, value in options:
                eng.send(f"setoption name {opt} value {value}")
                eng.send("isready")
                eng.until(lambda line: line == "readyok", 30)
            eng.send(f"position fen {fen}")
            eng.send("isready")
            eng.until(lambda line: line == "readyok", 30)
            eng.send("go depth 12")
            info = eng.until(lambda line: line.startswith("bestmove "), 180)
            last_info = ""
            nodes = None
            for line in info:
                if line.startswith("bestmove "):
                    break
                if line.startswith("info "):
                    last_info = line
            if " nodes " not in last_info:
                raise SystemExit(f"position {i} last info has no nodes: {last_info}")
            nodes = int(last_info.split(" nodes ", 1)[1].split()[0])
            rows.append((i, nodes))
            if i % 25 == 0:
                print(f"{tag} {i}/200", flush=True)
    finally:
        raw_path = OUT / f"o_{tag}.raw"
        raw_path.write_text("\n".join(eng.raw) + "\n", encoding="utf-8")
        eng.close()
    row_path = OUT / f"o_{tag}.rows"
    row_path.write_text("".join(f"{i}\t{n}\n" for i, n in rows), encoding="utf-8")
    meta = OUT / f"o_{tag}.meta"
    opt_lines = "\n".join(f"setoption name {opt} value {value}" for opt, value in options)
    meta.write_text(
        "\n".join([
            f"exe={exe}",
            f"sha256={sha256(exe)}",
            f"id_name={name}",
            "options:",
            opt_lines,
            "",
        ]),
        encoding="utf-8",
    )
    total = sum(n for _, n in rows)
    first = " / ".join(str(n) for _, n in rows[:3])
    print(f"{tag} positions {len(rows)} sum {total} first {first}")


if __name__ == "__main__":
    main()
