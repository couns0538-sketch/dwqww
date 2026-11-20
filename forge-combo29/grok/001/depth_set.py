#!/usr/bin/env python3
"""Depth search of a FEN/EPD list. One engine process. Stops on a bad engine line.

Usage:
  depth_set.py EXE FENS DEPTH OUT_PREFIX [--switch true|false] [--span N]
"""
import argparse
import hashlib
import queue
import subprocess
import sys
import threading
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


def fen_of(line: str) -> str:
    # EPD opcodes, if any, start at a ';' or a fourth-or-later token that is an opcode.
    body = line.split(";", 1)[0].strip()
    parts = body.split()
    if len(parts) < 4:
        raise SystemExit(f"not a fen: {line!r}")
    if len(parts) >= 6:
        return " ".join(parts[:6])
    return body


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("fens")
    ap.add_argument("depth", type=int)
    ap.add_argument("out_prefix")
    ap.add_argument("--switch", choices=("true", "false"), default=None)
    ap.add_argument("--span", type=int, default=None)
    ap.add_argument("--set", action="append", default=[], metavar="NAME=VALUE")
    args = ap.parse_args()

    exe = str(Path(args.exe).resolve())
    positions = [fen_of(ln) for ln in Path(args.fens).read_text().splitlines() if ln.strip()]
    prefix = Path(args.out_prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    raw_path = Path(str(prefix) + ".raw.txt")
    rows_path = Path(str(prefix) + ".rows.txt")
    meta_path = Path(str(prefix) + ".meta")

    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    options: list[str] = []

    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    lines: queue.Queue[str | None] = queue.Queue()

    def reader() -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            lines.put(line.rstrip("\n"))
        lines.put(None)

    threading.Thread(target=reader, daemon=True).start()
    log: list[str] = []
    id_name = ""
    failed = ""

    def send(cmd: str) -> None:
        log.append(">> " + cmd)
        assert proc.stdin is not None
        proc.stdin.write(cmd + "\n")
        proc.stdin.flush()

    def take(timeout: float) -> str | None:
        try:
            line = lines.get(timeout=timeout)
        except queue.Empty:
            return None
        if line is None:
            return None
        log.append("<< " + line)
        low = line.lower()
        if any(bad in low for bad in BAD):
            nonlocal failed
            failed = line
        return line

    def until(marker: str, timeout: float) -> bool:
        while True:
            line = take(timeout)
            if line is None:
                return False
            if failed:
                return False
            if line == marker or line.startswith(marker + " "):
                return True

    send("uci")
    while True:
        line = take(30)
        if line is None or failed:
            failed = failed or "no uciok"
            break
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
        if line == "uciok":
            break
    if not failed:
        send("isready")
        if not until("readyok", 30):
            failed = failed or "no readyok after uci"

    def setoption(name: str, value: str) -> None:
        nonlocal failed
        if failed:
            return
        cmd = f"setoption name {name} value {value}"
        options.append(cmd)
        send(cmd)
        send("isready")
        if not until("readyok", 30):
            failed = failed or f"no readyok after {name}"

    if not failed:
        setoption("Hash", "16")
        setoption("Threads", "1")
        for name, value in S14:
            setoption(name, value)
        if args.switch is not None:
            setoption("EvalRule50Damp", args.switch)
        if args.span is not None:
            setoption("EvalRule50Damp_Span", str(args.span))
        for item in args.set:
            if "=" not in item:
                failed = f"bad --set {item}"
                break
            name, value = item.split("=", 1)
            setoption(name, value)

    rows: list[str] = []
    if not failed:
        for index, fen in enumerate(positions, start=1):
            send("ucinewgame")
            send("isready")
            if not until("readyok", 30):
                failed = failed or f"no readyok after ucinewgame {index}"
                break
            send(f"position fen {fen}")
            send("isready")
            if not until("readyok", 30):
                failed = failed or f"no readyok after position {index}"
                break
            send(f"go depth {args.depth}")
            nodes = ""
            score = ""
            best = ""
            while True:
                line = take(120)
                if line is None:
                    failed = failed or f"no bestmove {index}"
                    break
                if failed:
                    break
                if line.startswith("info depth ") and f" depth {args.depth} " in f" {line} ":
                    parts = line.split()
                    if "nodes" in parts and "score" in parts:
                        # Keep the last info line at the requested depth.
                        if parts[1] == "depth" and parts[2] == str(args.depth):
                            nodes = parts[parts.index("nodes") + 1]
                            si = parts.index("score")
                            score = parts[si + 1]
                            if si + 2 < len(parts) and parts[si + 1] in ("cp", "mate"):
                                score = parts[si + 1] + " " + parts[si + 2]
                if line.startswith("bestmove "):
                    best = line.split()[1]
                    break
            if failed:
                break
            if not nodes or not best:
                failed = f"missing nodes or bestmove at {index}: nodes={nodes!r} best={best!r}"
                break
            rows.append(f"{index} {nodes} {score} {best}")

    raw_path.write_text("\n".join(log) + "\n")
    rows_path.write_text("\n".join(rows) + ("\n" if rows else ""))
    meta = [
        f"exe={exe}",
        f"sha256={sha}",
        f"id_name={id_name}",
        f"depth={args.depth}",
        f"positions={len(positions)}",
        f"rows={len(rows)}",
        f"failed={failed}",
        "options_sent:",
        *options,
        "",
    ]
    meta_path.write_text("\n".join(meta))
    try:
        if proc.stdin:
            proc.stdin.write("quit\n")
            proc.stdin.flush()
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
    if failed:
        print(failed, file=sys.stderr)
        return 1
    print(f"rows={len(rows)} file={rows_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
