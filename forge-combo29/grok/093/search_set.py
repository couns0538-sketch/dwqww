#!/usr/bin/env python3
"""Measured fixed-depth search. S14, Threads 1, Hash 16.

After every setoption and every position, send isready and read through readyok.
Stop on unknown option, invalid value, invalid FEN, or illegal move.
ucinewgame + isready before every go.
"""
import hashlib
import pathlib
import queue
import subprocess
import sys
import threading
import time

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

STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def fen_of(line):
    parts = line.split()
    if len(parts) < 6:
        return line.strip()
    return " ".join(parts[:6])


class Engine:
    def __init__(self, exe):
        self.exe = str(exe)
        self.proc = subprocess.Popen(
            [self.exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.raw = []
        self.lines = queue.Queue()

        def pump():
            for line in self.proc.stdout:
                self.lines.put(line)
            self.lines.put(None)

        threading.Thread(target=pump, daemon=True).start()

    def send(self, line):
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, done, timeout):
        deadline = time.time() + timeout
        got = []
        while time.time() < deadline:
            try:
                line = self.lines.get(timeout=0.25)
            except queue.Empty:
                if self.proc.poll() is not None:
                    break
                continue
            if line is None:
                break
            self.raw.append(line)
            got.append(line)
            for mark in STOP_MARKS:
                if mark in line:
                    raise RuntimeError("STOP " + line.strip())
            if done(line):
                return got
        raise TimeoutError("timed out waiting for engine")

    def close(self):
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def main():
    if len(sys.argv) < 5:
        print("usage: search_set.py EXE FENS DEPTH OUT_PREFIX [Name=value ...]", file=sys.stderr)
        sys.exit(2)
    exe = pathlib.Path(sys.argv[1]).resolve()
    fens_path = pathlib.Path(sys.argv[2])
    depth = int(sys.argv[3])
    out_prefix = pathlib.Path(sys.argv[4])
    extras = []
    for item in sys.argv[5:]:
        name, value = item.split("=", 1)
        extras.append((name, value))
    fens = [fen_of(line) for line in fens_path.read_text().splitlines() if line.strip()]
    sha = hashlib.sha256(exe.read_bytes()).hexdigest()
    options = S14 + extras
    eng = Engine(exe)
    id_name = ""
    error = None
    rows = []
    try:
        eng.send("uci")
        uci_lines = eng.read_until(lambda line: line.startswith("uciok"), 30)
        for line in uci_lines:
            if line.startswith("id name "):
                id_name = line[len("id name ") :].strip()
        for name, value in options:
            eng.send(f"setoption name {name} value {value}")
            eng.send("isready")
            eng.read_until(lambda line: line.startswith("readyok"), 30)
        for index, fen in enumerate(fens, start=1):
            eng.send("ucinewgame")
            eng.send("isready")
            eng.read_until(lambda line: line.startswith("readyok"), 30)
            eng.send(f"position fen {fen}")
            eng.send("isready")
            eng.read_until(lambda line: line.startswith("readyok"), 30)
            eng.send(f"go depth {depth}")
            lines = eng.read_until(lambda line: line.startswith("bestmove "), 180)
            nodes = None
            for line in lines:
                if " nodes " in line:
                    tail = line.split(" nodes ", 1)[1].split()[0]
                    if tail.isdigit():
                        nodes = int(tail)
            if nodes is None:
                raise RuntimeError(f"no nodes for position {index}")
            rows.append((index, nodes, fen))
            if index % 25 == 0:
                print(f"{out_prefix.name} {index}/{len(fens)}", flush=True)
    except Exception as exc:
        error = exc
    finally:
        eng.close()
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    (out_prefix.parent / (out_prefix.name + ".raw.txt")).write_text("".join(eng.raw))
    row_text = "".join(f"{index} {nodes} {fen}\n" for index, nodes, fen in rows)
    (out_prefix.parent / (out_prefix.name + ".rows.txt")).write_text(row_text)
    opt_lines = "\n".join(f"setoption name {name} value {value}" for name, value in options)
    meta = (
        f"exe={exe}\n"
        f"sha256={sha}\n"
        f"id_name={id_name}\n"
        f"depth={depth}\n"
        f"fens={fens_path}\n"
        f"count={len(rows)}\n"
        f"options_sent:\n{opt_lines}\n"
    )
    (out_prefix.parent / (out_prefix.name + ".meta")).write_text(meta)
    total = sum(nodes for _, nodes, _ in rows)
    print(f"SUM {total} count {len(rows)}", flush=True)
    if error is not None:
        print(f"ENGINE_ERROR {error}", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
