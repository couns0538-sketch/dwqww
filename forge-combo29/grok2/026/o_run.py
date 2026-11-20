#!/usr/bin/env python3
"""o_run.py EXE FENS OUT META [SWITCH true|false]

One engine process. S14, then Threads 1, then Hash 16, then the switch
when given, before every position. ucinewgame + isready before every
position. position + isready, then go depth 12. Stops on a refused line.
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
    ("Threads", "1"),
    ("Hash", "16"),
]

STOP_BITS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Stop(Exception):
    pass


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


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

    def send(self, line):
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, done):
        lines = []
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                raise Stop("engine closed stdout")
            line = line.rstrip("\r\n")
            lines.append(line)
            for bit in STOP_BITS:
                if bit in line:
                    raise Stop(line)
            if done(line):
                return lines

    def close(self):
        try:
            self.send("quit")
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()


def main():
    if len(sys.argv) not in (5, 7):
        sys.exit("usage: o_run.py EXE FENS OUT META [SWITCH true|false]")
    exe, fens_path, out_path, meta_path = sys.argv[1:5]
    options = list(S14)
    if len(sys.argv) == 7:
        switch, value = sys.argv[5], sys.argv[6]
        if value not in ("true", "false"):
            sys.exit("switch value must be true or false")
        options.append((switch, value))
    fens = [ln.strip() for ln in open(fens_path, encoding="utf-8") if ln.strip()]
    eng = Engine(exe)
    id_name = ""
    try:
        eng.send("uci")
        uci_lines = eng.read_until(lambda line: line == "uciok")
        for line in uci_lines:
            if line.startswith("id name "):
                id_name = line[len("id name "):]
        with open(out_path, "w", encoding="utf-8") as out:
            for n, fen in enumerate(fens, start=1):
                out.write(f"# POS {n}\n")
                eng.send("ucinewgame")
                eng.send("isready")
                for line in eng.read_until(lambda line: line == "readyok"):
                    out.write(line + "\n")
                for name, value in options:
                    eng.send(f"setoption name {name} value {value}")
                    eng.send("isready")
                    for line in eng.read_until(lambda line: line == "readyok"):
                        out.write(line + "\n")
                eng.send(f"position fen {fen}")
                eng.send("isready")
                for line in eng.read_until(lambda line: line == "readyok"):
                    out.write(line + "\n")
                eng.send("go depth 12")
                go_lines = eng.read_until(lambda line: line.startswith("bestmove "))
                for line in go_lines:
                    out.write(line + "\n")
                out.write(f"# END {n}\n")
                out.flush()
                if n % 25 == 0:
                    print(f"{n}/{len(fens)}", flush=True)
    except Stop as exc:
        eng.close()
        sys.exit(f"STOP: {exc}")
    eng.close()
    with open(meta_path, "w", encoding="utf-8") as meta:
        meta.write(f"exe: {exe}\n")
        meta.write(f"sha256: {sha256_file(exe)}\n")
        meta.write(f"id name: {id_name}\n")
        meta.write(f"positions: {len(fens)}\n")
        meta.write("option lines sent before every position, in this order:\n")
        for name, value in options:
            meta.write(f"setoption name {name} value {value}\n")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
