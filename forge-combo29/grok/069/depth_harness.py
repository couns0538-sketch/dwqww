#!/usr/bin/env python3
"""Fixed-depth UCI harness.

Usage:
  depth_harness.py EXE FENS DEPTH OUT_PREFIX [Name Value]...

Sends Hash 16, Threads 1, then the S14 options in the required order, then any
extra options. After every setoption and every position, sends isready and
reads every line up to readyok. Stops on unknown option, invalid value,
invalid FEN, or illegal move. ucinewgame + isready before every go.
"""
import hashlib
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

STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe: str):
        self.exe = exe
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.stderr_lines: list[str] = []
        self.transcript: list[str] = []
        self._err = threading.Thread(target=self._drain_err, daemon=True)
        self._err.start()

    def _drain_err(self) -> None:
        assert self.proc.stderr is not None
        for line in self.proc.stderr:
            self.stderr_lines.append(line)

    def send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.transcript.append(">> " + line)
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, done) -> list[str]:
        assert self.proc.stdout is not None
        got: list[str] = []
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                raise RuntimeError("engine closed stdout early")
            line = line.rstrip("\n")
            self.transcript.append(line)
            got.append(line)
            low = line.lower()
            for mark in STOP_MARKS:
                if mark.lower() in low:
                    raise RuntimeError(f"STOP {mark}: {line}")
            if done(line):
                return got

    def isready(self) -> None:
        self.send("isready")
        self.read_until(lambda line: line == "readyok")

    def setoption(self, name: str, value: str) -> None:
        self.send(f"setoption name {name} value {value}")
        self.isready()

    def close(self) -> None:
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        self._err.join(timeout=2)


def main() -> int:
    if len(sys.argv) < 5:
        print("usage: depth_harness.py EXE FENS DEPTH OUT_PREFIX [Name Value]...", file=sys.stderr)
        return 2
    exe = str(Path(sys.argv[1]).resolve())
    fens_path = Path(sys.argv[2])
    depth = int(sys.argv[3])
    out_prefix = Path(sys.argv[4])
    extra = sys.argv[5:]
    if len(extra) % 2 != 0:
        print("extra options must be Name Value pairs", file=sys.stderr)
        return 2
    extras = list(zip(extra[0::2], extra[1::2]))
    fens = [line.strip() for line in fens_path.read_text().splitlines() if line.strip()]
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()

    eng = Engine(exe)
    rows: list[str] = []
    failed = ""
    id_name = ""
    try:
        eng.send("uci")
        id_lines = eng.read_until(lambda line: line == "uciok")
        id_name = next((line for line in id_lines if line.startswith("id name ")), "")
        eng.setoption("Hash", "16")
        eng.setoption("Threads", "1")
        for name, value in S14:
            eng.setoption(name, value)
        for name, value in extras:
            eng.setoption(name, value)
        for index, fen in enumerate(fens, start=1):
            eng.send("ucinewgame")
            eng.isready()
            eng.send(f"position fen {fen}")
            eng.isready()
            eng.send(f"go depth {depth}")
            lines = eng.read_until(lambda line: line.startswith("bestmove "))
            nodes = None
            info = ""
            best = ""
            for line in lines:
                if line.startswith("bestmove "):
                    best = line.split()[1]
                parts = line.split()
                if len(parts) >= 4 and parts[0] == "info" and parts[1] == "depth" and parts[2] == str(depth) and "nodes" in parts:
                    nodes = int(parts[parts.index("nodes") + 1])
                    info = line
            if nodes is None:
                raise RuntimeError(f"no depth {depth} nodes for position {index}")
            rows.append(f"{index}\t{nodes}\t{best}\t{fen}\t{info}")
            if index % 25 == 0 or index == len(fens):
                print(f"progress {index}/{len(fens)}", file=sys.stderr, flush=True)
    except Exception as exc:
        failed = str(exc)
        eng.transcript.append(f"!! {exc}")
        print(f"HARNESS FAIL {exc}", file=sys.stderr)
    finally:
        eng.close()

    raw = out_prefix.with_suffix(".raw.txt") if out_prefix.suffix == "" else Path(str(out_prefix) + ".raw.txt")
    # OUT_PREFIX is a path stem. Files: PREFIX.raw.txt PREFIX.rows.tsv PREFIX.meta
    stem = out_prefix
    raw = Path(str(stem) + ".raw.txt")
    rows_path = Path(str(stem) + ".rows.tsv")
    meta_path = Path(str(stem) + ".meta")
    err_path = Path(str(stem) + ".stderr.txt")
    raw.write_text("\n".join(eng.transcript) + "\n")
    err_path.write_text("".join(eng.stderr_lines))
    header = "index\tnodes\tbestmove\tfen\tinfo\n"
    rows_path.write_text(header + "\n".join(rows) + "\n")
    total = sum(int(row.split("\t")[1]) for row in rows)
    option_lines = ["Hash 16", "Threads 1"] + [f"{n} {v}" for n, v in S14] + [f"{n} {v}" for n, v in extras]
    meta_path.write_text(
        "\n".join(
            [
                f"exe={exe}",
                f"sha256={sha}",
                f"id_name={id_name}",
                f"depth={depth}",
                f"fens={fens_path.resolve()}",
                f"positions={len(fens)}",
                f"nodes_sum={total}",
                "options_sent:",
                *[f"  {line}" for line in option_lines],
                f"raw={raw.resolve()}",
                f"rows={rows_path.resolve()}",
                f"stderr={err_path.resolve()}",
                f"failed={failed}",
            ]
        )
        + "\n"
    )
    print(f"positions {len(rows)} nodes_sum {total} failed={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"HARNESS FAIL {exc}", file=sys.stderr)
        sys.exit(1)
