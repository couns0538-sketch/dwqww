#!/usr/bin/env python3
"""Depth-sum harness. One engine process. isready after every setoption and position."""
import hashlib
import subprocess
import sys

STOP_BITS = ("unknown option", "invalid value", "invalid FEN", "illegal move")
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
        self.transcript = []

    def send(self, line):
        self.transcript.append(">> " + line)
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, marker):
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                raise SystemExit("engine closed waiting for " + marker)
            line = line.rstrip("\r\n")
            self.transcript.append(line)
            for bit in STOP_BITS:
                if bit in line:
                    raise SystemExit("STOP " + line)
            if marker in line:
                return line

    def close(self):
        try:
            self.send("quit")
        except BrokenPipeError:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fen_of(line):
    text = line.strip()
    if not text or text.startswith("#"):
        return ""
    # EPD may carry opcodes after the 6 FEN fields.
    parts = text.split()
    if len(parts) >= 6:
        return " ".join(parts[:6])
    return text


def nodes_of(info_line):
    parts = info_line.split()
    if "nodes" not in parts:
        raise SystemExit("no nodes in " + info_line)
    return int(parts[parts.index("nodes") + 1])


def main():
    if len(sys.argv) < 5:
        raise SystemExit("usage: measure_depth.py EXE FENS DEPTH OUTPREFIX [IdeaS34]")
    exe, fen_path, depth_s, out_prefix = sys.argv[1:5]
    idea = sys.argv[5] if len(sys.argv) > 5 else ""
    depth = int(depth_s)
    fens = []
    with open(fen_path, encoding="utf-8") as handle:
        for raw in handle:
            fen = fen_of(raw)
            if fen:
                fens.append(fen)
    engine = Engine(exe)
    options = []
    engine.send("uci")
    id_line = engine.read_until("uciok")
    id_name = ""
    for line in engine.transcript:
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
    def setopt(name, value):
        line = f"setoption name {name} value {value}"
        options.append(line)
        engine.send(line)
        engine.send("isready")
        engine.read_until("readyok")

    setopt("Threads", "1")
    setopt("Hash", "16")
    for name, value in S14:
        setopt(name, value)
    if idea != "":
        setopt("IdeaS34", idea)
    rows = []
    for index, fen in enumerate(fens, start=1):
        engine.send("ucinewgame")
        engine.send("isready")
        engine.read_until("readyok")
        engine.send("position fen " + fen)
        engine.send("isready")
        engine.read_until("readyok")
        engine.send(f"go depth {depth}")
        last = ""
        while True:
            line = engine.proc.stdout.readline()
            if line == "":
                raise SystemExit("engine closed during go")
            line = line.rstrip("\r\n")
            engine.transcript.append(line)
            for bit in STOP_BITS:
                if bit in line:
                    raise SystemExit("STOP " + line)
            if line.startswith("info depth "):
                last = line
            if line.startswith("bestmove "):
                break
        if not last:
            raise SystemExit("no info depth before bestmove for " + fen)
        depth_got = int(last.split()[2])
        nodes = nodes_of(last)
        rows.append((index, nodes, depth_got, fen))
        if index % 50 == 0:
            print(f"progress {index} sum {sum(r[1] for r in rows)}", flush=True)
    engine.close()
    total = sum(r[1] for r in rows)
    with open(out_prefix + ".rows", "w", encoding="utf-8") as handle:
        handle.write("index\tnodes\tdepth\tfen\n")
        for index, nodes, depth_got, fen in rows:
            handle.write(f"{index}\t{nodes}\t{depth_got}\t{fen}\n")
    with open(out_prefix + ".sum", "w", encoding="utf-8") as handle:
        handle.write(f"positions={len(rows)}\n")
        handle.write(f"depth={depth}\n")
        handle.write(f"sum={total}\n")
        if rows:
            head = " ".join(str(r[1]) for r in rows[:3])
            handle.write(f"first3={head}\n")
    with open(out_prefix + ".meta", "w", encoding="utf-8") as handle:
        handle.write(f"exe={exe}\n")
        handle.write(f"sha256={sha256(exe)}\n")
        handle.write(f"id_name={id_name}\n")
        handle.write(f"uciok_line={id_line}\n")
        handle.write("options_sent:\n")
        for line in options:
            handle.write(line + "\n")
    with open(out_prefix + ".transcript", "w", encoding="utf-8") as handle:
        handle.write("\n".join(engine.transcript))
        handle.write("\n")
    print(f"positions={len(rows)} sum={total}")


if __name__ == "__main__":
    main()
