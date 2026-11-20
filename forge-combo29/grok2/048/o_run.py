#!/usr/bin/env python3
"""o_run.py EXE FENS OUT SWITCH
SWITCH is "-" (do not send), "false", or "true" for option IdeaK4.
One fresh engine. S14 in the brief's order, then Threads and Hash were
already sent first so the S14 sequence itself is unchanged.
ucinewgame + isready before every position; isready after the position
line; go depth 12. Stops on unknown option, invalid value, invalid FEN,
illegal move.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

exe, fens_path, out_path, switch = sys.argv[1:5]
if switch not in ("-", "false", "true"):
    sys.exit(f"STOP bad switch {switch}")

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
# Threads and Hash are part of the O-run conditions, sent before S14.
options = [("Threads", "1"), ("Hash", "16")] + S14
if switch != "-":
    options.append(("IdeaK4", switch))

fens = [ln.strip() for ln in open(fens_path, encoding="utf-8") if ln.strip()]
if len(fens) != 200:
    sys.exit(f"STOP expected 200 fens, got {len(fens)}")

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

digest = sha256(exe)
proc = subprocess.Popen(
    [exe],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1,
)
log = []

def send(cmd):
    log.append(">> " + cmd)
    proc.stdin.write(cmd + "\n")
    proc.stdin.flush()

def fail(msg):
    Path(out_path).write_text("\n".join(log) + "\n")
    try:
        proc.kill()
    except Exception:
        pass
    sys.exit(msg)

def read_until(pred, what, limit=100000):
    for _ in range(limit):
        line = proc.stdout.readline()
        if line == "":
            fail(f"STOP eof waiting for {what}")
        line = line.rstrip("\n")
        log.append(line)
        low = line.lower()
        if ("unknown option" in low or "invalid value" in low or
                "invalid fen" in low or "illegal move" in low):
            fail(f"STOP {line}")
        if pred(line):
            return line
    fail(f"STOP too many lines waiting for {what}")

send("uci")
read_until(lambda l: l.strip() == "uciok", "uciok")
id_name = ""
option_lines = []
for line in log:
    if line.startswith("id name "):
        id_name = line[len("id name "):]
    if line.startswith("option name "):
        option_lines.append(line)

for name, value in options:
    send(f"setoption name {name} value {value}")
    send("isready")
    read_until(lambda l: l.strip() == "readyok", f"readyok after {name}")

for i, fen in enumerate(fens, start=1):
    send("ucinewgame")
    send("isready")
    read_until(lambda l: l.strip() == "readyok", f"readyok after ucinewgame {i}")
    send(f"position fen {fen}")
    send("isready")
    read_until(lambda l: l.strip() == "readyok", f"readyok after position {i}")
    send("go depth 12")
    read_until(lambda l: l.startswith("bestmove "), f"bestmove {i}")
    if i % 50 == 0:
        print(f"positions {i}", flush=True)

send("quit")
try:
    proc.wait(timeout=10)
except subprocess.TimeoutExpired:
    proc.kill()

text = "\n".join(log) + "\n"
Path(out_path).write_text(text)
meta = Path(out_path + ".meta")
sent = [f"setoption name {n} value {v}" for n, v in options]
meta.write_text("\n".join([
    f"exe {exe}",
    f"sha256 {digest}",
    f"id name {id_name}",
    "options sent:",
    *sent,
    "",
]))
print(f"wrote {out_path} id={id_name}")
