#!/usr/bin/env python3
"""orun.py EXE FENS OUTPREFIX SWITCH
SWITCH is "none" or "Name=true" or "Name=false".
One engine process. S14, Threads 1, Hash 16. ucinewgame and isready before every
position. isready after every setoption and every position. Stops on a refusal.
"""
import hashlib
import queue
import subprocess
import sys
import threading

STOP = ("unknown option", "invalid value", "invalid FEN", "illegal move")
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
    exe, fens_path, prefix, switch = sys.argv[1:5]
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    log = []
    lines = queue.Queue()

    def reader():
        for line in proc.stdout:
            lines.put(line)
        lines.put(None)

    threading.Thread(target=reader, daemon=True).start()

    def send(line):
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(pred, timeout=120):
        while True:
            try:
                line = lines.get(timeout=timeout)
            except queue.Empty:
                raise SystemExit("STOP: timeout waiting for the engine")
            if line is None:
                raise SystemExit("STOP: engine closed stdout")
            line = line.rstrip("\n")
            log.append(line)
            for bad in STOP:
                if bad in line:
                    raise SystemExit(f"STOP: {line}")
            if pred(line):
                return line

    def ready():
        send("isready")
        read_until(lambda line: line == "readyok")

    opt_lines = []
    try:
        send("uci")
        read_until(lambda line: line == "uciok")
        ready()
        options = [("Threads", "1"), ("Hash", "16")] + S14
        if switch != "none":
            name, value = switch.split("=", 1)
            if value not in ("true", "false"):
                raise SystemExit(f"STOP: switch value {value}")
            options.append((name, value))
        for name, value in options:
            line = f"setoption name {name} value {value}"
            opt_lines.append(line)
            send(line)
            ready()
        fens = [ln.strip() for ln in open(fens_path, encoding="utf-8") if ln.strip()]
        for index, fen in enumerate(fens, 1):
            send("ucinewgame")
            ready()
            send("position fen " + fen)
            ready()
            send("go depth 12")
            info = []

            def on_best(line, info=info):
                if line.startswith("info "):
                    info.append(line)
                return line.startswith("bestmove ")

            read_until(on_best)
            if not info:
                raise SystemExit(f"STOP: no info line before bestmove at position {index}")
            last = info[-1]
            parts = last.split()
            if "nodes" not in parts:
                raise SystemExit(f"STOP: last info line has no nodes at {index}: {last}")
            int(parts[parts.index("nodes") + 1])
            if index % 40 == 0:
                print(f"{prefix} {index}/{len(fens)}", flush=True)
        send("quit")
        proc.wait(timeout=30)
    finally:
        with open(prefix + ".txt", "w", encoding="utf-8") as handle:
            handle.write("\n".join(log) + ("\n" if log else ""))
        sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
        id_name = next((line for line in log if line.startswith("id name ")), "missing")
        with open(prefix + ".meta", "w", encoding="utf-8") as handle:
            handle.write(f"exe: {exe}\n")
            handle.write(f"sha256: {sha}\n")
            handle.write(f"id: {id_name}\n")
            handle.write("options:\n")
            for line in opt_lines:
                handle.write(line + "\n")
        if proc.poll() is None:
            proc.kill()


if __name__ == "__main__":
    main()
