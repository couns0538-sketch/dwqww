#!/usr/bin/env python3
"""O-run harness for Grok swarm 2 seat 008.

One engine process. Before every go depth 12: ucinewgame, position, then
Hash 16, Threads 1, the S14 options in the brief's order, then IdeaK4
when requested. isready after every setoption and every position. Stops
on unknown option, invalid value, invalid FEN, or illegal move.

Usage: o_harness.py EXE RAW META FENS SWITCH
SWITCH is none, true, or false. none does not send IdeaK4 (exe B).
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

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def main():
    if len(sys.argv) != 6:
        die("usage: o_harness.py EXE RAW META FENS SWITCH")
    exe, raw_path, meta_path, fens_path, switch = sys.argv[1:]
    if switch not in ("none", "true", "false"):
        die(f"STOP: switch must be none, true, or false, got {switch}")

    fens = []
    with open(fens_path, encoding="utf-8") as f:
        for line in f:
            fen = line.strip()
            if fen:
                fens.append(fen)
    if len(fens) != 200:
        die(f"STOP: expected 200 FENs, got {len(fens)}")

    sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    options = [("Hash", "16"), ("Threads", "1")] + list(S14)
    if switch != "none":
        options.append(("IdeaK4", switch))
    option_lines = [f"setoption name {name} value {value}" for name, value in options]

    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    raw = open(raw_path, "w", encoding="utf-8")
    id_name = ""

    def send(cmd):
        if proc.stdin is None:
            die("STOP: stdin closed")
        proc.stdin.write(cmd + "\n")
        proc.stdin.flush()

    def read_until(predicate):
        if proc.stdout is None:
            die("STOP: stdout closed")
        while True:
            line = proc.stdout.readline()
            if line == "":
                die("STOP: engine closed stdout")
            raw.write(line)
            raw.flush()
            text = line.rstrip("\n")
            for bad in BAD:
                if bad in text:
                    die(f"STOP: {text}")
            if predicate(text):
                return text

    try:
        send("uci")
        while True:
            text = read_until(lambda t: t == "uciok" or t.startswith("id name "))
            if text.startswith("id name "):
                id_name = text[len("id name "):]
                continue
            break
        send("isready")
        read_until(lambda t: t == "readyok")

        for fen in fens:
            send("ucinewgame")
            send("isready")
            read_until(lambda t: t == "readyok")
            send(f"position fen {fen}")
            send("isready")
            read_until(lambda t: t == "readyok")
            for line in option_lines:
                send(line)
                send("isready")
                read_until(lambda t: t == "readyok")
            send("go depth 12")
            read_until(lambda t: t.startswith("bestmove "))
    finally:
        if proc.stdin is not None:
            try:
                proc.stdin.write("quit\n")
                proc.stdin.flush()
            except BrokenPipeError:
                pass
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        raw.close()

    with open(meta_path, "w", encoding="utf-8") as meta:
        meta.write(f"exe: {exe}\n")
        meta.write(f"sha256: {sha}\n")
        meta.write(f"id name: {id_name}\n")
        meta.write(f"switch: {switch}\n")
        meta.write("option lines sent before every go depth 12, each followed by isready:\n")
        for line in option_lines:
            meta.write(line + "\n")
    print(f"ok {len(fens)} positions -> {raw_path}")


if __name__ == "__main__":
    main()
