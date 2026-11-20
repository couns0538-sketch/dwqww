#!/usr/bin/env python3
"""One runner for the sanitizer proofs.

Usage: sanitizer_run.py EXE FENS DEPTH RAW_OUT [Name=value ...]
Writes RAW_OUT even if the engine dies. stderr is merged into the output.
The meta file records nm -C EXE | grep -c __asan_.
"""
import hashlib
import os
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
    def __init__(self, exe: str):
        env = os.environ.copy()
        env["ASAN_OPTIONS"] = "abort_on_error=1:halt_on_error=1:detect_leaks=0"
        env["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
        )
        self.q: queue.Queue[str | None] = queue.Queue()
        self.lines: list[str] = []
        self.thread = threading.Thread(target=self._read, daemon=True)
        self.thread.start()

    def _read(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            line = line.rstrip("\r\n")
            self.lines.append(line)
            self.q.put(line)
        self.q.put(None)

    def send(self, command: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(command + "\n")
        self.proc.stdin.flush()

    def read_until(self, predicate, timeout: float) -> str:
        deadline = time.monotonic() + timeout
        while True:
            remain = deadline - time.monotonic()
            if remain <= 0:
                raise TimeoutError("timed out waiting for engine")
            try:
                line = self.q.get(timeout=min(0.5, remain))
            except queue.Empty:
                if self.proc.poll() is not None:
                    raise RuntimeError(f"engine exited {self.proc.returncode}")
                continue
            if line is None:
                raise RuntimeError(f"engine closed stdout, exit {self.proc.poll()}")
            for bad in BAD:
                if bad in line:
                    raise RuntimeError(line)
            if predicate(line):
                return line

    def close(self) -> None:
        if self.proc.poll() is None:
            try:
                self.send("quit")
            except BrokenPipeError:
                pass
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()


def main() -> None:
    if len(sys.argv) < 5:
        raise SystemExit("usage: sanitizer_run.py EXE FENS DEPTH RAW_OUT [Name=value ...]")
    exe, fen_path, depth_s, raw_out = sys.argv[1:5]
    extras = []
    for item in sys.argv[5:]:
        name, value = item.split("=", 1)
        extras.append((name, value))
    depth = int(depth_s)
    fens = []
    for raw in Path(fen_path).read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        fen = " ".join(parts[:6]) if len(parts) >= 6 else " ".join(parts[:4]) + " 0 1"
        fens.append(fen)
    nm = subprocess.run(["nm", "-C", exe], text=True, capture_output=True, check=False)
    asan_count = sum(1 for line in nm.stdout.splitlines() if "__asan_" in line)
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    eng = Engine(exe)
    sent = ["uci"]
    error = ""
    try:
        eng.send("uci")
        eng.read_until(lambda line: line == "uciok", 60)
        for name, value in [("Threads", "1"), ("Hash", "16"), *S14, *extras]:
            command = f"setoption name {name} value {value}"
            sent.append(command)
            eng.send(command)
            sent.append("isready")
            eng.send("isready")
            eng.read_until(lambda line: line == "readyok", 60)
        for fen in fens:
            eng.send("ucinewgame")
            sent.append("ucinewgame")
            eng.send("isready")
            sent.append("isready")
            eng.read_until(lambda line: line == "readyok", 60)
            eng.send(f"position fen {fen}")
            sent.append(f"position fen {fen}")
            eng.send("isready")
            sent.append("isready")
            eng.read_until(lambda line: line == "readyok", 60)
            eng.send(f"go depth {depth}")
            sent.append(f"go depth {depth}")
            eng.read_until(lambda line: line.startswith("bestmove "), 180)
    except Exception as exc:
        error = str(exc)
        print(f"RUNNER_STOP {error}", flush=True)
    finally:
        time.sleep(0.3)
        eng.close()
    id_name = ""
    for line in eng.lines:
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
            break
    text = [f"exe={exe}", f"sha256={sha}", f"id_name={id_name}", f"runner_error={error}", "options_sent:"]
    text.extend(sent)
    text.append("engine_output:")
    text.extend(eng.lines)
    Path(raw_out).write_text("\n".join(text) + "\n")
    hits = [line for line in eng.lines if "AddressSanitizer" in line or "runtime error:" in line]
    Path(str(raw_out) + ".meta.txt").write_text(
        f"exe={exe}\nsha256={sha}\nid_name={id_name}\n"
        f"nm_asan_symbol_lines={asan_count}\n"
        f"sanitizer_lines={len(hits)}\nrunner_error={error}\n"
        "options_sent:\n" + "\n".join(sent) + "\n"
    )
    print(f"asan_symbols {asan_count} sanitizer_lines {len(hits)} positions {len(fens)}")
    for line in hits[:5]:
        print(line)


if __name__ == "__main__":
    main()
