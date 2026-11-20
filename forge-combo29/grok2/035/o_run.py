#!/usr/bin/env python3
"""o_run.py EXE OUT LABEL [SWITCH true|false]
Depth-12 run over ~/first200.fens. S14, Threads 1, Hash 16.
ucinewgame + isready before every position. isready after every setoption.
Stops on unknown option, invalid value, invalid FEN, illegal move.
"""
import hashlib
import subprocess
import sys

STOPS = ("unknown option", "invalid value", "invalid FEN", "illegal move")
S14 = [
    ("Threads", "1"),
    ("Hash", "16"),
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


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Engine:
    def __init__(self, exe):
        self.exe = exe
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.lines = []

    def send(self, line):
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, done):
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                raise SystemExit("STOP eof from engine")
            line = line.rstrip("\r\n")
            self.lines.append(line)
            for bad in STOPS:
                if bad in line:
                    raise SystemExit("STOP " + line)
            if done(line):
                return line

    def isready(self):
        self.send("isready")
        self.read_until(lambda line: line == "readyok")

    def close(self):
        try:
            self.send("quit")
        except BrokenPipeError:
            pass
        self.proc.wait(timeout=60)


def main():
    if len(sys.argv) < 4:
        raise SystemExit("usage: o_run.py EXE OUT LABEL [SWITCH true|false]")
    exe, out_path, label = sys.argv[1], sys.argv[2], sys.argv[3]
    switch = None
    if len(sys.argv) >= 6 and sys.argv[4] == "SWITCH":
        if sys.argv[5] not in ("true", "false"):
            raise SystemExit("STOP switch value must be true or false")
        switch = sys.argv[5]
    fens = [ln.strip() for ln in open("/home/ubuntu/first200.fens", encoding="utf-8") if ln.strip()]
    if len(fens) != 200:
        raise SystemExit(f"STOP fen count {len(fens)}")
    eng = Engine(exe)
    options = []
    eng.send("uci")
    eng.read_until(lambda line: line == "uciok")
    eng.isready()
    for name, value in S14:
        cmd = f"setoption name {name} value {value}"
        options.append(cmd)
        eng.send(cmd)
        eng.isready()
    if switch is not None:
        cmd = f"setoption name IdeaS10 value {switch}"
        options.append(cmd)
        eng.send(cmd)
        eng.isready()
    for i, fen in enumerate(fens, start=1):
        eng.lines.append(f"# position {i}")
        eng.send("ucinewgame")
        eng.isready()
        eng.send("position fen " + fen)
        eng.isready()
        eng.send("go depth 12")
        eng.read_until(lambda line: line.startswith("bestmove "))
        if i % 25 == 0:
            print(f"{label} {i}/200", file=sys.stderr, flush=True)
    eng.close()
    id_name = next((ln for ln in eng.lines if ln.startswith("id name ")), "id name MISSING")
    with open(out_path, "w", encoding="utf-8") as o:
        o.write("\n".join(eng.lines) + "\n")
    meta = out_path + ".meta"
    with open(meta, "w", encoding="utf-8") as m:
        m.write(f"label {label}\n")
        m.write(f"exe_path {exe}\n")
        m.write(f"sha256 {sha256_file(exe)}\n")
        m.write(f"{id_name}\n")
        m.write("options_sent\n")
        for cmd in options:
            m.write(cmd + "\n")
        m.write(f"positions 200\n")
        m.write("go depth 12\n")
        m.write("threads_hash Threads 1 Hash 16\n")
    print(f"WROTE {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
