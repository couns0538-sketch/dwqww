#!/usr/bin/env python3
"""Fixed-depth node harness. One engine process. isready after every setoption and position."""
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

class Engine:
    def __init__(self, exe: Path):
        self.exe = exe
        self.proc = subprocess.Popen(
            [str(exe)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.raw = []
        self.q = queue.Queue()
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self.q.put(line)
        self.q.put(None)

    def send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.raw.append(">>> " + line + "\n")
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, predicate, timeout: float) -> str:
        while True:
            try:
                line = self.q.get(timeout=timeout)
            except queue.Empty as exc:
                raise TimeoutError("timeout waiting for engine") from exc
            if line is None:
                raise EOFError("engine closed stdout")
            self.raw.append(line)
            low = line.lower()
            for bad in BAD:
                if bad.lower() in low:
                    raise RuntimeError("STOP " + bad + " :: " + line.rstrip())
            if predicate(line):
                return line

    def close(self) -> None:
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()

def last_nodes(chunk: list[str]) -> int | None:
    found = None
    for line in chunk:
        if " nodes " not in line:
            continue
        parts = line.split()
        if "nodes" in parts:
            i = parts.index("nodes")
            if i + 1 < len(parts) and parts[i + 1].isdigit():
                found = int(parts[i + 1])
    return found

def main() -> int:
    if len(sys.argv) != 6:
        print("usage: search_set.py EXE FENS DEPTH OUT extra_options_csv", file=sys.stderr)
        return 2
    exe = Path(sys.argv[1])
    fens_path = Path(sys.argv[2])
    depth = int(sys.argv[3])
    out_path = Path(sys.argv[4])
    extra = [x for x in sys.argv[5].split(",") if x]
    fens = [ln.strip() for ln in fens_path.read_text().splitlines() if ln.strip()]
    digest = sha256(exe)
    eng = Engine(exe)
    id_name = ""
    failed = None
    try:
        eng.send("uci")
        eng.read_until(lambda s: s.startswith("uciok"), 30)
        for line in eng.raw:
            if line.startswith("id name "):
                id_name = line[len("id name "):].rstrip("\r\n")
        for opt in S14 + extra:
            eng.send(opt)
            eng.send("isready")
            eng.read_until(lambda s: s.startswith("readyok"), 30)
        for index, fen in enumerate(fens, start=1):
            before = len(eng.raw)
            eng.send("ucinewgame")
            eng.send("isready")
            eng.read_until(lambda s: s.startswith("readyok"), 30)
            eng.send("position fen " + fen)
            eng.send("isready")
            eng.read_until(lambda s: s.startswith("readyok"), 30)
            eng.send("go depth " + str(depth))
            eng.read_until(lambda s: s.startswith("bestmove "), 180)
            nodes = last_nodes(eng.raw[before:])
            if nodes is None:
                raise RuntimeError("no nodes for position " + str(index))
            eng.raw.append("### POS %d NODES %d\n" % (index, nodes))
            if index % 25 == 0 or index == len(fens):
                print("pos", index, "nodes", nodes, flush=True)
    except Exception as exc:
        failed = exc
    finally:
        eng.close()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("".join(eng.raw))
        meta = Path(str(out_path) + ".meta")
        opts = S14 + extra
        meta.write_text(
            "exe=" + str(exe.resolve()) + "\n"
            "sha256=" + digest + "\n"
            "id_name=" + id_name + "\n"
            "depth=" + str(depth) + "\n"
            "fens=" + str(fens_path.resolve()) + "\n"
            "count=" + str(len(fens)) + "\n"
            "options_sent=\n" + "\n".join(opts) + "\n"
            "error=" + ("" if failed is None else str(failed)) + "\n"
        )
    if failed is not None:
        print("FAIL", failed, file=sys.stderr)
        return 1
    print("WROTE", out_path)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
