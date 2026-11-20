#!/usr/bin/env python3
"""One O-run: S14, Threads 1, Hash 16, optional switch, 200 positions, depth 12.

python3 orun.py <exe> <fens> <out-base> <switch-name|none> <true|false|none>
Writes <out-base>.txt (engine stdout) and <out-base>.meta.
"""
import hashlib
import queue
import subprocess
import sys
import threading
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
    ("Threads", "1"),
    ("Hash", "16"),
]
STOP_BITS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if len(sys.argv) != 6:
        sys.exit("usage: orun.py <exe> <fens> <out-base> <switch|none> <true|false|none>")
    exe, fens_path, out_base, switch, switch_value = sys.argv[1:]
    if switch == "none":
        options = list(S14)
    else:
        if switch_value not in ("true", "false"):
            sys.exit("switch value must be true or false")
        options = list(S14) + [(switch, switch_value)]
    fens = [line.strip() for line in open(fens_path, encoding="utf-8") if line.strip()]
    exe_sha = sha256_file(exe)
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    lines = []
    q = queue.Queue()

    def reader():
        for line in proc.stdout:
            q.put(line)
        q.put(None)

    threading.Thread(target=reader, daemon=True).start()
    stopped = {"why": None}

    def send(text):
        proc.stdin.write(text + "\n")
        proc.stdin.flush()

    def read_until(pred, timeout):
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                line = q.get(timeout=0.2)
            except queue.Empty:
                if proc.poll() is not None:
                    stopped["why"] = f"engine exited {proc.returncode}"
                    return False
                continue
            if line is None:
                stopped["why"] = "stdout closed"
                return False
            lines.append(line)
            if any(bit in line for bit in STOP_BITS):
                stopped["why"] = line.rstrip("\r\n")
                return False
            if pred(line):
                return True
        stopped["why"] = "timeout"
        return False

    def isready():
        send("isready")
        return read_until(lambda line: line.strip() == "readyok", 60)

    send("uci")
    if not read_until(lambda line: line.strip() == "uciok", 30):
        sys.exit(f"STOP: no uciok ({stopped['why']})")
    id_name = ""
    for line in lines:
        if line.startswith("id name "):
            id_name = line[len("id name "):].rstrip("\r\n")
    sent = []
    for name, value in options:
        command = f"setoption name {name} value {value}"
        send(command)
        sent.append(command)
        if not isready():
            sys.exit(f"STOP after {command}: {stopped['why']}")
    for index, fen in enumerate(fens, start=1):
        send("ucinewgame")
        if not isready():
            sys.exit(f"STOP ucinewgame {index}: {stopped['why']}")
        send(f"position fen {fen}")
        if not isready():
            sys.exit(f"STOP position {index}: {stopped['why']}")
        send("go depth 12")
        if not read_until(lambda line: line.startswith("bestmove "), 180):
            sys.exit(f"STOP go {index}: {stopped['why']}")
        if index % 20 == 0:
            print(f"{out_base} position {index}", file=sys.stderr, flush=True)
    send("quit")
    read_until(lambda line: False, 3)
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
    err = proc.stderr.read()
    with open(out_base + ".txt", "w", encoding="utf-8") as f:
        f.writelines(lines)
    with open(out_base + ".meta", "w", encoding="utf-8") as f:
        f.write(f"started_exe: {exe}\n")
        f.write(f"sha256: {exe_sha}\n")
        f.write(f"id_name: {id_name}\n")
        f.write(f"fens: {fens_path}\n")
        f.write(f"positions: {len(fens)}\n")
        f.write("options_sent:\n")
        for command in sent:
            f.write(command + "\n")
        if err:
            f.write("stderr:\n")
            f.write(err)
    print(f"wrote {out_base}.txt positions {len(fens)} id {id_name}", flush=True)


if __name__ == "__main__":
    main()
