"""o_run.py: one depth-12 pass over first200.fens.

Usage: python3 o_run.py EXE RAW META FENS [SWITCH true|false]

Sends Threads, Hash, then S14, then the switch when one is named.
After every setoption and every position command, reads every line up to readyok.
Stops on unknown option, invalid value, invalid FEN, or illegal move.
"""
import hashlib
import subprocess
import sys
import threading
import queue

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
    def __init__(self, path):
        self.path = path
        self.proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.lines = queue.Queue()
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self.lines.put(line)
        self.lines.put(None)

    def send(self, text):
        assert self.proc.stdin is not None
        self.proc.stdin.write(text + "\n")
        self.proc.stdin.flush()

    def read_until(self, marker, timeout):
        got = []
        import time
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"no {marker!r} after {timeout}s; last lines: {got[-5:]}")
            try:
                line = self.lines.get(timeout=min(remaining, 1.0))
            except queue.Empty:
                if self.proc.poll() is not None:
                    raise RuntimeError(f"engine exited {self.proc.returncode} waiting for {marker!r}")
                continue
            if line is None:
                raise RuntimeError(f"engine closed stdout waiting for {marker!r}; got {got[-5:]}")
            got.append(line)
            stripped = line.strip()
            for bad in BAD:
                if bad in line:
                    raise RuntimeError(f"STOP {bad}: {stripped}")
            if stripped == marker or stripped.startswith(marker + " "):
                return got

    def close(self):
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()


def main():
    if len(sys.argv) not in (5, 7):
        sys.exit("usage: o_run.py EXE RAW META FENS [SWITCH true|false]")
    exe, raw_path, meta_path, fens_path = sys.argv[1:5]
    switch = None
    if len(sys.argv) == 7:
        switch = (sys.argv[5], sys.argv[6])
        if switch[1] not in ("true", "false"):
            sys.exit("switch value must be true or false")
    fens = []
    with open(fens_path, encoding="utf-8") as handle:
        for line in handle:
            fen = line.strip()
            if fen:
                fens.append(fen)
    if len(fens) != 200:
        sys.exit(f"STOP: expected 200 fens, got {len(fens)}")
    sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    eng = Engine(exe)
    transcript = []
    options = [("Threads", "1"), ("Hash", "16")] + S14
    if switch is not None:
        options.append(switch)
    try:
        eng.send("uci")
        transcript.extend(eng.read_until("uciok", 30))
        id_name = ""
        for line in transcript:
            if line.startswith("id name "):
                id_name = line.strip()
        for name, value in options:
            eng.send(f"setoption name {name} value {value}")
            eng.send("isready")
            transcript.extend(eng.read_until("readyok", 30))
        for index, fen in enumerate(fens, start=1):
            eng.send("ucinewgame")
            eng.send("isready")
            transcript.extend(eng.read_until("readyok", 30))
            eng.send(f"position fen {fen}")
            eng.send("isready")
            transcript.extend(eng.read_until("readyok", 30))
            eng.send("go depth 12")
            transcript.extend(eng.read_until("bestmove", 120))
            if index % 50 == 0:
                print(f"position {index}", flush=True)
    finally:
        eng.close()
    with open(raw_path, "w", encoding="utf-8") as handle:
        handle.writelines(transcript)
    with open(meta_path, "w", encoding="utf-8") as handle:
        handle.write(f"exe {exe}\n")
        handle.write(f"sha256 {sha}\n")
        handle.write(f"{id_name}\n")
        for name, value in options:
            handle.write(f"setoption name {name} value {value}\n")
        handle.write(f"fens {fens_path}\n")
        handle.write(f"fen_count {len(fens)}\n")
    print(f"WROTE {raw_path}")


if __name__ == "__main__":
    main()
