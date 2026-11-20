#!/usr/bin/env python3
"""Depth-sum harness. Reads every line up to readyok or bestmove. Stops on engine errors."""

import argparse
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

STOP_BITS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe: str) -> None:
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.lines: queue.Queue[str | None] = queue.Queue()
        self.thread = threading.Thread(target=self._pump, daemon=True)
        self.thread.start()

    def _pump(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self.lines.put(line.rstrip("\n"))
        self.lines.put(None)

    def send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, marker: str, timeout: float) -> list[str]:
        collected: list[str] = []
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"timeout waiting for {marker}; tail={collected[-5:]}")
            try:
                line = self.lines.get(timeout=remaining)
            except queue.Empty as exc:
                raise TimeoutError(f"timeout waiting for {marker}") from exc
            if line is None:
                self.last_read = collected
                raise RuntimeError(f"engine exited waiting for {marker}; tail={collected[-8:]}")
            collected.append(line)
            lowered = line.lower()
            for bit in STOP_BITS:
                if bit.lower() in lowered:
                    raise RuntimeError(f"STOP {bit}: {line}")
            if marker == "bestmove" and line.startswith("bestmove "):
                self.last_read = collected
                return collected
            if marker != "bestmove" and line == marker:
                self.last_read = collected
                return collected

    def close(self) -> None:
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_fens(path: Path, limit: int) -> list[str]:
    fens = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 6:
            raise SystemExit(f"short fen line: {line}")
        fens.append(" ".join(parts[:6]))
        if limit and len(fens) >= limit:
            break
    return fens


def nodes_of(info_lines: list[str]) -> int:
    found = None
    for line in info_lines:
        parts = line.split()
        if "nodes" not in parts:
            continue
        index = parts.index("nodes")
        if index + 1 < len(parts) and parts[index + 1].isdigit():
            found = int(parts[index + 1])
    if found is None:
        raise RuntimeError(f"no nodes in {info_lines[-6:]}")
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--fens", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--idea", choices=("omit", "false", "true"), default="omit")
    parser.add_argument("--divisor", type=int, default=64)
    parser.add_argument("--history-depth", type=int, default=5)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--go-nodes", type=int, default=0)
    args = parser.parse_args()

    exe = Path(args.exe).resolve()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    fens = load_fens(Path(args.fens), args.limit)
    digest = sha256(exe)
    engine = Engine(str(exe))
    engine.last_read = []
    raw: list[str] = []
    options_sent: list[str] = []
    id_name = ""
    counts: list[int] = []
    error: BaseException | None = None
    try:
        engine.send("uci")
        raw += engine.read_until("uciok", 30)
        for line in raw:
            if line.startswith("id name "):
                id_name = line[len("id name ") :]

        def setoption(name: str, value: str) -> None:
            command = f"setoption name {name} value {value}"
            options_sent.append(command)
            raw.append(">> " + command)
            engine.send(command)
            raw.append(">> isready")
            engine.send("isready")
            raw.extend(engine.read_until("readyok", 30))

        for name, value in S14:
            setoption(name, value)
        setoption("Threads", "1")
        setoption("Hash", "16")
        if args.idea == "true":
            setoption("IdeaK5", "true")
            setoption("IdeaK5_Divisor", str(args.divisor))
            setoption("IdeaK5_Depth", str(args.history_depth))
        elif args.idea == "false":
            setoption("IdeaK5", "false")

        for index, fen in enumerate(fens):
            raw.append(f">> ucinewgame {index}")
            engine.send("ucinewgame")
            raw.append(">> isready")
            engine.send("isready")
            raw.extend(engine.read_until("readyok", 30))
            position = f"position fen {fen}"
            raw.append(">> " + position)
            engine.send(position)
            raw.append(">> isready")
            engine.send("isready")
            raw.extend(engine.read_until("readyok", 30))
            if args.go_nodes:
                go = f"go nodes {args.go_nodes}"
            else:
                go = f"go depth {args.depth}"
            raw.append(">> " + go)
            engine.send(go)
            info = engine.read_until("bestmove", 180)
            raw.extend(info)
            counts.append(nodes_of(info))
            print(f"{args.label} {index} {counts[-1]}", flush=True)
    except BaseException as exc:
        error = exc
        raw.extend(engine.last_read)
        raw.append(f"HARNESS FAIL {exc}")
    finally:
        engine.close()
        (out / f"{args.label}.log").write_text("\n".join(raw) + "\n")
        (out / f"{args.label}.nodes").write_text("\n".join(str(n) for n in counts) + "\n")
        (out / f"{args.label}.meta").write_text(
            f"exe {exe}\n"
            f"sha256 {digest}\n"
            f"id name {id_name}\n"
            + "\n".join(options_sent)
            + "\n"
            f"fens {Path(args.fens).resolve()}\n"
            f"positions {len(fens)}\n"
            f"depth {args.depth}\n"
            f"go_nodes {args.go_nodes}\n"
            f"idea {args.idea}\n"
            f"sum {sum(counts)}\n"
            f"error {error}\n"
        )
    if error is not None:
        raise error
    print(f"SUM {args.label} {sum(counts)} positions {len(counts)}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"HARNESS FAIL {exc}", file=sys.stderr)
        sys.exit(1)
