#!/usr/bin/env python3
"""o_run.py EXE FENS OUT.raw OUT.meta [SWITCH value]
One engine process. S14, Threads 1, Hash 16 before every position.
ucinewgame + isready, position, isready, go depth 12.
Stops on unknown option, invalid value, invalid FEN, illegal move.
"""
import hashlib
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
        self.q = queue.Queue()

        def reader():
            for line in self.proc.stdout:
                self.q.put(line.rstrip("\n"))
            self.q.put(None)

        self.thread = threading.Thread(target=reader, daemon=True)
        self.thread.start()

    def send(self, cmd):
        self.proc.stdin.write(cmd + "\n")
        self.proc.stdin.flush()

    def read_until(self, pred, timeout):
        got = []
        end = time.time() + timeout
        while time.time() < end:
            try:
                line = self.q.get(timeout=0.2)
            except queue.Empty:
                if self.proc.poll() is not None:
                    break
                continue
            if line is None:
                break
            got.append(line)
            for bad in BAD:
                if bad in line:
                    raise SystemExit(f"STOP: {line}")
            if pred(line):
                return got
        raise SystemExit(f"STOP: timeout waiting after {got[-3:] if got else 'nothing'}")

    def close(self):
        try:
            self.send("quit")
        except BrokenPipeError:
            pass
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def main():
    exe, fens_path, raw_path, meta_path = sys.argv[1:5]
    extra = []
    if len(sys.argv) == 7:
        extra = [(sys.argv[5], sys.argv[6])]
    elif len(sys.argv) != 5:
        sys.exit("usage: o_run.py EXE FENS OUT.raw OUT.meta [SWITCH value]")

    with open(fens_path, encoding="utf-8") as f:
        fens = [ln.strip() for ln in f if ln.strip()]

    digest = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    eng = Engine(exe)
    raw = []

    def capture(lines):
        raw.extend(lines)

    def flush_raw():
        with open(raw_path, "w", encoding="utf-8") as o:
            if raw:
                o.write("\n".join(raw) + "\n")

    try:
        eng.send("uci")
        hello = eng.read_until(lambda s: s == "uciok", 30)
        capture(hello)
        id_name = next((ln for ln in hello if ln.startswith("id name ")), "id name MISSING")

        options = S14 + extra
        for i, fen in enumerate(fens, 1):
            for name, value in options:
                eng.send(f"setoption name {name} value {value}")
                eng.send("isready")
                capture(eng.read_until(lambda s: s == "readyok", 30))
            eng.send("ucinewgame")
            eng.send("isready")
            capture(eng.read_until(lambda s: s == "readyok", 30))
            eng.send(f"position fen {fen}")
            eng.send("isready")
            capture(eng.read_until(lambda s: s == "readyok", 30))
            eng.send("go depth 12")
            capture(eng.read_until(lambda s: s.startswith("bestmove "), 180))
            if i % 20 == 0:
                print(f"{i}/{len(fens)}", flush=True)
    finally:
        flush_raw()
        eng.close()
    with open(meta_path, "w", encoding="utf-8") as m:
        m.write(f"exe {exe}\n")
        m.write(f"sha256 {digest}\n")
        m.write(f"{id_name}\n")
        m.write("options:\n")
        for name, value in options:
            m.write(f"setoption name {name} value {value}\n")
        m.write("ucinewgame\n")
        m.write("isready\n")
        m.write("position fen <fen>\n")
        m.write("isready\n")
        m.write("go depth 12\n")
        m.write(f"positions {len(fens)}\n")
    print(f"wrote {raw_path} {len(fens)} positions", flush=True)


if __name__ == "__main__":
    main()
