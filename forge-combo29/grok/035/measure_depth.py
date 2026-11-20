#!/usr/bin/env python3
"""Fixed-depth node counter. One engine process. isready after every setoption and position."""
import hashlib
import subprocess
import sys
from pathlib import Path

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def load_fens(path: Path):
    fens = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 4:
            raise SystemExit(f"short fen line: {line}")
        # EPD may carry opcodes after the six FEN fields.
        fen = " ".join(parts[:6]) if len(parts) >= 6 else " ".join(parts)
        fens.append(fen)
    return fens


class Engine:
    def __init__(self, exe: str, log_path: Path):
        self.exe = exe
        self.log_path = log_path
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.lines = []

    def send(self, line: str):
        self.lines.append(">> " + line)
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, done):
        assert self.proc.stdout is not None
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                self.flush()
                raise SystemExit("engine closed stdout")
            line = line.rstrip("\r\n")
            self.lines.append(line)
            low = line.lower()
            for bad in BAD:
                if bad.lower() in low:
                    self.flush()
                    raise SystemExit(f"STOP {bad}: {line}")
            if done(line):
                return line

    def ready(self):
        self.send("isready")
        self.read_until(lambda line: line == "readyok")

    def flush(self):
        self.log_path.write_text("\n".join(self.lines) + "\n")

    def close(self):
        if self.proc.poll() is None:
            try:
                self.send("quit")
            except BrokenPipeError:
                pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        self.flush()


def main():
    if len(sys.argv) < 6:
        raise SystemExit("usage: measure_depth.py EXE FENS DEPTH OUT_PREFIX OPTFILE")
    exe, fen_path, depth_s, out_prefix, opt_path = sys.argv[1:6]
    depth = int(depth_s)
    fens = load_fens(Path(fen_path))
    options = [line.strip() for line in Path(opt_path).read_text().splitlines() if line.strip()]
    prefix = Path(out_prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    raw = Path(str(prefix) + ".raw")
    nodes_path = Path(str(prefix) + ".nodes")
    meta_path = Path(str(prefix) + ".meta")
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    eng = Engine(exe, raw)
    try:
        eng.send("uci")
        id_line = eng.read_until(lambda line: line == "uciok")
        id_name = next(line for line in eng.lines if line.startswith("id name "))
        for opt in options:
            eng.send("setoption name " + opt)
            eng.ready()
        rows = []
        for index, fen in enumerate(fens, start=1):
            eng.send("ucinewgame")
            eng.ready()
            eng.send("position fen " + fen)
            eng.ready()
            eng.send(f"go depth {depth}")
            last_nodes = None
            while True:
                line = eng.read_until(lambda item: item.startswith("bestmove ") or " nodes " in item)
                if line.startswith("bestmove "):
                    break
                parts = line.split()
                if "nodes" in parts:
                    last_nodes = parts[parts.index("nodes") + 1]
            if last_nodes is None:
                eng.flush()
                raise SystemExit(f"no nodes for position {index}")
            rows.append((index, last_nodes, fen))
            if index % 25 == 0:
                print(f"progress {index}/{len(fens)}", flush=True)
        nodes_path.write_text("".join(f"{i}\t{n}\t{fen}\n" for i, n, fen in rows))
        total = sum(int(n) for _, n, _ in rows)
        meta = [
            f"exe {exe}",
            f"sha256 {sha}",
            id_name,
            f"depth {depth}",
            f"positions {len(fens)}",
            f"fenfile {fen_path}",
            "options:",
            *[f"setoption name {opt}" for opt in options],
            f"nodes_sum {total}",
            f"uciok_seen {id_line == 'uciok'}",
        ]
        meta_path.write_text("\n".join(meta) + "\n")
        print(f"SUM {total} POS {len(rows)}")
        if rows:
            print("FIRST", " ".join(n for _, n, _ in rows[:3]))
    finally:
        eng.close()


if __name__ == "__main__":
    main()
