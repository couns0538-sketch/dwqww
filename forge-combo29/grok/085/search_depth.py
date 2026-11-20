#!/usr/bin/env python3
"""Fixed-depth node count over a FEN list. S14, then Threads 1, Hash 16, then extra options.

Stops on unknown option, invalid value, invalid FEN, or illegal move.
Writes <prefix>.raw.txt, <prefix>.nodes.txt, <prefix>.sum.txt, and <prefix>.raw.txt.meta.
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
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class ProtocolError(RuntimeError):
    pass


def load_fens(path: Path) -> list[str]:
    fens = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fens.append(line)
    return fens


def last_nodes(lines: list[str]) -> int | None:
    found = None
    for line in lines:
        if " nodes " not in line:
            continue
        tail = line.split(" nodes ", 1)[1].split()
        if tail and tail[0].isdigit():
            found = int(tail[0])
    return found


def main() -> int:
    if len(sys.argv) < 5:
        print(
            "usage: search_depth.py EXE POSITIONS DEPTH PREFIX [Name=value ...]",
            file=sys.stderr,
        )
        return 2
    exe = Path(sys.argv[1]).resolve()
    positions = Path(sys.argv[2]).resolve()
    depth = int(sys.argv[3])
    prefix = Path(sys.argv[4]).resolve()
    extras = []
    for item in sys.argv[5:]:
        if "=" not in item:
            print("extra option must be Name=value", file=sys.stderr)
            return 2
        name, value = item.split("=", 1)
        extras.append((name, value))
    fens = load_fens(positions)
    sha = hashlib.sha256(exe.read_bytes()).hexdigest()
    option_lines = [f"setoption name {name} value {value}" for name, value in S14]
    option_lines.append("setoption name Threads value 1")
    option_lines.append("setoption name Hash value 16")
    option_lines.extend(f"setoption name {name} value {value}" for name, value in extras)

    proc = subprocess.Popen(
        [str(exe)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    lines_q: queue.Queue[str | None] = queue.Queue()

    def reader() -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            lines_q.put(line)
        lines_q.put(None)

    threading.Thread(target=reader, daemon=True).start()
    log: list[str] = []

    def send(line: str) -> None:
        assert proc.stdin is not None
        log.append(">> " + line)
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(marker: str, timeout: float) -> list[str]:
        deadline = time.monotonic() + timeout
        got: list[str] = []
        while time.monotonic() < deadline:
            try:
                line = lines_q.get(timeout=0.2)
            except queue.Empty:
                if proc.poll() is not None and lines_q.empty():
                    break
                continue
            if line is None:
                break
            line = line.rstrip("\n")
            log.append(line)
            for bad in BAD:
                if bad in line:
                    raise ProtocolError(line)
            got.append(line)
            if line == marker or line.startswith(marker + " "):
                return got
        raise ProtocolError(f"timeout waiting for {marker}")

    id_name = ""
    try:
        send("uci")
        uci_lines = read_until("uciok", 30)
        for line in uci_lines:
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
        for opt in option_lines:
            send(opt)
            send("isready")
            read_until("readyok", 30)
        rows = []
        for index, fen in enumerate(fens, start=1):
            send("ucinewgame")
            send("isready")
            read_until("readyok", 30)
            send("position fen " + fen)
            send("isready")
            read_until("readyok", 30)
            send(f"go depth {depth}")
            info = read_until("bestmove", 120)
            nodes = last_nodes(info)
            if nodes is None:
                raise ProtocolError(f"no nodes for position {index}")
            rows.append((index, nodes, fen))
            if index % 25 == 0 or index == len(fens):
                print(f"{index}/{len(fens)} nodes {nodes}", file=sys.stderr, flush=True)
        send("quit")
    except Exception:
        proc.kill()
        prefix.parent.mkdir(parents=True, exist_ok=True)
        prefix.with_name(prefix.name + ".raw.txt").write_text("\n".join(log) + "\n")
        raise
    else:
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()

    prefix.parent.mkdir(parents=True, exist_ok=True)
    raw_path = prefix.with_name(prefix.name + ".raw.txt")
    nodes_path = prefix.with_name(prefix.name + ".nodes.txt")
    sum_path = prefix.with_name(prefix.name + ".sum.txt")
    meta_path = prefix.with_name(prefix.name + ".raw.txt.meta")
    raw_path.write_text("\n".join(log) + "\n")
    node_lines = [f"{index} {nodes} {fen}" for index, nodes, fen in rows]
    nodes_path.write_text("\n".join(node_lines) + "\n")
    total = sum(nodes for _, nodes, _ in rows)
    first = " ".join(str(nodes) for _, nodes, _ in rows[:3])
    sum_text = f"positions {len(rows)}\nsum {total}\nfirst3 {first}\n"
    sum_path.write_text(sum_text)
    meta = (
        f"exe: {exe}\n"
        f"sha256: {sha}\n"
        f"id name: {id_name}\n"
        f"positions: {positions}\n"
        f"depth: {depth}\n"
        "options:\n"
        + "\n".join(option_lines)
        + "\n"
    )
    meta_path.write_text(meta)
    print(sum_text, end="")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ProtocolError as exc:
        print(f"STOP {exc}", file=sys.stderr)
        sys.exit(1)
