#!/usr/bin/env python3
"""kimi5 job 40 runner: depth-12 searches over a position set with a per-position
node cap taken from a base rows file. Pure stdlib. One engine process per run.
ucinewgame + isready before EVERY search (unless --keep-table: ucinewgame only once,
isready still before every search). Position sent as
'position fen <first four fields of the EPD line> 0 1' (EPD move counters NOT sent).
Every command mirrored into an input log.
Refusal scan on EVERY line read: 'unknown option', 'invalid value', 'illegal move',
'invalid FEN', 'ERROR' stop the run (no rows file written).
Cap: --cap <base.rows> <num>/<den>  -> per-position cap = base_nodes * num // den;
  the go command is 'go depth 12 nodes <cap>'. Without --cap: 'go depth 12'.
  Caps are written to <tag>.caps ('<n> <cap>').
Rows file <tag>.rows: one line per position, file order,
  '<n from 1> <depth of last line beginning "info depth"> <that line's nodes> <bestmove>'
  single spaces, LF, trailing LF. (Raw values; EXPLODED marking is the analysis's job.)
.meta beside the rows file: exe path, exe sha256, id name, option lines sent, go mode,
  cap spec, start/end UTC.
Full raw stdout in <tag>_full.txt. Existing output STOPS the run (no overwrite).
Usage: runner_j40.py <engine> <epd> <outdir> <tag> [--cap base.rows num/den] [--keep-table] -- <optfile>
"""
import hashlib
import os
import subprocess
import sys
import time

argv = sys.argv[1:]
CAP = None          # (base_nodes list, num, den)
CAP_BASE = None     # path of the base rows file
KEEP_TABLE = False
pos = []
OPTFILE = None
i = 0
while i < len(argv):
    if argv[i] == "--cap":
        base_path = argv[i + 1]
        num_s, den_s = argv[i + 2].split("/")
        base_nodes = []
        with open(base_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    base_nodes.append(int(line.split()[2]))
        CAP = (base_nodes, int(num_s), int(den_s))
        CAP_BASE = base_path
        i += 3
    elif argv[i] == "--keep-table":
        KEEP_TABLE = True
        i += 1
    elif argv[i] == "--":
        OPTFILE = argv[i + 1] if len(argv) > i + 1 else None
        break
    else:
        pos.append(argv[i])
        i += 1

ENGINE, FENS, OUTDIR, TAG = pos[0], pos[1], pos[2], pos[3]

os.makedirs(OUTDIR, exist_ok=True)
stamp = lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

rows_path = os.path.join(OUTDIR, f"{TAG}.rows")
caps_path = os.path.join(OUTDIR, f"{TAG}.caps")
input_log = os.path.join(OUTDIR, f"{TAG}_input.log")
full_path = os.path.join(OUTDIR, f"{TAG}_full.txt")
for path in (rows_path, caps_path, input_log, full_path):
    if os.path.exists(path):
        raise SystemExit(f"REFUSING TO OVERWRITE existing output: {path}")

with open(ENGINE, "rb") as f:
    exe_sha = hashlib.sha256(f.read()).hexdigest()

options = [("Threads", "1"), ("Hash", "16")]
if OPTFILE and OPTFILE != "none":
    with open(OPTFILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                name, _, value = line.rpartition(" ")
                options.append((name.strip(), value))

proc = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT, text=True, bufsize=1)
il = open(input_log, "w")
full = open(full_path, "w")

def send(line):
    il.write(line + "\n")
    il.flush()
    proc.stdin.write(line + "\n")
    proc.stdin.flush()

REFUSALS = ("unknown option", "invalid value", "illegal move", "invalid FEN", "ERROR")

def read_until(token):
    lines = []
    while True:
        line = proc.stdout.readline()
        if not line:
            raise RuntimeError(f"engine closed output while waiting for {token}")
        line = line.rstrip("\n")
        lines.append(line)
        full.write(line + "\n")
        for bad in REFUSALS:
            if bad in line:
                il.close()
                full.close()
                raise SystemExit(f"REFUSAL LINE: {line}")
        if line.split(" ")[0] == token or line.startswith(token + " "):
            return lines

t0 = stamp()
send("uci")
uci_lines = read_until("uciok")
id_name = next((l for l in uci_lines if l.startswith("id name")), "id name ?")
sent_options = []
for name, value in options:
    send(f"setoption name {name} value {value}")
    sent_options.append(f"setoption name {name} value {value}")
send("isready")
read_until("readyok")
if KEEP_TABLE:
    send("ucinewgame")
    send("isready")
    read_until("readyok")

positions = []
with open(FENS) as f:
    for line in f:
        line = line.strip()
        if line:
            positions.append(line)

if CAP is not None and len(CAP[0]) != len(positions):
    raise SystemExit(f"base rows count {len(CAP[0])} != positions {len(positions)}")

rows = []
caps = []
for i, fen in enumerate(positions):
    if not KEEP_TABLE:
        send("ucinewgame")
        send("isready")
        read_until("readyok")
    else:
        send("isready")
        read_until("readyok")
    fields = fen.split()
    send(f"position fen {' '.join(fields[:4])} 0 1")
    if CAP is not None:
        base_nodes, num, den = CAP
        cap = base_nodes[i] * num // den
        caps.append(f"{i + 1} {cap}")
        send(f"go depth 12 nodes {cap}")
    else:
        send("go depth 12")
    out = read_until("bestmove")
    depth = nodes = bm = None
    for l in out:
        if l.startswith("info depth") and " nodes " in l:
            parts = l.split()
            depth = int(parts[2])
            nodes = int(parts[parts.index("nodes") + 1])
        elif l.startswith("bestmove"):
            bm = l.split()[1] if len(l.split()) > 1 else "none"
    if depth is None or nodes is None or bm is None:
        il.close()
        full.close()
        raise SystemExit(f"no info-depth/bestmove line for position {i + 1}: {out[-5:]}")
    rows.append(f"{i + 1} {depth} {nodes} {bm}")
    if i < 3 or (i + 1) % 50 == 0:
        print(f"{TAG} pos {i + 1}/{len(positions)} depth {depth} nodes {nodes}", flush=True)

send("quit")
il.close()
full.close()
t1 = stamp()

with open(rows_path, "w") as f:
    f.write("\n".join(rows) + "\n")
if CAP is not None:
    with open(caps_path, "w") as f:
        f.write("\n".join(caps) + "\n")
with open(rows_path + ".meta", "w") as f:
    f.write(f"exe: {ENGINE}\nexe_sha256: {exe_sha}\n{id_name}\nfens: {FENS}\n"
            f"go: depth 12\nkeep_table: {KEEP_TABLE}\n"
            f"cap: {'none' if CAP is None else f'{CAP[1]}/{CAP[2]} x {CAP_BASE}'}\n"
            f"options_sent ({len(sent_options)}):\n")
    for l in sent_options:
        f.write(f"  {l}\n")
    f.write(f"start_utc: {t0}\nend_utc: {t1}\n"
            f"rows: {len(rows)}\nnodes_sum: {sum(int(r.split()[2]) for r in rows)}\n")
print(f"DONE {TAG} n={len(rows)}")
