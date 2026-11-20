#!/usr/bin/env python3
"""o_harness.py EXE RAW_PREFIX [true|false]
One fresh engine. S14, then Threads 1, Hash 16, then IdeaS13 if a third argument is given.
ucinewgame + isready before every FEN in ~/first200.fens, then go depth 12.
Writes RAW_PREFIX.raw (engine stdout) and RAW_PREFIX.meta.
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
    exe = sys.argv[1]
    prefix = sys.argv[2]
    switch = sys.argv[3] if len(sys.argv) > 3 else None
    options = list(S14)
    if switch is not None:
        if switch not in ("true", "false"):
            sys.exit(f"STOP: switch must be true or false, got {switch}")
        options.append(("IdeaS13", switch))
    sent = [f"setoption name {name} value {value}" for name, value in options]
    digest = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    raw_path = prefix + ".raw"
    meta_path = prefix + ".meta"
    id_name = ""
    with open(raw_path, "w", encoding="utf-8") as raw:
        def send(line):
            proc.stdin.write(line + "\n")
            proc.stdin.flush()

        def read_until(marker, timeout_lines=100000):
            nonlocal id_name
            got = []
            for _ in range(timeout_lines):
                line = proc.stdout.readline()
                if line == "":
                    sys.exit("STOP: engine closed stdout")
                raw.write(line)
                raw.flush()
                text = line.rstrip("\r\n")
                if text.startswith("id name ") and not id_name:
                    id_name = text[len("id name "):]
                for mark in STOPS:
                    if mark in text:
                        sys.exit(f"STOP: {text}")
                got.append(text)
                if text == marker or text.startswith(marker + " "):
                    return got
            sys.exit(f"STOP: never saw {marker}")

        send("uci")
        read_until("uciok")
        for line in sent:
            send(line)
            send("isready")
            read_until("readyok")
        fens = [ln.strip() for ln in open("/home/ubuntu/first200.fens", encoding="utf-8") if ln.strip()]
        if len(fens) != 200:
            sys.exit(f"STOP: expected 200 fens, got {len(fens)}")
        for fen in fens:
            send("ucinewgame")
            send("isready")
            read_until("readyok")
            send("position fen " + fen)
            send("isready")
            read_until("readyok")
            send("go depth 12")
            read_until("bestmove")
        send("quit")
        proc.stdin.close()
        rest = proc.stdout.read()
        if rest:
            raw.write(rest)
        proc.wait(timeout=30)
    with open(meta_path, "w", encoding="utf-8") as meta:
        meta.write(f"exe {exe}\n")
        meta.write(f"sha256 {digest}\n")
        meta.write(f"id name {id_name}\n")
        meta.write("options\n")
        for line in sent:
            meta.write(line + "\n")
        meta.write(f"fens /home/ubuntu/first200.fens\n")
        meta.write("command go depth 12\n")
        meta.write("before_each ucinewgame isready position isready\n")
    print(f"wrote {raw_path} id={id_name} sha256={digest}")


if __name__ == "__main__":
    main()
