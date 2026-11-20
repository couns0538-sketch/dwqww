#!/usr/bin/env python3
"""UCI harness for seat 026. One fresh engine process per invocation.

Modes:
  honesty  -- no setoption; send uci, then one command (bench / go perft)
  search   -- S14, Threads 1, Hash 16, then optional extra options, then each FEN
"""

import argparse
import hashlib
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

STOP_MARKS = ("unknown option", "invalid value", "invalid fen", "illegal move")

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
    ("Threads", "1"),
    ("Hash", "16"),
]


class Engine:
    def __init__(self, exe: str):
        self.exe = str(Path(exe).resolve())
        self.proc = subprocess.Popen(
            [self.exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        self.q: queue.Queue[str | None] = queue.Queue()
        self.lines: list[str] = []
        self.bad: str | None = None
        self.thread = threading.Thread(target=self._read, daemon=True)
        self.thread.start()
        self.options_sent: list[str] = []
        self.id_name = ""

    def _read(self) -> None:
        assert self.proc.stdout is not None
        for raw in self.proc.stdout:
            text = raw.decode("utf-8", "replace").rstrip("\r\n")
            self.lines.append(text)
            self.q.put(text)
            low = text.lower()
            for mark in STOP_MARKS:
                if mark in low:
                    self.bad = text
                    break
        self.q.put(None)

    def send(self, cmd: str) -> None:
        if self.bad:
            raise SystemExit("STOP " + self.bad)
        assert self.proc.stdin is not None
        self.proc.stdin.write((cmd + "\n").encode())
        self.proc.stdin.flush()

    def read_until(self, pred, timeout: float) -> list[str]:
        got: list[str] = []
        end = time.time() + timeout
        while time.time() < end:
            try:
                item = self.q.get(timeout=0.25)
            except queue.Empty:
                if self.proc.poll() is not None and self.q.empty():
                    break
                continue
            if item is None:
                break
            got.append(item)
            if self.bad:
                raise SystemExit("STOP " + self.bad)
            if pred(item):
                return got
        tail = " | ".join(self.lines[-8:])
        raise SystemExit("TIMEOUT last=" + tail)

    def isready(self, timeout: float = 60.0) -> None:
        self.send("isready")
        self.read_until(lambda s: s.split()[:1] == ["readyok"], timeout)

    def setoption(self, name: str, value: str) -> None:
        line = f"setoption name {name} value {value}"
        self.options_sent.append(line)
        self.send(line)
        self.isready()

    def uci(self) -> None:
        self.send("uci")
        lines = self.read_until(lambda s: s == "uciok", 60.0)
        for line in lines:
            if line.startswith("id name "):
                self.id_name = line[len("id name ") :]

    def quit(self) -> None:
        try:
            if self.proc.poll() is None:
                self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        self.thread.join(timeout=2)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def asan_count(exe: str) -> str:
    try:
        out = subprocess.run(
            ["nm", "-C", exe],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return f"nm-failed {exc}"
    return str(sum(1 for line in out.stdout.splitlines() if "__asan_" in line))


def write_meta(out_path: Path, eng: Engine, extra: list[str]) -> None:
    meta = out_path.with_suffix(out_path.suffix + ".meta")
    body = [
        f"exe {eng.exe}",
        f"sha256 {sha256_file(eng.exe)}",
        f"id_name {eng.id_name}",
        f"asan_symbols {asan_count(eng.exe)}",
        "options_sent",
    ]
    body.extend(eng.options_sent if eng.options_sent else ["(none)"])
    body.extend(extra)
    meta.write_text("\n".join(body) + "\n", encoding="utf-8")


def load_fens(path: Path, limit: int) -> list[str]:
    fens = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # EPD may carry opcodes after the first four or six fields. Keep a FEN.
        parts = line.split()
        if len(parts) >= 6:
            fen = " ".join(parts[:6])
        else:
            fen = line
        fens.append(fen)
        if limit and len(fens) >= limit:
            break
    return fens


def parse_info(line: str) -> tuple[str, str, str] | None:
    if not line.startswith("info ") or " score " not in line or " nodes " not in line:
        return None
    toks = line.split()
    nodes = score = ""
    try:
        nodes = toks[toks.index("nodes") + 1]
    except ValueError:
        return None
    if "cp" in toks:
        score = "cp " + toks[toks.index("cp") + 1]
    elif "mate" in toks:
        score = "mate " + toks[toks.index("mate") + 1]
    else:
        # format_score may be "score cp N" or a bare integer after score.
        try:
            i = toks.index("score")
            if toks[i + 1] in ("cp", "mate"):
                score = toks[i + 1] + " " + toks[i + 2]
            else:
                score = toks[i + 1]
        except (ValueError, IndexError):
            score = "?"
    return nodes, score, line


def cmd_honesty(args: argparse.Namespace) -> None:
    eng = Engine(args.exe)
    try:
        eng.uci()
        eng.send(args.send)
        if args.send.startswith("bench"):
            eng.read_until(lambda s: s.startswith("info string bench "), 300.0)
        elif "perft" in args.send:
            eng.read_until(lambda s: s.startswith("nodes "), 300.0)
        else:
            eng.read_until(lambda s: s.startswith("bestmove "), 300.0)
    finally:
        eng.quit()
        raw = "\n".join(eng.lines) + "\n"
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(raw, encoding="utf-8")
        write_meta(out, eng, [f"send {args.send}"])
    print(f"wrote {args.out} lines {len(eng.lines)}")


def cmd_search(args: argparse.Namespace) -> None:
    fens = load_fens(Path(args.fens), args.limit)
    eng = Engine(args.exe)
    rows: list[str] = []
    try:
        eng.uci()
        for name, value in S14:
            eng.setoption(name, value)
        for item in args.opt or []:
            if "=" not in item:
                raise SystemExit(f"bad --opt {item}")
            name, value = item.split("=", 1)
            eng.setoption(name, value)
        for index, fen in enumerate(fens, start=1):
            eng.send("ucinewgame")
            eng.isready()
            eng.send("position fen " + fen)
            eng.isready()
            eng.send(f"go depth {args.depth}")
            chunk = eng.read_until(lambda s: s.startswith("bestmove "), args.timeout)
            nodes = score = "?"
            best = ""
            for line in chunk:
                parsed = parse_info(line)
                if parsed:
                    nodes, score, _ = parsed
                if line.startswith("bestmove "):
                    best = line.split()[1]
            rows.append(f"{index} {nodes} {score} {best}")
            if index % 25 == 0 or index == len(fens):
                print(f"progress {index}/{len(fens)}", flush=True)
    finally:
        eng.quit()
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(eng.lines) + "\n", encoding="utf-8")
        rows_path = out.with_suffix(out.suffix + ".rows")
        rows_path.write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")
        write_meta(
            out,
            eng,
            [
                f"fens {Path(args.fens).resolve()}",
                f"fens_sha256 {sha256_file(args.fens)}",
                f"depth {args.depth}",
                f"count {len(fens)}",
                f"rows {rows_path.resolve()}",
            ],
        )
    print(f"wrote {args.out} positions {len(rows)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)

    hon = sub.add_parser("honesty")
    hon.add_argument("--exe", required=True)
    hon.add_argument("--out", required=True)
    hon.add_argument("--send", required=True)
    hon.set_defaults(func=cmd_honesty)

    sea = sub.add_parser("search")
    sea.add_argument("--exe", required=True)
    sea.add_argument("--fens", required=True)
    sea.add_argument("--depth", type=int, required=True)
    sea.add_argument("--out", required=True)
    sea.add_argument("--limit", type=int, default=0)
    sea.add_argument("--timeout", type=float, default=180.0)
    sea.add_argument("--opt", action="append", default=[])
    sea.set_defaults(func=cmd_search)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    try:
        main()
    except SystemExit as exc:
        if exc.code not in (0, None):
            print(exc, file=sys.stderr)
        raise
