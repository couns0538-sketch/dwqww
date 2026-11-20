#!/usr/bin/env python3
"""Depth-search a FEN list. S14, Threads 1, Hash 16. Stops on a bad engine line."""
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

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe: str) -> None:
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.lines: queue.Queue[str] = queue.Queue()
        self.errors: queue.Queue[str] = queue.Queue()
        self.stdout_lines: list[str] = []
        self.stderr_lines: list[str] = []
        self._out = threading.Thread(target=self._pump, args=(self.proc.stdout, self.lines, self.stdout_lines), daemon=True)
        self._err = threading.Thread(target=self._pump, args=(self.proc.stderr, self.errors, self.stderr_lines), daemon=True)
        self._out.start()
        self._err.start()

    @staticmethod
    def _pump(pipe, dest: queue.Queue, store: list[str]) -> None:
        assert pipe is not None
        for line in pipe:
            text = line.rstrip("\n").rstrip("\r")
            store.append(text)
            dest.put(text)

    def send(self, command: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(command + "\n")
        self.proc.stdin.flush()

    def read_until(self, prefixes: tuple[str, ...], timeout: float) -> list[str]:
        got: list[str] = []
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"no {prefixes} within {timeout}s; last={got[-3:]}")
            try:
                line = self.lines.get(timeout=min(0.2, remaining))
            except queue.Empty:
                if self.proc.poll() is not None:
                    raise RuntimeError(f"engine exited {self.proc.returncode}; last={got[-3:]}")
                continue
            got.append(line)
            for bad in BAD:
                if bad in line:
                    raise RuntimeError(line)
            if line.startswith(prefixes):
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_fens(path: Path, limit: int | None) -> list[str]:
    fens = []
    for line in path.read_text().splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        fens.append(text)
        if limit is not None and len(fens) >= limit:
            break
    return fens


def nodes_from(block: list[str]) -> int:
    found = None
    for line in block:
        if " nodes " not in line:
            continue
        parts = line.split()
        if "nodes" in parts:
            found = int(parts[parts.index("nodes") + 1])
    if found is None:
        raise RuntimeError(f"no nodes in {block[-5:]}")
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--fens", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--extra", action="append", default=[], help="name=value sent after S14")
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    exe = Path(args.exe).resolve()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fens = load_fens(Path(args.fens), args.limit or None)
    extras = []
    for item in args.extra:
        name, value = item.split("=", 1)
        extras.append((name, value))

    engine = Engine(str(exe))
    sent: list[str] = []
    id_name = ""
    options: list[tuple[str, str]] = [("Threads", "1"), ("Hash", "16"), *S14, *extras]
    rows: list[tuple[int, int]] = []
    failed: BaseException | None = None
    try:
        engine.send("uci")
        sent.append("uci")
        ident = engine.read_until(("uciok",), 30)
        for line in ident:
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
        for name, value in options:
            command = f"setoption name {name} value {value}"
            engine.send(command)
            sent.append(command)
            engine.send("isready")
            sent.append("isready")
            engine.read_until(("readyok",), 30)
        for index, fen in enumerate(fens, start=1):
            engine.send("ucinewgame")
            sent.append("ucinewgame")
            engine.send("isready")
            sent.append("isready")
            engine.read_until(("readyok",), 30)
            engine.send(f"position fen {fen}")
            sent.append(f"position fen {fen}")
            engine.send("isready")
            sent.append("isready")
            engine.read_until(("readyok",), 30)
            engine.send(f"go depth {args.depth}")
            sent.append(f"go depth {args.depth}")
            block = engine.read_until(("bestmove ",), 120)
            nodes = nodes_from(block)
            rows.append((index, nodes))
            if index % 50 == 0:
                print(f"{args.tag} {index}/{len(fens)}", file=sys.stderr, flush=True)
    except (RuntimeError, TimeoutError) as exc:
        failed = exc
    finally:
        engine.close()

    raw_path = out_dir / f"{args.tag}.txt"
    nodes_path = out_dir / f"{args.tag}.nodes"
    meta_path = out_dir / f"{args.tag}.meta"
    err_path = out_dir / f"{args.tag}.err"
    sent_path = out_dir / f"{args.tag}.sent"
    raw_path.write_text("\n".join(engine.stdout_lines) + ("\n" if engine.stdout_lines else ""))
    err_path.write_text("\n".join(engine.stderr_lines) + ("\n" if engine.stderr_lines else ""))
    sent_path.write_text("\n".join(sent) + "\n")
    total = sum(nodes for _, nodes in rows)
    node_lines = [f"{index} {nodes}" for index, nodes in rows]
    node_lines.append(f"sum {total}")
    node_lines.append(f"count {len(rows)}")
    nodes_path.write_text("\n".join(node_lines) + "\n")
    meta_path.write_text(
        "\n".join(
            [
                f"exe={exe}",
                f"sha256={sha256(exe)}",
                f"id_name={id_name}",
                f"fens={Path(args.fens).resolve()}",
                f"depth={args.depth}",
                f"positions={len(fens)}",
                "options:",
                *[f"setoption name {name} value {value}" for name, value in options],
                f"failed={failed}",
                "",
            ]
        )
    )
    print(f"{args.tag} sum {total} count {len(rows)}")
    if failed is not None:
        print(f"STOP {failed}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, TimeoutError) as exc:
        print(f"STOP {exc}", file=sys.stderr)
        sys.exit(2)
