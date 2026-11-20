#!/usr/bin/env python3
"""Depth search over a FEN/EPD list. One engine process. S14, then Threads 1, Hash 16.

Switch:
  omit  do not send IdeaK7 (exe B does not have it)
  off   setoption IdeaK7 false
  on    setoption IdeaK7 true, then IdeaK7_Weight 100

Stops on unknown option, invalid value, invalid FEN, illegal move.
Writes <prefix>.raw.txt, <prefix>.tsv, <prefix>.meta.
"""
import argparse
import hashlib
import queue
import subprocess
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

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe: str):
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.q: queue.Queue[str | None] = queue.Queue()
        self.log: list[str] = []

        def reader() -> None:
            assert self.proc.stdout is not None
            for line in self.proc.stdout:
                self.q.put(line.rstrip("\n"))
            self.q.put(None)

        threading.Thread(target=reader, daemon=True).start()

    def send(self, line: str) -> None:
        self.log.append("> " + line)
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, marker: str, timeout: float) -> list[str]:
        deadline = time.monotonic() + timeout
        got: list[str] = []
        while time.monotonic() < deadline:
            try:
                line = self.q.get(timeout=0.2)
            except queue.Empty:
                continue
            if line is None:
                raise RuntimeError("engine exited before " + marker)
            self.log.append("< " + line)
            got.append(line)
            lowered = line.lower()
            for bad in BAD:
                if bad.lower() in lowered:
                    raise RuntimeError("STOP " + line)
            if line.startswith(marker):
                return got
        raise TimeoutError("timeout waiting for " + marker)

    def close(self) -> None:
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()


def fen_of(line: str) -> str:
    parts = line.split()
    if len(parts) < 4:
        raise RuntimeError("short fen line: " + line)
    if len(parts) >= 6:
        return " ".join(parts[:6])
    return " ".join(parts)


def nodes_and_move(lines: list[str]) -> tuple[int, str]:
    nodes = None
    move = ""
    for line in lines:
        parts = line.split()
        for i, token in enumerate(parts):
            if token == "nodes" and i + 1 < len(parts):
                nodes = int(parts[i + 1])
        if line.startswith("bestmove "):
            move = parts[1] if len(parts) > 1 else ""
    if nodes is None:
        raise RuntimeError("no nodes in search output")
    return nodes, move


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--fens", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--switch", choices=("omit", "off", "on"), required=True)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    exe = str(Path(args.exe).resolve())
    digest = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    fens = []
    for raw in Path(args.fens).read_text().splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        fens.append(fen_of(raw))
    if args.limit:
        fens = fens[: args.limit]
    options: list[tuple[str, str]] = [("Threads", "1"), ("Hash", "16"), *S14]
    if args.switch == "off":
        options.append(("IdeaK7", "false"))
    elif args.switch == "on":
        options.append(("IdeaK7", "true"))
        options.append(("IdeaK7_Weight", "100"))
    eng = Engine(exe)
    id_name = ""
    try:
        eng.send("uci")
        uci_lines = eng.read_until("uciok", 30)
        for line in uci_lines:
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
        for name, value in options:
            eng.send(f"setoption name {name} value {value}")
            eng.send("isready")
            eng.read_until("readyok", 30)
        rows = []
        for index, fen in enumerate(fens, start=1):
            eng.send("ucinewgame")
            eng.send("isready")
            eng.read_until("readyok", 30)
            eng.send("position fen " + fen)
            eng.send("isready")
            eng.read_until("readyok", 60)
            eng.send(f"go depth {args.depth}")
            got = eng.read_until("bestmove", 180)
            nodes, move = nodes_and_move(got)
            rows.append((index, nodes, move, fen))
            if index % 50 == 0:
                print(f"progress {index} {nodes}", flush=True)
    finally:
        prefix = Path(args.prefix)
        prefix.parent.mkdir(parents=True, exist_ok=True)
        (prefix.parent / (prefix.name + ".raw.txt")).write_text("\n".join(eng.log) + "\n")
        eng.close()
    tsv = ["index\tnodes\tbestmove\tfen"]
    for index, nodes, move, fen in rows:
        tsv.append(f"{index}\t{nodes}\t{move}\t{fen}")
    (prefix.parent / (prefix.name + ".tsv")).write_text("\n".join(tsv) + "\n")
    opt_lines = "\n".join(f"setoption name {name} value {value}" for name, value in options)
    meta = (
        f"exe={exe}\nsha256={digest}\nid_name={id_name}\n"
        f"depth={args.depth}\nswitch={args.switch}\npositions={len(rows)}\n"
        f"options:\n{opt_lines}\n"
    )
    (prefix.parent / (prefix.name + ".meta")).write_text(meta)
    total = sum(nodes for _, nodes, _, _ in rows)
    print(f"positions {len(rows)} sum {total}")


if __name__ == "__main__":
    main()
