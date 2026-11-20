#!/usr/bin/env python3
"""orun.py EXE FENS OUTPREFIX [SWITCH true|false]
One engine process. S14, Threads 1 and Hash 16 are sent once, in order,
before the positions. ucinewgame + isready before every position.
go depth 12. Raw transcript (sent lines prefixed '>> ') and a .meta file.
Stops on unknown option, invalid value, invalid FEN, illegal move.
"""
import hashlib
import subprocess
import sys

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

STOP = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, path):
        self.path = path
        self.p = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        self.log = []

    def send(self, line):
        self.log.append(">> " + line)
        self.p.stdin.write((line + "\n").encode())
        self.p.stdin.flush()

    def read_until(self, done):
        while True:
            raw = self.p.stdout.readline()
            if raw == b"":
                sys.exit("STOP: engine closed stdout")
            line = raw.decode("utf-8", "replace").rstrip("\n")
            self.log.append(line)
            for word in STOP:
                if word in line:
                    sys.exit("STOP: " + line)
            if done(line):
                return line

    def close(self):
        try:
            self.send("quit")
        except BrokenPipeError:
            pass
        try:
            self.p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.p.kill()


def main():
    if len(sys.argv) not in (4, 5):
        sys.exit("usage: orun.py EXE FENS OUTPREFIX [SWITCH true|false]")
    exe, fens_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
    switch = sys.argv[4] if len(sys.argv) == 5 else None
    if switch not in (None, "true", "false"):
        sys.exit("switch must be true or false")
    fens = [ln.strip() for ln in open(fens_path, encoding="utf-8") if ln.strip()]
    eng = Engine(exe)
    eng.send("uci")
    id_name = ""
    while True:
        line = eng.read_until(lambda s: s == "uciok" or s.startswith("id name "))
        if line.startswith("id name "):
            id_name = line[len("id name "):]
            continue
        break
    eng.send("isready")
    eng.read_until(lambda s: s == "readyok")
    options = [("Threads", "1"), ("Hash", "16")] + S14
    if switch is not None:
        options.append(("IdeaS10", switch))
    sent = []
    for name, value in options:
        cmd = f"setoption name {name} value {value}"
        sent.append(cmd)
        eng.send(cmd)
        eng.send("isready")
        eng.read_until(lambda s: s == "readyok")
    for fen in fens:
        eng.send("ucinewgame")
        eng.send("isready")
        eng.read_until(lambda s: s == "readyok")
        eng.send("position fen " + fen)
        eng.send("isready")
        eng.read_until(lambda s: s == "readyok")
        eng.send("go depth 12")
        eng.read_until(lambda s: s.startswith("bestmove "))
    eng.close()
    with open(out + ".txt", "w", encoding="utf-8") as f:
        f.write("\n".join(eng.log) + "\n")
    sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    with open(out + ".meta", "w", encoding="utf-8") as f:
        f.write(f"exe: {exe}\n")
        f.write(f"sha256: {sha}\n")
        f.write(f"id name: {id_name}\n")
        f.write("options:\n")
        for cmd in sent:
            f.write(cmd + "\n")
        f.write(f"positions: {len(fens)}\n")
        f.write(f"fens: {fens_path}\n")
    print(f"wrote {out}.txt {out}.meta positions {len(fens)}")


if __name__ == "__main__":
    main()
