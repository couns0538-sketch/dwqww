#!/usr/bin/env python3
"""o_run.py EXE OUTSTEM [true|false]
One engine process. S14, then Threads 1, then Hash 16, then IdeaB1 if given.
ucinewgame + isready before every FEN in ~/first200.fens, then go depth 12.
Stops on unknown option, invalid value, invalid FEN, or illegal move.
Writes OUTSTEM.txt (transcript) and OUTSTEM.meta.
"""
import hashlib
import queue
import subprocess
import sys
import threading

FENS = "/home/ubuntu/first200.fens"
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

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def main():
    exe = sys.argv[1]
    stem = sys.argv[2]
    switch = sys.argv[3] if len(sys.argv) > 3 else None
    options = list(S14)
    if switch is not None:
        if switch not in ("true", "false"):
            sys.exit("switch must be true or false")
        options.append(("IdeaB1", switch))
    sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    fens = [ln.strip() for ln in open(FENS, encoding="utf-8") if ln.strip()]
    proc = subprocess.Popen(
        ["stdbuf", "-oL", exe],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
    )
    log = []
    lines = queue.Queue()

    def reader():
        for raw in proc.stdout:
            lines.put(raw)
        lines.put(None)

    threading.Thread(target=reader, daemon=True).start()

    def send(line):
        log.append(">> " + line)
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(token, timeout):
        got = []
        while True:
            try:
                raw = lines.get(timeout=timeout)
            except queue.Empty:
                proc.kill()
                dump()
                sys.exit(f"STOP timeout waiting for {token}")
            if raw is None:
                dump()
                sys.exit(f"STOP eof waiting for {token}")
            line = raw.rstrip("\r\n")
            log.append("<< " + line)
            got.append(line)
            for bad in BAD:
                if bad in line:
                    dump()
                    sys.exit("STOP " + line)
            if line == token or line.startswith(token + " "):
                return got

    def dump():
        with open(stem + ".txt", "w", encoding="utf-8") as f:
            f.write("\n".join(log) + "\n")

    send("uci")
    uci_lines = read_until("uciok", 30)
    id_name = next((ln[8:] for ln in uci_lines if ln.startswith("id name ")), "MISSING")
    send("isready")
    read_until("readyok", 30)
    for name, value in options:
        send(f"setoption name {name} value {value}")
        send("isready")
        read_until("readyok", 30)
    for index, fen in enumerate(fens, start=1):
        send("ucinewgame")
        send("isready")
        read_until("readyok", 30)
        send("position fen " + fen)
        send("isready")
        read_until("readyok", 30)
        send("go depth 12")
        read_until("bestmove", 180)
        if index % 50 == 0:
            print(f"{stem} {index}/{len(fens)}", flush=True)
    send("quit")
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
    dump()
    with open(stem + ".meta", "w", encoding="utf-8") as f:
        f.write(f"exe {exe}\n")
        f.write("started stdbuf -oL so option lines are not stuck in a full pipe\n")
        f.write(f"sha256 {sha}\n")
        f.write(f"id name {id_name}\n")
        f.write("options\n")
        for name, value in options:
            f.write(f"setoption name {name} value {value}\n")
    print(f"wrote {stem}.txt {stem}.meta", flush=True)


if __name__ == "__main__":
    main()
