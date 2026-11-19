#!/usr/bin/env python3
"""kimi5 job 34 oracle: for every F/P record of a job-34 .fp.log (or an index subset), on the
PLAIN build (PC20, Threads 1, Hash 16): ucinewgame, isready, position fen <FEN> moves <move>,
go depth D. value = -(score of that search); a mate score counts as 30000 with its sign.
BEATS = value > alpha (the record's a= field). D1 = max(1, d-1); D2 = d+2.
--no-negate: scratch copy that does NOT negate (the C-SIGN control's second way).
--parity P --npar N: process only records with ordinal % N == P (ordinal over the input order,
0-based, AFTER subsetting); used to split one pass over workers and to take every 2nd record.
One engine process per invocation serves all its records; ucinewgame+isready before each.
A refusal line ('illegal move', 'invalid FEN', 'unknown option', 'invalid value', 'ERROR')
stops the run with 'refused' and the line.
Usage: oracle_j34.py <engine> <fp.log> <out.jsonl> <d1|d2> <optfile> [--no-negate] [--parity P N] [--limit K]
"""
import hashlib
import json
import subprocess
import sys

ENGINE, FPLOG, OUT, DMODE, OPTFILE = sys.argv[1:6]
NEGATE = True
PARITY, NPAR, LIMIT = 0, 1, None
args = sys.argv[6:]
i = 0
while i < len(args):
    if args[i] == "--no-negate":
        NEGATE = False
        i += 1
    elif args[i] == "--parity":
        PARITY, NPAR = int(args[i + 1]), int(args[i + 2])
        i += 3
    elif args[i] == "--limit":
        LIMIT = int(args[i + 1])
        i += 2
    else:
        raise SystemExit(f"bad arg {args[i]}")

REFUSALS = ("illegal move", "invalid FEN", "unknown option", "invalid value", "ERROR")

recs = []
for line in open(FPLOG):
    if " info string F " not in line and " info string P " not in line:
        continue
    parts = line.split()
    cls = parts[3]  # F or P
    kv = {}
    for tok in parts[4:]:
        if tok.startswith("fen="):
            break
        k, _, v = tok.partition("=")
        kv[k] = v
    fen = line.split(" fen=", 1)[1].rstrip("\n")
    recs.append({"idx": int(parts[0]), "cls": cls, "d": int(kv["d"]), "l": int(kv["l"]), "a": int(kv["a"]),
                 "k": int(kv["k"]), "m": int(kv["m"]), "w": int(kv["w"]), "c": int(kv["c"]),
                 "h": int(kv["h"]), "t": int(kv["t"]), "p": kv["p"], "s": kv["s"],
                 "r": int(kv["r"]) if cls == "P" else None, "mv": kv["mv"], "fen": fen})
if LIMIT is not None:
    recs = recs[:LIMIT]
recs = [r for j, r in enumerate(recs) if j % NPAR == PARITY]
print(f"records to do: {len(recs)} (parity {PARITY}/{NPAR}, mode {DMODE}, negate {NEGATE})", flush=True)

with open(ENGINE, "rb") as f:
    exe_sha = hashlib.sha256(f.read()).hexdigest()

proc = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT, text=True, bufsize=1)

def send(line):
    proc.stdin.write(line + "\n")
    proc.stdin.flush()

def read_until(token):
    lines = []
    while True:
        line = proc.stdout.readline()
        if not line:
            raise RuntimeError(f"engine closed output while waiting for {token}")
        line = line.rstrip("\n")
        lines.append(line)
        if line.split(" ")[0] == token or line.startswith(token + " "):
            return lines

send("uci")
uci_lines = read_until("uciok")
send("setoption name Threads value 1")
send("setoption name Hash value 16")
for line in open(OPTFILE):
    line = line.strip()
    if line and not line.startswith("#"):
        name, _, value = line.rpartition(" ")
        send(f"setoption name {name.strip()} value {value}")
send("isready")
ready = read_until("readyok")
for l in uci_lines + ready:
    if any(x in l for x in REFUSALS):
        raise SystemExit(f"refused at setup: {l}")

done = 0
with open(OUT, "w") as out:
    for r in recs:
        D = max(1, r["d"] - 1) if DMODE == "d1" else r["d"] + 2
        send("ucinewgame")
        send("isready")
        rdy = read_until("readyok")
        for l in rdy:
            if any(x in l for x in REFUSALS):
                raise SystemExit(f"refused at record {done}: {l}")
        send(f"position fen {r['fen']} moves {r['mv']}")
        send(f"go depth {D}")
        lines = read_until("bestmove")
        for l in lines:
            if any(x in l for x in REFUSALS):
                raise SystemExit(f"refused at record {done}: {l}")
        score = None
        for l in lines:
            if l.startswith("info depth") and " score " in l:
                p = l.split()
                j = p.index("score")
                if p[j + 1] == "cp":
                    score = int(p[j + 2])
                elif p[j + 1] == "mate":
                    score = 30000 if int(p[j + 2]) > 0 else -30000
        noscore = score is None
        if noscore:
            score = 0
        value = -score if NEGATE else score
        beats = (not noscore) and value > r["a"]
        out.write(json.dumps({"idx": r["idx"], "cls": r["cls"], "d": r["d"], "l": r["l"], "a": r["a"],
                              "k": r["k"], "m": r["m"], "w": r["w"], "c": r["c"], "h": r["h"], "t": r["t"],
                              "p": r["p"], "s": r["s"], "r": r["r"], "mv": r["mv"], "D": D,
                              "score": score, "value": value, "beats": beats, "noscore": noscore}) + "\n")
        done += 1
        if done % 500 == 0:
            print(f"{done}/{len(recs)} done", flush=True)
send("quit")
proc.stdin.close()
proc.wait(timeout=30)
print(f"DONE {done} records, exe {exe_sha[:12]}, negate {NEGATE}", flush=True)
