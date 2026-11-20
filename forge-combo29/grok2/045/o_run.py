#!/usr/bin/env python3
"""o_run.py EXE LABEL SWITCH FENS RAW META

One fresh engine process. Sends Threads 1, Hash 16, then S14 in the brief's
order, then IdeaS10 when SWITCH is true or false (lower case). SWITCH none
sends no switch (exe B). After every setoption and every position command,
sends isready and reads every line up to readyok. ucinewgame + isready before
every position, then go depth 12. Raw file is engine stdout only.

Stops on unknown option, invalid value, invalid FEN, or illegal move.
"""
import hashlib
import select
import subprocess
import sys
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
]

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe):
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        self.buf = b""

    def send(self, line):
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def read_until(self, pred, timeout):
        deadline = time.time() + timeout
        lines = []
        while time.time() < deadline:
            while b"\n" in self.buf:
                raw, self.buf = self.buf.split(b"\n", 1)
                line = raw.decode("utf-8", "replace") + "\n"
                lines.append(line)
                low = line.lower()
                for bad in BAD:
                    if bad.lower() in low:
                        raise SystemExit("STOP: " + bad + ": " + line.rstrip())
                if pred(line):
                    return lines
            if self.proc.poll() is not None:
                rest = self.proc.stdout.read() or b""
                if rest:
                    self.buf += rest
                    continue
                break
            ready, _, _ = select.select([self.proc.stdout], [], [], 0.5)
            if not ready:
                continue
            chunk = self.proc.stdout.read(65536)
            if chunk:
                self.buf += chunk
        tail = "".join(lines[-8:])
        raise SystemExit("STOP: timeout, last lines:\n" + tail)

    def close(self):
        try:
            self.send("quit")
        except (BrokenPipeError, OSError):
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def isready(eng, raw):
    eng.send("isready")
    raw.extend(eng.read_until(lambda s: s.startswith("readyok"), 120))


def main():
    if len(sys.argv) != 7:
        raise SystemExit("usage: o_run.py EXE LABEL SWITCH FENS RAW META")
    exe, label, switch, fens_path, raw_path, meta_path = sys.argv[1:7]
    fens = [ln.strip() for ln in open(fens_path, encoding="utf-8") if ln.strip()]
    if len(fens) != 200:
        raise SystemExit(f"STOP: expected 200 fens, got {len(fens)}")
    if switch not in ("true", "false", "none"):
        raise SystemExit("STOP: switch must be true, false, or none")
    sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    options = [("Threads", "1"), ("Hash", "16")] + list(S14)
    if switch != "none":
        options.append(("IdeaS10", switch))
    sent = [f"setoption name {name} value {value}" for name, value in options]
    eng = Engine(exe)
    raw = []
    id_name = ""
    try:
        eng.send("uci")
        hello = eng.read_until(lambda s: s.startswith("uciok"), 60)
        raw.extend(hello)
        for line in hello:
            if line.startswith("id name "):
                id_name = line[len("id name "):].rstrip("\n")
        isready(eng, raw)
        for cmd in sent:
            eng.send(cmd)
            isready(eng, raw)
        for index, fen in enumerate(fens, start=1):
            eng.send("ucinewgame")
            isready(eng, raw)
            eng.send("position fen " + fen)
            isready(eng, raw)
            eng.send("go depth 12")
            raw.extend(eng.read_until(lambda s: s.startswith("bestmove "), 180))
            if index % 50 == 0:
                print(f"{label} {index}/200", flush=True)
    finally:
        eng.close()
    with open(raw_path, "w", encoding="utf-8") as out:
        out.writelines(raw)
    with open(meta_path, "w", encoding="utf-8") as meta:
        meta.write(f"label: {label}\n")
        meta.write(f"exe: {exe}\n")
        meta.write(f"sha256: {sha}\n")
        meta.write(f"id name: {id_name}\n")
        meta.write(f"switch: {switch}\n")
        meta.write(f"fens: {fens_path}\n")
        meta.write("options:\n")
        for cmd in sent:
            meta.write(cmd + "\n")
    bestmoves = sum(1 for line in raw if line.startswith("bestmove "))
    print(f"{label} bestmoves {bestmoves} raw {raw_path}")
    if bestmoves != 200:
        raise SystemExit(f"STOP: {label} bestmoves {bestmoves}")


if __name__ == "__main__":
    main()
