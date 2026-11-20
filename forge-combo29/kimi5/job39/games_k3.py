#!/usr/bin/env python3
"""kimi5 job 39: K3 bare-king game runner (file 39's protocol exactly).
One engine process for all games. Options: Threads 1, Hash 16, then the optfile
lines, then any --extra 'Name value'. Before every game: ucinewgame, isready.
Before every move: 'position fen <start> moves <all moves so far>', 'go <limit>'.
Judged BEFORE every move, in file 39's order: checkmate ('mate'), stalemate,
insufficient material ('insufficient'), is_repetition(3) ('repetition'),
halfmove clock >= 100 ('fifty'), 200 plies played ('cap').
Canonical text <tag>.txt: one line per game, input order,
'<kind>|<start fen>|<result>|<plies>|<final fen>' (python-chess board.fen(),
all six fields), '\\n' after every line, ASCII; its sha256 is printed.
Refusal scan on every stdout line ('unknown option', 'invalid value',
'illegal move', 'invalid FEN', 'ERROR'): stop, print the line, exit 2, NO
canonical file. An engine bestmove that is not a legal move: same, 'ILLEGAL:'.
Raw streams: <tag>_input.log, <tag>_full.txt. Existing output STOPS the run.
Usage: games_k3.py <engine> <games-file> <outdir> <tag> <go...> -- <optfile|-> [--extra 'N v']...
"""
import hashlib
import os
import subprocess
import sys

import chess

REFUSALS = ("unknown option", "invalid value", "illegal move", "invalid FEN", "ERROR")
MAX_PLIES = 200

argv = sys.argv[1:]
sep = argv.index("--")
ENGINE, GAMES, OUTDIR, TAG = argv[0], argv[1], argv[2], argv[3]
GO = "go " + " ".join(argv[4:sep])
rest = argv[sep + 1:]
OPTFILE = rest[0] if rest else "-"
extras = []
i = 1
while i < len(rest):
    if rest[i] == "--extra":
        extras.append(rest[i + 1])
        i += 2
    else:
        i += 1

os.makedirs(OUTDIR, exist_ok=True)
canon_path = os.path.join(OUTDIR, f"{TAG}.txt")
input_log = os.path.join(OUTDIR, f"{TAG}_input.log")
full_path = os.path.join(OUTDIR, f"{TAG}_full.txt")
for path in (canon_path, input_log, full_path):
    if os.path.exists(path):
        raise SystemExit(f"REFUSING TO OVERWRITE existing output: {path}")

games = []
with open(GAMES) as f:
    for line in f:
        line = line.rstrip("\n")
        if not line:
            continue
        parts = line.split("|")
        games.append((parts[0], parts[1]))

options = [("Threads", "1"), ("Hash", "16")]
if OPTFILE != "-":
    with open(OPTFILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                name, _, value = line.rpartition(" ")
                options.append((name.strip(), value))
for e in extras:
    name, _, value = e.rpartition(" ")
    options.append((name.strip(), value))

proc = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT, text=True, bufsize=1)
il = open(input_log, "w")
full = open(full_path, "w")
refused = []

def send(line):
    il.write(line + "\n")
    proc.stdin.write(line + "\n")
    proc.stdin.flush()

def readline():
    line = proc.stdout.readline()
    if line == "":
        refused.append("ENGINE EXITED")
        return ""
    full.write(line)
    for r in REFUSALS:
        if r in line:
            refused.append(line.rstrip("\n"))
    return line

def wait_for(prefix):
    while True:
        line = readline()
        if refused or line.startswith(prefix):
            return line

send("uci")
wait_for("uciok")
for name, value in options:
    send(f"setoption name {name} value {value}")

rows = []
for kind, start_fen in games:
    if refused:
        break
    send("ucinewgame")
    send("isready")
    wait_for("readyok")
    board = chess.Board(start_fen)
    moves = []
    plies = 0
    result = None
    while True:
        if board.is_checkmate():
            result = "mate"
        elif board.is_stalemate():
            result = "stalemate"
        elif board.is_insufficient_material():
            result = "insufficient"
        elif board.is_repetition(3):
            result = "repetition"
        elif board.halfmove_clock >= 100:
            result = "fifty"
        elif plies >= MAX_PLIES:
            result = "cap"
        if result is not None:
            break
        if moves:
            send(f"position fen {start_fen} moves {' '.join(moves)}")
        else:
            send(f"position fen {start_fen}")
        send(GO)
        best = None
        while True:
            line = readline()
            if refused:
                break
            if line.startswith("bestmove"):
                best = line.split()[1]
                break
        if refused:
            break
        try:
            mv = chess.Move.from_uci(best)
        except Exception:
            refused.append(f"BAD-MOVE: {best}")
            break
        if mv not in board.legal_moves:
            refused.append(f"ILLEGAL: {best} at {board.fen()}")
            break
        moves.append(best)
        board.push(mv)
        plies += 1
    if refused:
        break
    rows.append(f"{kind}|{start_fen}|{result}|{plies}|{board.fen()}")

send("quit")
try:
    proc.wait(timeout=10)
except Exception:
    proc.kill()
il.close()
full.close()

if refused:
    print("REFUSED:", refused[0])
    sys.exit(2)

text = "".join(r + "\n" for r in rows)
with open(canon_path, "w", encoding="ascii", newline="") as f:
    f.write(text)
sha = hashlib.sha256(text.encode("ascii")).hexdigest()
counts = {}
plies_sum = 0
for r in rows:
    res = r.split("|")[2]
    counts[res] = counts.get(res, 0) + 1
    plies_sum += int(r.split("|")[3])
print(f"games {len(rows)} sha256 {sha}")
print("counts", dict(sorted(counts.items())), "plies_sum", plies_sum)
