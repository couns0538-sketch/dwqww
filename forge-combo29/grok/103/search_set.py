#!/usr/bin/env python3
"""Depth search of a FEN/EPD list. One process, ucinewgame before every go.

Stops if the engine reports an unknown option, an invalid value, an invalid FEN,
or an illegal move. Writes the full transcript, a .meta, and one nodes line per
position parsed from that transcript.
"""
import hashlib
import queue
import subprocess
import sys
import threading
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
]

STOP_PHRASES = ("unknown option", "invalid value", "invalid fen", "illegal move")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fen_of(line: str) -> str:
    parts = line.split()
    if len(parts) < 6:
        raise SystemExit(f"short FEN line: {line!r}")
    return " ".join(parts[:6])


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
        self.q = queue.Queue()
        self.transcript = []
        self.bad = None
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self.transcript.append(line)
            lowered = line.lower()
            for phrase in STOP_PHRASES:
                if phrase in lowered:
                    self.bad = line.rstrip("\n")
            self.q.put(line)
        self.q.put(None)

    def send(self, line: str):
        if self.bad:
            raise SystemExit(f"STOP {self.bad}")
        assert self.proc.stdin is not None
        self.transcript.append(">> " + line + "\n")
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def wait_for(self, predicate, timeout: float):
        deadline = time.time() + timeout
        got = []
        while time.time() < deadline:
            if self.bad:
                raise SystemExit(f"STOP {self.bad}")
            remaining = deadline - time.time()
            try:
                line = self.q.get(timeout=min(1.0, max(0.1, remaining)))
            except queue.Empty:
                if self.proc.poll() is not None:
                    raise SystemExit("engine exited")
                continue
            if line is None:
                raise SystemExit("engine closed stdout")
            got.append(line)
            if predicate(line):
                return got
        raise SystemExit(f"timeout waiting after {got[-1].rstrip() if got else 'no output'}")

    def close(self):
        try:
            if self.proc.poll() is None and self.proc.stdin is not None:
                self.proc.stdin.write("quit\n")
                self.proc.stdin.flush()
        except (BrokenPipeError, OSError, SystemExit):
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def nodes_of(lines):
    found = None
    for line in lines:
        if " nodes " in line and line.startswith("info "):
            parts = line.split()
            if "nodes" in parts:
                found = int(parts[parts.index("nodes") + 1])
    if found is None:
        raise SystemExit("no nodes on info line")
    return found


def main() -> int:
    if len(sys.argv) < 5:
        print("usage: search_set.py EXE FENS DEPTH OUT_PREFIX [extra setoption lines...]", file=sys.stderr)
        return 2
    exe = Path(sys.argv[1]).resolve()
    fens = [fen_of(line.strip()) for line in Path(sys.argv[2]).read_text().splitlines() if line.strip()]
    depth = int(sys.argv[3])
    prefix = Path(sys.argv[4])
    extras = sys.argv[5:]
    digest = sha256_file(exe)
    engine = Engine(exe)
    option_lines = []
    id_name = ""
    rows = []
    try:
        engine.send("uci")
        prelude = engine.wait_for(lambda line: line.strip() == "uciok", 30)
        for line in prelude:
            if line.startswith("id name "):
                id_name = line[len("id name "):].rstrip("\n")
        engine.send("setoption name Threads value 1")
        option_lines.append("setoption name Threads value 1")
        engine.send("isready")
        engine.wait_for(lambda line: line.strip() == "readyok", 30)
        engine.send("setoption name Hash value 16")
        option_lines.append("setoption name Hash value 16")
        engine.send("isready")
        engine.wait_for(lambda line: line.strip() == "readyok", 30)
        for name, value in S14:
            sent = f"setoption name {name} value {value}"
            engine.send(sent)
            option_lines.append(sent)
            engine.send("isready")
            engine.wait_for(lambda line: line.strip() == "readyok", 30)
        for extra in extras:
            engine.send(extra)
            option_lines.append(extra)
            engine.send("isready")
            engine.wait_for(lambda line: line.strip() == "readyok", 30)
        rows = []
        for index, fen in enumerate(fens, start=1):
            engine.send("ucinewgame")
            engine.send("isready")
            engine.wait_for(lambda line: line.strip() == "readyok", 60)
            engine.send(f"position fen {fen}")
            engine.send("isready")
            engine.wait_for(lambda line: line.strip() == "readyok", 60)
            engine.send(f"go depth {depth}")
            body = engine.wait_for(lambda line: line.startswith("bestmove "), 180)
            rows.append(nodes_of(body))
            if index % 25 == 0 or index == len(fens):
                print(f"{index}/{len(fens)} nodes {rows[-1]} sum {sum(rows)}", flush=True)
    finally:
        raw = "".join(engine.transcript)
        prefix.parent.mkdir(parents=True, exist_ok=True)
        prefix.with_suffix(".txt").write_text(raw)
        meta = (
            f"exe={exe}\n"
            f"sha256={digest}\n"
            f"id_name={id_name}\n"
            f"depth={depth}\n"
            f"positions={len(fens)}\n"
            f"fen_file={Path(sys.argv[2]).resolve()}\n"
            "options:\n" + "".join(line + "\n" for line in option_lines)
        )
        Path(str(prefix) + ".meta").write_text(meta)
        if rows:
            Path(str(prefix) + ".nodes").write_text("\n".join(str(n) for n in rows) + "\n")
            print(f"SUM {sum(rows)} COUNT {len(rows)} FIRST {rows[:3]}", flush=True)
        engine.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
