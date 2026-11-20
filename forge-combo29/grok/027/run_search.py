#!/usr/bin/env python3
"""Measured fixed-depth searches.

One engine process. S14, then Hash 16 and Threads 1, each followed by isready.
Before every go: ucinewgame, isready, position, isready.
Stops on unknown option, invalid value, invalid FEN, or illegal move.
"""
import argparse
import hashlib
import os
import re
import select
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
STOP_PHRASES = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe: str):
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        self.log: list[str] = []
        self.pending: list[str] = []
        self.raw = b""
        if self.proc.stderr is not None:
            os.set_blocking(self.proc.stderr.fileno(), False)

    def send(self, line: str) -> None:
        self.log.append(">> " + line)
        assert self.proc.stdin is not None
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def read_line(self, timeout: float) -> str:
        assert self.proc.stdout is not None
        while not self.pending:
            ready, _, _ = select.select([self.proc.stdout], [], [], timeout)
            if not ready:
                raise TimeoutError(f"no output for {timeout}s")
            chunk = os.read(self.proc.stdout.fileno(), 1 << 20)
            if not chunk:
                err = b""
                if self.proc.stderr is not None:
                    err = os.read(self.proc.stderr.fileno(), 1 << 16)
                raise EOFError("engine closed stdout " + err.decode("utf-8", "replace"))
            self.raw += chunk
            while b"\n" in self.raw:
                blob, self.raw = self.raw.split(b"\n", 1)
                self.pending.append(blob.decode("utf-8", "replace").rstrip("\r"))
        line = self.pending.pop(0)
        self.log.append("<< " + line)
        for phrase in STOP_PHRASES:
            if phrase in line:
                raise RuntimeError(line)
        return line

    def until(self, prefix: str, timeout: float) -> None:
        while True:
            line = self.read_line(timeout)
            if line.startswith(prefix):
                return

    def close(self) -> None:
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()


def load_fens(path: Path) -> list[str]:
    fens = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 6:
            raise SystemExit(f"short fen line: {line}")
        fens.append(" ".join(parts[:6]))
    return fens


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--fens", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--idea", choices=("omit", "false", "true"), default="omit")
    parser.add_argument("--limit", type=int, default=0, help="use only the first N positions")
    args = parser.parse_args()
    exe = Path(args.exe).resolve()
    fens = load_fens(Path(args.fens))
    if args.limit:
        fens = fens[: args.limit]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    engine = Engine(str(exe))
    options: list[str] = []
    try:
        engine.send("uci")
        engine.until("uciok", 30)
        id_name = ""
        for line in engine.log:
            if line.startswith("<< id name "):
                id_name = line[len("<< id name ") :]
        for name, value in S14:
            sent = f"setoption name {name} value {value}"
            options.append(sent)
            engine.send(sent)
            engine.send("isready")
            engine.until("readyok", 30)
        for name, value in (("Hash", "16"), ("Threads", "1")):
            sent = f"setoption name {name} value {value}"
            options.append(sent)
            engine.send(sent)
            engine.send("isready")
            engine.until("readyok", 30)
        if args.idea != "omit":
            sent = f"setoption name IdeaS44 value {args.idea}"
            options.append(sent)
            engine.send(sent)
            engine.send("isready")
            engine.until("readyok", 30)
        rows = []
        for index, fen in enumerate(fens, start=1):
            engine.send("ucinewgame")
            engine.send("isready")
            engine.until("readyok", 30)
            engine.send(f"position fen {fen}")
            engine.send("isready")
            engine.until("readyok", 30)
            engine.send(f"go depth {args.depth}")
            nodes = None
            score = ""
            best = ""
            while True:
                line = engine.read_line(120)
                if line.startswith("info depth "):
                    match = re.search(r" nodes (\d+)", line)
                    if match:
                        nodes = int(match.group(1))
                    score_match = re.search(r" score (?:cp|mate) -?\d+", line)
                    if score_match:
                        score = score_match.group(0).strip()
                if line.startswith("bestmove "):
                    best = line.split()[1]
                    break
            if nodes is None or not best:
                raise RuntimeError(f"position {index} missing nodes or bestmove")
            rows.append((index, nodes, best, score, fen))
            print(f"{args.label} {index} {nodes} {best} {score}", flush=True)
    finally:
        log_path = out / f"{args.label}.txt"
        log_path.write_text("\n".join(engine.log) + "\n", encoding="utf-8")
        engine.close()
    tsv = out / f"{args.label}.nodes"
    tsv.write_text(
        "".join(f"{i}\t{nodes}\t{best}\t{score}\t{fen}\n" for i, nodes, best, score, fen in rows),
        encoding="utf-8",
    )
    total = sum(nodes for _, nodes, _, _, _ in rows)
    first3 = " / ".join(str(nodes) for _, nodes, _, _, _ in rows[:3])
    meta = (
        f"exe_started={exe}\n"
        f"sha256={sha256(exe)}\n"
        f"id_name={id_name}\n"
        f"depth={args.depth}\n"
        f"positions={len(rows)}\n"
        f"sum={total}\n"
        f"first3={first3}\n"
        "options_sent:\n"
        + "".join(f"  {line}\n" for line in options)
    )
    (out / f"{args.label}.meta").write_text(meta, encoding="utf-8")
    print(f"SUM {args.label} {total} first3 {first3} n={len(rows)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        raise
