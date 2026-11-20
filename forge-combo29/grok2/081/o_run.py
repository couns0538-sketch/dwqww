#!/usr/bin/env python3
"""Depth-12 node harness for one O run.

Usage:
  python3 o_run.py EXE OUTPREFIX [SWITCH VALUE]

SWITCH VALUE is omitted for the plain engine. VALUE is true or false.
S14 options, then Threads 1, then Hash 16, then the switch if given.
Stops on unknown option, invalid value, invalid FEN, or illegal move.
"""
import hashlib
import subprocess
import sys

STOP_PHRASES = ("unknown option", "invalid value", "invalid fen", "illegal move")
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


class StopRun(Exception):
    pass


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def nodes_of(info_line):
    parts = info_line.split()
    for index, part in enumerate(parts):
        if part == "nodes" and index + 1 < len(parts):
            return parts[index + 1]
    return None


def main():
    if len(sys.argv) not in (3, 5):
        sys.exit("usage: o_run.py EXE OUTPREFIX [SWITCH VALUE]")
    exe = sys.argv[1]
    prefix = sys.argv[2]
    switch = None
    if len(sys.argv) == 5:
        switch = (sys.argv[3], sys.argv[4])
        if switch[1] not in ("true", "false"):
            sys.exit("switch value must be true or false")
    fens = [line.strip() for line in open("/home/ubuntu/first200.fens", encoding="utf-8") if line.strip()]
    if len(fens) != 200:
        sys.exit(f"expected 200 fens, got {len(fens)}")

    options = [f"setoption name {name} value {value}" for name, value in S14]
    if switch is not None:
        options.append(f"setoption name {switch[0]} value {switch[1]}")

    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    raw_lines = []

    def send(line):
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(done):
        while True:
            line = proc.stdout.readline()
            if line == "":
                raise StopRun("engine closed stdout")
            line = line.rstrip("\r\n")
            raw_lines.append(line)
            lowered = line.lower()
            for phrase in STOP_PHRASES:
                if phrase in lowered:
                    raise StopRun(f"STOP {phrase}: {line}")
            if done(line):
                return line

    id_name = ""
    try:
        send("uci")
        while True:
            line = read_until(lambda item: item == "uciok" or item.startswith("id name "))
            if line.startswith("id name "):
                id_name = line[len("id name "):]
                read_until(lambda item: item == "uciok")
                break
        for option in options:
            send(option)
            send("isready")
            read_until(lambda item: item == "readyok")
        rows = []
        for number, fen in enumerate(fens, start=1):
            send("ucinewgame")
            send("isready")
            read_until(lambda item: item == "readyok")
            send("position fen " + fen)
            send("isready")
            read_until(lambda item: item == "readyok")
            send("go depth 12")
            last_info = ""
            while True:
                line = read_until(lambda item: item.startswith("bestmove ") or item.startswith("info "))
                if line.startswith("info "):
                    last_info = line
                    continue
                break
            found = nodes_of(last_info)
            if found is None:
                raise StopRun(f"no nodes on last info of position {number}: {last_info}")
            rows.append(f"{number}\t{found}\t{last_info}")
            if number % 50 == 0:
                print(f"{prefix} {number}/200", flush=True)
        send("quit")
        proc.wait(timeout=30)
    except Exception:
        proc.kill()
        with open(prefix + ".raw.txt", "w", encoding="utf-8") as handle:
            handle.write("\n".join(raw_lines) + "\n")
        raise

    with open(prefix + ".rows.txt", "w", encoding="utf-8") as handle:
        handle.write("\n".join(rows) + "\n")
    with open(prefix + ".raw.txt", "w", encoding="utf-8") as handle:
        handle.write("\n".join(raw_lines) + "\n")
    with open(prefix + ".meta", "w", encoding="utf-8") as handle:
        handle.write(f"exe={exe}\n")
        handle.write(f"sha256={sha256_file(exe)}\n")
        handle.write(f"id_name={id_name}\n")
        handle.write("options:\n")
        for option in options:
            handle.write(option + "\n")
    print(f"wrote {prefix}.rows.txt {len(rows)}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except StopRun as error:
        sys.exit(str(error))
