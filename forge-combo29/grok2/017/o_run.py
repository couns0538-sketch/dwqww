#!/usr/bin/env python3
"""o_run.py EXE LABEL SWITCH VALUE FENS RAW META
One engine process. S14, then Threads 1, Hash 16, then SWITCH if not '-'.
ucinewgame + isready, position + isready, go depth 12 for every FEN.
Stops on unknown option, invalid value, invalid FEN, illegal move.
"""
import hashlib
import subprocess
import sys

STOPS = ("unknown option", "invalid value", "invalid FEN", "illegal move")
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


def main():
    exe, label, switch, value, fens_path, raw_path, meta_path = sys.argv[1:8]
    fens = [ln.strip() for ln in open(fens_path, encoding="utf-8") if ln.strip()]
    if len(fens) != 200:
        sys.exit(f"STOP: expected 200 fens, got {len(fens)}")
    sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    options = [f"setoption name {n} value {v}" for n, v in S14]
    if switch != "-":
        if value not in ("true", "false"):
            sys.exit(f"STOP: switch value must be true or false, got {value}")
        options.append(f"setoption name {switch} value {value}")
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    id_name = ""
    with open(raw_path, "w", encoding="utf-8") as raw:
        def fail(msg):
            raw.flush()
            proc.kill()
            sys.exit(f"STOP {label}: {msg}")

        def send(line):
            proc.stdin.write(line + "\n")
            proc.stdin.flush()

        def read_until(pred):
            nonlocal id_name
            while True:
                line = proc.stdout.readline()
                if line == "":
                    fail("EOF from engine")
                raw.write(line)
                if line.startswith("id name "):
                    id_name = line[len("id name "):].rstrip("\n")
                for token in STOPS:
                    if token in line:
                        fail(line.strip())
                if pred(line):
                    return line

        send("uci")
        read_until(lambda line: line.startswith("uciok"))
        send("isready")
        read_until(lambda line: line.strip() == "readyok")
        for opt in options:
            send(opt)
            send("isready")
            read_until(lambda line: line.strip() == "readyok")
        for i, fen in enumerate(fens, start=1):
            send("ucinewgame")
            send("isready")
            read_until(lambda line: line.strip() == "readyok")
            send(f"position fen {fen}")
            send("isready")
            read_until(lambda line: line.strip() == "readyok")
            send("go depth 12")
            read_until(lambda line: line.startswith("bestmove"))
            if i % 50 == 0:
                print(f"{label} {i}/200", file=sys.stderr, flush=True)
        send("quit")
    proc.wait(timeout=30)
    with open(meta_path, "w", encoding="utf-8") as meta:
        meta.write(f"label={label}\n")
        meta.write(f"exe={exe}\n")
        meta.write(f"sha256={sha}\n")
        meta.write(f"id_name={id_name}\n")
        meta.write(f"switch={switch}\n")
        meta.write(f"value={value}\n")
        meta.write("options:\n")
        for opt in options:
            meta.write(opt + "\n")
    print(f"WROTE {raw_path} id={id_name} sha={sha}")


if __name__ == "__main__":
    main()
