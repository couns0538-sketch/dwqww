#!/usr/bin/env python3
"""kimi5 job 38 oracle, after oracle_j34.py. On the PLAIN build (PC20, Threads 1, Hash 16).
Q/S/N records: ucinewgame, isready, position fen <FEN> moves <move>, go depth D;
  value = -(score); BEATS = value > the record's a=. D1 = max(1, d-1); D2 = d+2.
W records (n >= 1 hidden quiets): ucinewgame, isready, position fen <FEN>, go depth D
  searchmoves <hidden quiets>; value = the score as printed (NOT negated); BEATS = value > a=.
  D1 = d+1; D2 = d+4. A W record with n = 0 gets no search and no BEATS (beats = null).
--one-by-one: the C-W way for W records: each hidden quiet by itself the job-34 way
  (position fen <FEN> moves <quiet>, go depth max(1, d-1), value = -score); writes per-record
  BEST and per-quiet values. --hq-cap K limits to the first K hidden quiets of a record.
--alpha-override V: BEATS compares value > V instead of the record's a= (C-ALPHA).
--no-negate: do not negate Q/S/N values (the C-SIGN scratch way).
--kind Q|S|N|W, --limit K, --minhq A --maxhq B (W record filters), --parity P N.
A refusal line stops the run with 'refused' and the line.
Usage: oracle_j38.py <engine> <qsnw.log> <out.jsonl> <d1|d2> <optfile> --kind X [flags]
"""
import hashlib
import json
import subprocess
import sys

ENGINE, LOG, OUT, DMODE, OPTFILE = sys.argv[1:6]
KIND = None
NEGATE = True
PARITY, NPAR, LIMIT = 0, 1, None
MINHQ, MAXHQ = 0, 10**9
ONE_BY_ONE = False
HQ_CAP = None
ALPHA_OVERRIDE = None
args = sys.argv[6:]
i = 0
while i < len(args):
    if args[i] == "--kind":
        KIND = args[i + 1]; i += 2
    elif args[i] == "--no-negate":
        NEGATE = False; i += 1
    elif args[i] == "--parity":
        PARITY, NPAR = int(args[i + 1]), int(args[i + 2]); i += 3
    elif args[i] == "--limit":
        LIMIT = int(args[i + 1]); i += 2
    elif args[i] == "--minhq":
        MINHQ = int(args[i + 1]); i += 2
    elif args[i] == "--maxhq":
        MAXHQ = int(args[i + 1]); i += 2
    elif args[i] == "--one-by-one":
        ONE_BY_ONE = True; i += 1
    elif args[i] == "--hq-cap":
        HQ_CAP = int(args[i + 1]); i += 2
    elif args[i] == "--alpha-override":
        ALPHA_OVERRIDE = int(args[i + 1]); i += 2
    else:
        raise SystemExit(f"bad arg {args[i]}")
if KIND not in ("Q", "S", "N", "W"):
    raise SystemExit("--kind Q|S|N|W required")

REFUSALS = ("illegal move", "invalid FEN", "unknown option", "invalid value", "ERROR")

recs = []
for line in open(LOG):
    if f" info string {KIND}38 " not in line:
        continue
    parts = line.split()
    kv = {}
    for tok in parts[4:]:
        if tok.startswith("fen="):
            break
        k, _, v = tok.partition("=")
        kv[k] = v
    fen = line.split(" fen=", 1)[1].rstrip("\n")
    r = {"idx": int(parts[0]), "cls": KIND, "d": int(kv["d"]), "a": int(kv["a"]),
         "p": int(kv["p"]), "mv": kv["mv"] if KIND != "W" else None, "fen": fen}
    if KIND in ("Q", "S"):
        r["l"] = int(kv["l"])
    if KIND == "Q":
        r["e"] = int(kv["e"]); r["i"] = int(kv["i"]); r["s"] = int(kv["s"])
    if KIND in ("S", "N"):
        r["k"] = int(kv["k"])
    if KIND == "N":
        r["t"] = kv["t"]
    if KIND == "W":
        r["c"] = kv["c"]; r["n"] = int(kv["n"]); r["b"] = int(kv["b"])
        r["hq"] = kv["hq"].split(",") if kv["hq"] else []
    recs.append(r)
if KIND == "W":
    recs = [r for r in recs if MINHQ <= r["n"] <= MAXHQ]
if LIMIT is not None:
    recs = recs[:LIMIT]
recs = [r for j, r in enumerate(recs) if j % NPAR == PARITY]
print(f"records to do: {len(recs)} (kind {KIND}, parity {PARITY}/{NPAR}, mode {DMODE}, "
      f"negate {NEGATE}, one_by_one {ONE_BY_ONE})", flush=True)

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

def check(lines, where):
    for l in lines:
        if any(x in l for x in REFUSALS):
            raise SystemExit(f"refused at {where}: {l}")

def search_score(pos_line, go_line, where):
    send("ucinewgame")
    send("isready")
    check(read_until("readyok"), where)
    send(pos_line)
    send(go_line)
    lines = read_until("bestmove")
    check(lines, where)
    score = None
    for l in lines:
        if l.startswith("info depth") and " score " in l:
            p = l.split()
            j = p.index("score")
            if p[j + 1] == "cp":
                score = int(p[j + 2])
            elif p[j + 1] == "mate":
                score = 30000 if int(p[j + 2]) > 0 else -30000
    return score

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
check(uci_lines + ready, "setup")

done = 0
with open(OUT, "w") as out:
    for r in recs:
        alpha = ALPHA_OVERRIDE if ALPHA_OVERRIDE is not None else r["a"]
        if KIND == "W" and ONE_BY_ONE:
            values = []
            quiets = r["hq"][:HQ_CAP] if HQ_CAP is not None else r["hq"]
            for q in quiets:
                sc = search_score(f"position fen {r['fen']} moves {q}", f"go depth {max(1, r['d'] - 1)}",
                                  f"record {done}")
                ns = sc is None
                values.append((q, None if ns else -sc))
            best = max((v for _, v in values if v is not None), default=None)
            out.write(json.dumps({**r, "hq_used": quiets, "values": values, "best": best,
                                  "best_beats": (best is not None and best > alpha)}) + "\n")
        elif KIND == "W":
            if r["n"] < 1:
                out.write(json.dumps({**r, "D": None, "score": None, "value": None,
                                      "beats": None, "noscore": True}) + "\n")
            else:
                D = r["d"] + 1 if DMODE == "d1" else r["d"] + 4
                sc = search_score(f"position fen {r['fen']}",
                                  f"go depth {D} searchmoves {' '.join(r['hq'])}", f"record {done}")
                noscore = sc is None
                value = 0 if noscore else sc
                beats = (not noscore) and value > alpha
                out.write(json.dumps({**r, "D": D, "score": sc if not noscore else 0,
                                      "value": value, "beats": beats, "noscore": noscore}) + "\n")
        else:
            D = max(1, r["d"] - 1) if DMODE == "d1" else r["d"] + 2
            sc = search_score(f"position fen {r['fen']} moves {r['mv']}", f"go depth {D}",
                              f"record {done}")
            noscore = sc is None
            if noscore:
                sc = 0
            value = -sc if NEGATE else sc
            beats = (not noscore) and value > alpha
            out.write(json.dumps({**r, "D": D, "score": sc, "value": value,
                                  "beats": beats, "noscore": noscore}) + "\n")
        done += 1
        if done % 500 == 0:
            print(f"{done}/{len(recs)} done", flush=True)
send("quit")
proc.stdin.close()
proc.wait(timeout=30)
print(f"DONE {done} records, exe {exe_sha[:12]}, kind {KIND}", flush=True)
