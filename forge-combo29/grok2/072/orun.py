#!/usr/bin/env python3
"""One O-run: S14, Threads 1, Hash 16, optional switch, depth 12 on each FEN.

Raw engine stdout goes to <out>.txt. A .meta sits beside it.
"""
import hashlib
import queue
import subprocess
import sys
import threading
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


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def start_reader(proc: subprocess.Popen) -> queue.Queue:
    lines: queue.Queue = queue.Queue()

    def pump() -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            lines.put(line)
        lines.put(None)

    threading.Thread(target=pump, daemon=True).start()
    return lines


def readline(lines: queue.Queue, timeout: float) -> str:
    try:
        line = lines.get(timeout=timeout)
    except queue.Empty:
        raise TimeoutError(f"no output for {timeout}s")
    if line is None:
        raise EOFError("engine closed stdout")
    return line


def read_until(lines, raw, pred, timeout: float) -> list[str]:
    found = []
    while True:
        line = readline(lines, timeout)
        raw.write(line)
        raw.flush()
        found.append(line)
        if any(bad in line for bad in BAD):
            raise SystemExit(f"STOP {line.rstrip()}")
        if pred(line):
            return found
    return found


def main() -> None:
    if len(sys.argv) not in (4, 5):
        sys.exit("usage: orun.py <exe> <fens> <out-prefix> [SwitchName]")
    exe = Path(sys.argv[1]).resolve()
    fens = Path(sys.argv[2]).read_text(encoding="utf-8").splitlines()
    fens = [fen.strip() for fen in fens if fen.strip()]
    prefix = Path(sys.argv[3])
    options = list(S14)
    if len(sys.argv) == 5:
        # Full UCI line, for example: setoption name IdeaB1 value false
        options.append(sys.argv[4])
    prefix.parent.mkdir(parents=True, exist_ok=True)
    raw_path = prefix.with_suffix(".txt")
    meta_path = Path(str(prefix) + ".meta")
    proc = subprocess.Popen(
        [str(exe)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None
    lines = start_reader(proc)
    id_name = "MISSING"
    with raw_path.open("w", encoding="utf-8") as raw:
        def send(line: str) -> None:
            proc.stdin.write(line + "\n")
            proc.stdin.flush()

        send("uci")
        uci_lines = read_until(lines, raw, lambda s: s.startswith("uciok"), 30)
        for line in uci_lines:
            if line.startswith("id name "):
                id_name = line[len("id name ") :].rstrip("\n")
        send("isready")
        read_until(lines, raw, lambda s: s.startswith("readyok"), 30)
        for opt in options:
            send(opt)
            send("isready")
            read_until(lines, raw, lambda s: s.startswith("readyok"), 30)
        for index, fen in enumerate(fens, start=1):
            send("ucinewgame")
            send("isready")
            read_until(lines, raw, lambda s: s.startswith("readyok"), 30)
            send(f"position fen {fen}")
            send("isready")
            read_until(lines, raw, lambda s: s.startswith("readyok"), 30)
            send("go depth 12")
            read_until(lines, raw, lambda s: s.startswith("bestmove"), 120)
            if index % 25 == 0:
                print(f"{prefix.name} {index}/{len(fens)}", flush=True)
        send("quit")
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
    meta_path.write_text(
        "\n".join(
            [
                f"exe={exe}",
                f"sha256={sha256(exe)}",
                f"id_name={id_name}",
                "options:",
                *options,
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"wrote {raw_path} positions {len(fens)} id {id_name}")


if __name__ == "__main__":
    main()
