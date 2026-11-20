#!/usr/bin/env python3
"""Measured depth search. One engine process. Stops on UCI errors.

Usage: search_set.py EXE FENS DEPTH OUTPREFIX [extra setoption lines...]
Writes OUTPREFIX.tsv, OUTPREFIX.raw, OUTPREFIX.meta, OUTPREFIX.sum
"""
import hashlib
import subprocess
import sys

BAD_BITS = ("unknown option", "invalid value", "invalid FEN", "illegal move")

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


class ProtocolError(RuntimeError):
    pass


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
        self.raw = []

    def send(self, line):
        self.raw.append(">> " + line)
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, pred):
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                raise ProtocolError("engine closed stdout")
            line = line.rstrip("\n")
            self.raw.append(line)
            for bit in BAD_BITS:
                if bit in line:
                    raise ProtocolError(line)
            if pred(line):
                return line

    def close(self):
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()


def main():
    if len(sys.argv) < 5:
        print("usage: search_set.py EXE FENS DEPTH OUTPREFIX [setoption ...]", file=sys.stderr)
        return 2
    exe, fen_path, depth_s, prefix = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    extra = sys.argv[5:]
    depth = int(depth_s)
    fens = []
    for line in open(fen_path):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fens.append(line.split(";")[0].strip())
    sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    eng = Engine(exe)
    id_name = ""
    try:
        eng.send("uci")
        while True:
            line = eng.read_until(lambda s: s == "uciok" or s.startswith("id name "))
            if line.startswith("id name "):
                id_name = line[len("id name "):]
            if line == "uciok":
                break
        options = list(S14) + list(extra)
        for opt in options:
            eng.send(opt)
            eng.send("isready")
            eng.read_until(lambda s: s == "readyok")
        rows = []
        for index, fen in enumerate(fens, start=1):
            eng.send("ucinewgame")
            eng.send("isready")
            eng.read_until(lambda s: s == "readyok")
            eng.send("position fen " + fen)
            eng.send("isready")
            eng.read_until(lambda s: s == "readyok")
            eng.send("go depth " + str(depth))
            nodes = None
            while True:
                line = eng.read_until(lambda s: s.startswith("bestmove ") or " nodes " in s)
                if " nodes " in line and not line.startswith("bestmove "):
                    parts = line.split()
                    if "nodes" in parts:
                        nodes = int(parts[parts.index("nodes") + 1])
                if line.startswith("bestmove "):
                    break
            if nodes is None:
                raise ProtocolError("no nodes before bestmove for position " + str(index))
            rows.append((index, nodes))
            if index % 50 == 0:
                print("progress", index, sum(n for _, n in rows), flush=True)
    except ProtocolError as exc:
        open(prefix + ".raw", "w").write("\n".join(eng.raw) + "\n")
        open(prefix + ".error", "w").write(str(exc) + "\n")
        print("STOP", exc, file=sys.stderr)
        eng.close()
        return 3
    eng.close()
    open(prefix + ".raw", "w").write("\n".join(eng.raw) + "\n")
    with open(prefix + ".tsv", "w") as handle:
        handle.write("index\tnodes\n")
        for index, nodes in rows:
            handle.write(f"{index}\t{nodes}\n")
    total = sum(n for _, n in rows)
    first = " ".join(str(n) for _, n in rows[:3])
    with open(prefix + ".sum", "w") as handle:
        handle.write(f"positions {len(rows)}\n")
        handle.write(f"depth {depth}\n")
        handle.write(f"sum {total}\n")
        handle.write(f"first3 {first}\n")
    with open(prefix + ".meta", "w") as handle:
        handle.write(f"exe={exe}\n")
        handle.write(f"sha256={sha}\n")
        handle.write(f"id_name={id_name}\n")
        handle.write("options_sent:\n")
        for opt in options:
            handle.write(opt + "\n")
        handle.write(f"fens={fen_path}\n")
        handle.write(f"depth={depth}\n")
        handle.write("per_position=ucinewgame, isready, position fen, isready, go depth\n")
    print(f"positions {len(rows)} depth {depth} sum {total} first3 {first}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
