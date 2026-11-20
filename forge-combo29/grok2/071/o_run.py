#!/usr/bin/env python3
"""o_run.py EXE FENS OUTBASE [switch]
switch: none (default), false, or true. Sends IdeaB1 only for false/true.
S14 in the brief's order, after Threads 1 and Hash 16.
ucinewgame + isready before every position, then position, isready, go depth 12.
The nodes kept are those of the last "info depth" line before bestmove.
"""
import hashlib
import subprocess
import sys

STOP_MARKERS = ("unknown option", "invalid value", "invalid FEN", "illegal move")

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


def main():
    exe, fens_path, outbase = sys.argv[1], sys.argv[2], sys.argv[3]
    switch = sys.argv[4] if len(sys.argv) > 4 else "none"
    if switch not in ("none", "false", "true"):
        sys.exit(f"STOP: bad switch {switch}")
    sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    transcript = []
    options_sent = []

    def fail(msg):
        proc.kill()
        path = outbase + ".partial.txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(transcript) + "\n")
        sys.exit(f"STOP: {msg} (partial {path})")

    def take():
        line = proc.stdout.readline()
        if line == "":
            fail("engine closed")
        line = line.rstrip("\r\n")
        transcript.append(line)
        low = line.lower()
        for marker in STOP_MARKERS:
            if marker.lower() in low:
                fail(line)
        return line

    def send(cmd):
        proc.stdin.write(cmd + "\n")
        proc.stdin.flush()

    def send_option(name, value):
        cmd = f"setoption name {name} value {value}"
        send(cmd)
        options_sent.append(cmd)
        send("isready")
        while True:
            line = take()
            if line == "readyok":
                return

    send("uci")
    id_name = ""
    while True:
        line = take()
        if line.startswith("id name "):
            id_name = line[len("id name "):]
        if line == "uciok":
            break

    send_option("Threads", "1")
    send_option("Hash", "16")
    for name, value in S14:
        send_option(name, value)
    if switch != "none":
        send_option("IdeaB1", switch)

    fens = [ln.strip() for ln in open(fens_path, encoding="utf-8") if ln.strip()]
    rows = []
    for i, fen in enumerate(fens, 1):
        send("ucinewgame")
        send("isready")
        while True:
            if take() == "readyok":
                break
        send(f"position fen {fen}")
        send("isready")
        while True:
            if take() == "readyok":
                break
        send("go depth 12")
        last_nodes = None
        last_info = None
        while True:
            line = take()
            if line.startswith("info depth ") and "nodes" in line.split():
                parts = line.split()
                last_nodes = int(parts[parts.index("nodes") + 1])
                last_info = line
            if line.startswith("bestmove"):
                break
        if last_nodes is None:
            fail(f"no info depth nodes before bestmove at position {i}")
        rows.append((i, last_nodes, last_info))
        if i % 25 == 0:
            print(f"pos {i} nodes {last_nodes}", flush=True)

    send("quit")
    proc.stdin.close()
    proc.wait(timeout=30)

    with open(outbase + ".txt", "w", encoding="utf-8") as f:
        f.write("\n".join(transcript) + "\n")
    with open(outbase + ".rows", "w", encoding="utf-8") as f:
        for i, n, info in rows:
            f.write(f"{i}\t{n}\n")
    with open(outbase + ".meta", "w", encoding="utf-8") as f:
        f.write(f"exe {exe}\n")
        f.write(f"sha256 {sha}\n")
        f.write(f"id_name {id_name}\n")
        f.write("options:\n")
        for opt in options_sent:
            f.write(opt + "\n")
    total = sum(n for _, n, _ in rows)
    a, b, c = (n for _, n, _ in rows[:3])
    print(f"positions {len(rows)} sum {total} first {a} {b} {c}")


if __name__ == "__main__":
    main()
