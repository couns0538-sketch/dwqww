#!/usr/bin/env python3
"""Fixed-depth node harness.

One engine process. Sends S14 before every go, then ucinewgame, the position,
and go depth N. Reads every line up to readyok after each setoption and each
position. Stops on unknown option, invalid value, invalid FEN, or illegal move.
Writes the engine's raw output and a .meta file beside it.
"""
import argparse
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

STOP_PHRASES = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def fen_of(line):
    text = line.strip()
    if not text or text.startswith("#"):
        return None
    parts = text.split()
    if len(parts) < 6:
        raise SystemExit("short fen line: " + text)
    return " ".join(parts[:6])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--fens", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--extra", action="append", default=[], help="name=value sent after S14, before every go")
    parser.add_argument("--limit", type=int, default=0, help="only the first N positions")
    args = parser.parse_args()

    extras = []
    for item in args.extra:
        name, value = item.split("=", 1)
        extras.append((name, value))

    fens = []
    with open(args.fens, "r", encoding="utf-8") as handle:
        for line in handle:
            fen = fen_of(line)
            if fen is not None:
                fens.append(fen)
    if args.limit:
        fens = fens[: args.limit]
    if not fens:
        raise SystemExit("no positions")

    sha = hashlib.sha256(open(args.exe, "rb").read()).hexdigest()
    meta_path = args.out + ".meta"
    option_lines = [("Hash", "16"), ("Threads", "1")] + S14 + extras

    proc = subprocess.Popen(
        [args.exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    log = open(args.out, "w", encoding="utf-8")

    def send(text):
        log.write(">> " + text + "\n")
        log.flush()
        proc.stdin.write(text + "\n")
        proc.stdin.flush()

    def read_until(done_prefix):
        while True:
            line = proc.stdout.readline()
            if line == "":
                raise SystemExit("engine closed stdout")
            log.write(line)
            log.flush()
            text = line.rstrip("\r\n")
            for phrase in STOP_PHRASES:
                if phrase in text:
                    raise SystemExit("STOP " + text)
            if text.startswith(done_prefix):
                return text

    send("uci")
    id_name = ""
    while True:
        line = proc.stdout.readline()
        if line == "":
            raise SystemExit("engine closed stdout during uci")
        log.write(line)
        log.flush()
        text = line.rstrip("\r\n")
        if text.startswith("id name "):
            id_name = text
        if text == "uciok":
            break
    send("isready")
    read_until("readyok")
    for name, value in (("Hash", "16"), ("Threads", "1")):
        send("setoption name " + name + " value " + value)
        send("isready")
        read_until("readyok")

    for index, fen in enumerate(fens):
        send("ucinewgame")
        send("isready")
        read_until("readyok")
        for name, value in S14 + extras:
            send("setoption name " + name + " value " + value)
            send("isready")
            read_until("readyok")
        send("position fen " + fen)
        send("isready")
        read_until("readyok")
        send("go depth " + str(args.depth))
        nodes = None
        while True:
            line = proc.stdout.readline()
            if line == "":
                raise SystemExit("engine closed stdout during go")
            log.write(line)
            log.flush()
            text = line.rstrip("\r\n")
            for phrase in STOP_PHRASES:
                if phrase in text:
                    raise SystemExit("STOP " + text)
            if " nodes " in text and text.startswith("info "):
                for part in text.split():
                    pass
                bits = text.split()
                if "nodes" in bits:
                    nodes = bits[bits.index("nodes") + 1]
            if text.startswith("bestmove "):
                break
        if nodes is None:
            raise SystemExit("no nodes for position " + str(index))
        log.write("RESULT " + str(index) + " nodes " + nodes + "\n")
        log.flush()

    send("quit")
    while True:
        line = proc.stdout.readline()
        if line == "":
            break
        log.write(line)
        log.flush()
    proc.wait(timeout=60)
    log.close()

    with open(meta_path, "w", encoding="utf-8") as meta:
        meta.write("exe=" + args.exe + "\n")
        meta.write("sha256=" + sha + "\n")
        meta.write(id_name + "\n")
        meta.write("fens=" + args.fens + "\n")
        meta.write("depth=" + str(args.depth) + "\n")
        meta.write("positions=" + str(len(fens)) + "\n")
        for name, value in option_lines:
            meta.write("option " + name + " " + value + "\n")
    print("wrote", args.out, "positions", len(fens))


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(1)
