#!/usr/bin/env python3
"""kimi5 job 36 runner: clock or depth searches over a position set, pure stdlib.
One engine process per run. ucinewgame + isready before EVERY search.
Position sent as 'position fen <first four fields of the EPD line> 0 1' (EPD move
counters are NOT sent). Every command mirrored into an input log.
Refusal scan on EVERY line read: 'unknown option', 'invalid value', 'illegal move',
'ERROR' stop the run (no rows file written).
Rows file <tag>.rows: one line per position, file order,
  '<n from 1> <depth of last line beginning "info depth"> <that line's nodes> <bestmove>'
  single spaces, LF, trailing LF.
Ledger file <tag>.ledger: lines beginning 'info string ITER', 'info string LEDGER' or
  'info string TmFinishIteration', each with its position number in front.
.meta beside the rows file: exe path, exe sha256, id name, option lines sent, go command.
Full raw stdout in <tag>_full.txt. Existing output STOPS the run (no overwrite).
Usage: runner_j36.py <engine> <epd> <outdir> <tag> <go...> -- <optfile>
  go: everything between the outdir/tag and '--' is joined as the go command tail
      e.g.  depth 12 -- pc20.opt   |   wtime 6000 btime 6000 winc 60 binc 60 -- pc20+nc.opt
"""
import hashlib
import os
import subprocess
import sys
import time

argv = sys.argv[1:]
sep = argv.index("--")
ENGINE, FENS, OUTDIR, TAG = argv[0], argv[1], argv[2], argv[3]
GO = "go " + " ".join(argv[4:sep])
OPTFILE = argv[sep + 1] if len(argv) > sep + 1 else None

os.makedirs(OUTDIR, exist_ok=True)
stamp = lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

rows_path = os.path.join(OUTDIR, f"{TAG}.rows")
ledger_path = os.path.join(OUTDIR, f"{TAG}.ledger")
input_log = os.path.join(OUTDIR, f"{TAG}_input.log")
full_path = os.path.join(OUTDIR, f"{TAG}_full.txt")
for path in (rows_path, ledger_path, input_log, full_path):
    if os.path.exists(path):
        raise SystemExit(f"REFUSING TO OVERWRITE existing output: {path}")

with open(ENGINE, "rb") as f:
    exe_sha = hashlib.sha256(f.read()).hexdigest()

options = [("Threads", "1"), ("Hash", "16")]
if OPTFILE:
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

REFUSALS = ("unknown option", "invalid value", "illegal move", "ERROR")

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

positions = []
with open(FENS) as f:
    for line in f:
        line = line.strip()
        if line:
            positions.append(line)

rows = []
ledger = []
for i, fen in enumerate(positions):
    send("ucinewgame")
    send("isready")
    read_until("readyok")
    fields = fen.split()
    send(f"position fen {' '.join(fields[:4])} 0 1")
    send(GO)
    out = read_until("bestmove")
    depth = nodes = bm = None
    for l in out:
        if l.startswith("info depth") and " nodes " in l:
            parts = l.split()
            depth = int(parts[2])
            nodes = int(parts[parts.index("nodes") + 1])
        elif l.startswith("info string ITER") or l.startswith("info string LEDGER") or \
                l.startswith("info string TmFinishIteration"):
            ledger.append(f"{i + 1} {l}")
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
with open(ledger_path, "w") as f:
    f.write("\n".join(ledger) + ("\n" if ledger else ""))
with open(rows_path + ".meta", "w") as f:
    f.write(f"exe: {ENGINE}\nexe_sha256: {exe_sha}\n{id_name}\nfens: {FENS}\n"
            f"go: {GO}\noptions_sent ({len(sent_options)}):\n")
    for l in sent_options:
        f.write(f"  {l}\n")
    f.write(f"start_utc: {t0}\nend_utc: {t1}\n"
            f"rows: {len(rows)}\nnodes_sum: {sum(int(r.split()[2]) for r in rows)}\n")
print(f"DONE {TAG} n={len(rows)} ledger_lines={len(ledger)}")
