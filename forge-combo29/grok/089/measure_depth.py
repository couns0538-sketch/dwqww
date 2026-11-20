#!/usr/bin/env python3
"""Depth-limited node measure. One engine process. Stops on UCI errors.

Usage:
  measure_depth.py EXE OUT_PREFIX POS_FILE DEPTH [switch]
switch is omitted, or "IdeaA8=false", or "IdeaA8=true".
S14 is always sent, then Threads 1, Hash 16, then the switch if given.
"""
import hashlib
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

STOP_BITS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe: str):
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.log = []
        self.err_buf = ""

    def send(self, line: str) -> None:
        self.log.append(">> " + line)
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, pred, what: str) -> str:
        assert self.proc.stdout is not None
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                err = ""
                if self.proc.stderr is not None:
                    err = self.proc.stderr.read() or ""
                self.err_buf += err
                raise RuntimeError(f"eof waiting for {what}\n" + "\n".join(self.log[-30:]) + "\n" + err)
            line = line.rstrip("\n")
            self.log.append("<< " + line)
            for bit in STOP_BITS:
                if bit in line:
                    raise RuntimeError(f"STOP {bit}: {line}")
            if pred(line):
                return line

    def ready(self) -> None:
        self.send("isready")
        self.read_until(lambda s: s == "readyok", "readyok")

    def stderr_text(self) -> str:
        if self.proc.stderr is None:
            return self.err_buf
        try:
            self.err_buf += self.proc.stderr.read() or ""
        except Exception:
            pass
        return self.err_buf

    def close(self) -> None:
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()
            self.proc.wait(timeout=10)


def main() -> None:
    exe = str(Path(sys.argv[1]).resolve())
    out_prefix = Path(sys.argv[2])
    pos_file = Path(sys.argv[3])
    depth = int(sys.argv[4])
    switch = sys.argv[5] if len(sys.argv) > 5 else ""
    positions = []
    for raw in pos_file.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        fen = line.split(";")[0].strip()
        positions.append(fen)

    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    eng = Engine(exe)
    options = []
    try:
        eng.send("uci")
        id_line = eng.read_until(lambda s: s == "uciok", "uciok")
        id_name = ""
        for row in eng.log:
            if row.startswith("<< id name "):
                id_name = row[len("<< id name ") :]
        for name, value in S14:
            cmd = f"setoption name {name} value {value}"
            options.append(cmd)
            eng.send(cmd)
            eng.ready()
        for name, value in (("Threads", "1"), ("Hash", "16")):
            cmd = f"setoption name {name} value {value}"
            options.append(cmd)
            eng.send(cmd)
            eng.ready()
        if switch:
            if "=" not in switch:
                raise SystemExit("switch must be Name=true or Name=false")
            name, value = switch.split("=", 1)
            if value not in ("true", "false"):
                raise SystemExit("switch value must be true or false")
            cmd = f"setoption name {name} value {value}"
            options.append(cmd)
            eng.send(cmd)
            eng.ready()
            # The spin default is whatever the engine advertises. Send it only
            # when the caller passes IdeaA8_Captures=N as a second switch token
            # glued with a comma: IdeaA8=true,IdeaA8_Captures=2
        rows = []
        for index, fen in enumerate(positions, start=1):
            eng.send("ucinewgame")
            eng.ready()
            eng.send(f"position fen {fen}")
            eng.ready()
            eng.send(f"go depth {depth}")
            best = eng.read_until(lambda s: s.startswith("bestmove "), "bestmove")
            nodes = None
            for row in reversed(eng.log):
                if not row.startswith("<< info "):
                    continue
                parts = row.split()
                if "nodes" in parts:
                    nodes = int(parts[parts.index("nodes") + 1])
                    break
            if nodes is None:
                raise RuntimeError(f"no nodes for position {index}")
            rows.append(f"{index}\t{nodes}\t{best}\t{fen}")
            if index % 50 == 0:
                print(f"done {index}/{len(positions)}", flush=True)
        text = "\n".join(rows) + "\n"
        out_prefix.parent.mkdir(parents=True, exist_ok=True)
        out_prefix.write_text(text)
        meta = (
            f"exe={exe}\n"
            f"sha256={sha}\n"
            f"id_name={id_name}\n"
            f"uciok_line={id_line}\n"
            f"depth={depth}\n"
            f"positions={pos_file.resolve()}\n"
            f"count={len(positions)}\n"
            + "".join(f"option={line}\n" for line in options)
        )
        Path(str(out_prefix) + ".meta").write_text(meta)
        total = sum(int(row.split("\t", 2)[1]) for row in rows)
        first = [int(row.split("\t", 2)[1]) for row in rows[:3]]
        print(f"SUM {total} FIRST {first} N {len(rows)} FILE {out_prefix}")
    finally:
        eng.close()
        err = eng.stderr_text()
        Path(str(out_prefix) + ".stderr").write_text(err)
        log_path = Path(str(out_prefix) + ".log")
        log_path.write_text("\n".join(eng.log) + "\n")
        if err.strip():
            print("STDERR_NONEMPTY", file=sys.stderr)
            print(err, file=sys.stderr)


if __name__ == "__main__":
    main()
