#!/usr/bin/env python3
"""Fixed-depth node harness.

S14, then Threads 1, then Hash 16, then any extra setoption lines.
ucinewgame + isready before every go. isready after every setoption and position.
Stops on unknown option, invalid value, invalid FEN, or illegal move.
"""
import argparse
import hashlib
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

S14 = [
    "setoption name LmrQuietBase value 93",
    "setoption name LmrQuietDivisor value 205",
    "setoption name LmrNoisyBase value 13",
    "setoption name LmrNoisyDivisor value 333",
    "setoption name LmrHistoryDivisor value 5643",
    "setoption name NullMoveBase value 5",
    "setoption name LmpBase value 8",
    "setoption name HistoryPruneMultiplier value 2220",
    "setoption name HistoryBonusQuadratic value 24",
    "setoption name HistoryBonusLinear value 54",
    "setoption name HistoryBonusMax value 2212",
    "setoption name SingularDepth value 6",
    "setoption name IirDepth value 2",
    "setoption name NonPawnCorrection value true",
    "setoption name Threads value 1",
    "setoption name Hash value 16",
]

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class ProtocolError(RuntimeError):
    pass


class Engine:
    def __init__(self, exe: str) -> None:
        self.exe = str(Path(exe).resolve())
        self.proc = subprocess.Popen(
            [self.exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.lines: queue.Queue[str | None] = queue.Queue()
        self.stderr = queue.Queue()

        def pump(stream, dest) -> None:
            assert stream is not None
            for line in stream:
                dest.put(line)
            dest.put(None)

        threading.Thread(target=pump, args=(self.proc.stdout, self.lines), daemon=True).start()
        threading.Thread(target=pump, args=(self.proc.stderr, self.stderr), daemon=True).start()

    def send(self, command: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(command + "\n")
        self.proc.stdin.flush()

    def read_until(self, done, timeout: float) -> list[str]:
        collected: list[str] = []
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            remaining = deadline - time.monotonic()
            try:
                line = self.lines.get(timeout=min(0.5, remaining))
            except queue.Empty:
                if self.proc.poll() is not None:
                    raise ProtocolError(f"engine exited {self.proc.returncode} while waiting")
                continue
            if line is None:
                raise ProtocolError("engine closed stdout")
            text = line.rstrip("\r\n")
            collected.append(text)
            for marker in BAD:
                if marker in text:
                    raise ProtocolError(text)
            if done(text):
                return collected
        raise ProtocolError(f"timeout after {timeout}s; last={collected[-3:]}")

    def close(self) -> str:
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=5)
        err = []
        while True:
            try:
                line = self.stderr.get_nowait()
            except queue.Empty:
                break
            if line is None:
                break
            err.append(line)
        return "".join(err)


def sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_fens(path: Path, limit: int) -> list[str]:
    fens = []
    for line in path.read_text().splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        fen = text.split(";")[0].strip()
        parts = fen.split()
        if len(parts) >= 6:
            fen = " ".join(parts[:6])
        fens.append(fen)
        if limit and len(fens) >= limit:
            break
    return fens


def nodes_of(info_lines: list[str]) -> int:
    nodes = None
    for line in info_lines:
        if " nodes " not in line:
            continue
        fields = line.split()
        if "nodes" in fields:
            nodes = int(fields[fields.index("nodes") + 1])
    if nodes is None:
        raise ProtocolError("no nodes field before bestmove")
    return nodes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--fens", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--extra", action="append", default=[])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()

    exe = str(Path(args.exe).resolve())
    fens = load_fens(Path(args.fens), args.limit)
    options = S14 + list(args.extra)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    engine = Engine(exe)
    transcript: list[str] = []
    rows: list[str] = []
    try:
        engine.send("uci")
        transcript.append(">>> uci")
        uci_lines = engine.read_until(lambda line: line == "uciok", 30)
        transcript.extend(uci_lines)
        id_name = next((line for line in uci_lines if line.startswith("id name ")), "")
        for option in options:
            engine.send(option)
            transcript.append(">>> " + option)
            engine.send("isready")
            transcript.append(">>> isready")
            got = engine.read_until(lambda line: line == "readyok", 30)
            transcript.extend(got)
        for index, fen in enumerate(fens, start=1):
            engine.send("ucinewgame")
            transcript.append(">>> ucinewgame")
            engine.send("isready")
            transcript.append(">>> isready")
            transcript.extend(engine.read_until(lambda line: line == "readyok", 30))
            position = f"position fen {fen}"
            engine.send(position)
            transcript.append(">>> " + position)
            engine.send("isready")
            transcript.append(">>> isready")
            transcript.extend(engine.read_until(lambda line: line == "readyok", 30))
            go = f"go depth {args.depth}"
            engine.send(go)
            transcript.append(">>> " + go)
            got = engine.read_until(lambda line: line.startswith("bestmove "), args.timeout)
            transcript.extend(got)
            nodes = nodes_of(got)
            best = next(line for line in got if line.startswith("bestmove "))
            rows.append(f"{index}\t{nodes}\t{best}\t{fen}")
            if index % 50 == 0 or index == len(fens):
                print(f"{index}/{len(fens)} nodes_so_far {sum(int(r.split(chr(9))[1]) for r in rows)}", flush=True)
    except Exception as exc:
        transcript.append(f"!!! {exc}")
        out.with_suffix(".txt").write_text("\n".join(transcript) + "\n")
        err = engine.close()
        if err:
            out.with_suffix(".err").write_text(err)
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    err = engine.close()
    raw_path = out.with_suffix(".txt")
    raw_path.write_text("\n".join(transcript) + "\n")
    rows_path = out.with_suffix(".rows.tsv")
    rows_path.write_text("\n".join(rows) + "\n")
    if err:
        out.with_suffix(".err").write_text(err)
    meta = [
        f"exe {exe}",
        f"sha256 {sha256(exe)}",
        f"id_name {id_name}",
        "options",
        *options,
        f"depth {args.depth}",
        f"fens {args.fens}",
        f"count {len(fens)}",
        f"sum {sum(int(row.split(chr(9))[1]) for row in rows)}",
        "",
    ]
    out.with_suffix(".meta").write_text("\n".join(meta))
    print(f"SUM {sum(int(row.split(chr(9))[1]) for row in rows)} positions {len(rows)}")
    print("FIRST", " ".join(row.split(chr(9))[1] for row in rows[:3]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
