#!/usr/bin/env python3
"""engine_perft_t1.py EXE FENFILE MAXDEPTH OUTJSON BATCH [OPTIONPAIRS]
Identical to ../job1/engine_perft.py except that it sends, once per engine process, before any search:
    setoption name Threads value 1
    setoption name Hash value 16
and (optionally) any further `Name=Value` pairs given as the 6th argument, e.g. `CuckooRep=true,HistRework=2`.
Each setoption is followed by `isready` and the answer is read up to `readyok`, and the run STOPS on
`unknown option` / `invalid value` / `ERROR`.

Why this exists: the swarm rule of 2026-11-16T22:20Z requires any score to be reported at Threads 1. perft does
not use threads or the hash at all (Board::perft, src/board.cpp:1205-1222: a plain recursive walk, no hash probe,
no thread), but stating Threads 1 explicitly means no table of mine can be mistaken for a threaded one.
"""
import json
import os
import subprocess
import sys
import time

EXE, FENFILE, MAXDEPTH, OUTJSON = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
BATCH = int(sys.argv[5]) if len(sys.argv) > 5 else 500
EXTRA = []
if len(sys.argv) > 6 and sys.argv[6].strip():
    for pair in sys.argv[6].split(","):
        k, _, v = pair.partition("=")
        EXTRA.append((k.strip(), v.strip()))
ERRWORDS = ("unknown option", "invalid value", "invalid FEN", "illegal move", "ERROR")

fens = [l.strip().split("\t")[-1] for l in open(FENFILE) if l.strip()]
rawdir = OUTJSON + ".raw"
os.makedirs(rawdir, exist_ok=True)
results, errors, restarts = {}, [], []
stamp = lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class Engine:
    def __init__(self, rawpath):
        self.raw = open(rawpath, "w")
        self.p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.sent_options = []

    def send(self, cmd):
        self.raw.write(f">>> {cmd}\n")
        self.raw.flush()
        self.p.stdin.write(cmd + "\n")
        self.p.stdin.flush()

    def read_until(self, want, idx=None, what=""):
        lines = []
        while True:
            line = self.p.stdout.readline()
            if line == "":
                raise RuntimeError(f"engine died waiting for {want!r} {what} at position {idx}")
            self.raw.write(line)
            self.raw.flush()
            s = line.strip()
            lines.append(s)
            if s == want or s.startswith(want):
                return lines
            for w in ERRWORDS:
                if w in s:
                    errors.append((idx, what, s))
                    raise RuntimeError(f"engine refused a command ({what}): {s}")

    def close(self, timeout=120):
        try:
            self.send("quit")
        except Exception:  # noqa: BLE001
            pass
        try:
            self.p.wait(timeout=timeout)
        except Exception:  # noqa: BLE001
            self.p.kill()
        self.raw.close()


def run_batch(lo, hi, attempt):
    res = {}
    e = Engine(f"{rawdir}/batch_{lo:05d}_{hi:05d}.a{attempt}.txt")
    e.send("uci"); e.read_until("uciok", lo, "uci")
    # the swarm rule: Threads 1 stated explicitly, plus Hash 16 as the brief's sums use
    for name, val in [("Threads", "1"), ("Hash", "16")] + EXTRA:
        e.send(f"setoption name {name} value {val}")
        e.send("isready")
        e.read_until("readyok", lo, f"setoption {name}")
        e.sent_options.append((name, val))
    e.send("ucinewgame"); e.send("isready"); e.read_until("readyok", lo, "ucinewgame")
    for idx in range(lo, hi):
        e.send(f"position fen {fens[idx]}")
        e.send("isready")
        e.read_until("readyok", idx, "position")
        res.setdefault(idx, {})
        for d in range(1, MAXDEPTH + 1):
            e.send(f"go perft {d}")
            got = None
            while True:
                line = e.p.stdout.readline()
                if line == "":
                    raise RuntimeError(f"engine died at position {idx} depth {d}")
                e.raw.write(line); e.raw.flush()
                s = line.strip()
                if s.startswith("nodes "):
                    got = int(s.split()[1]); break
                for w in ERRWORDS:
                    if w in s:
                        errors.append((idx, f"perft{d}", s))
            res[idx][d] = got
    e.close()
    return res, e.sent_options


t0 = time.time()
sent = []
for lo in range(0, len(fens), BATCH):
    hi = min(lo + BATCH, len(fens))
    attempt = 1
    while True:
        try:
            res, opts = run_batch(lo, hi, attempt)
            results.update({str(k): v for k, v in res.items()})
            sent = opts
            break
        except Exception as ex:  # noqa: BLE001
            restarts.append({"range": [lo, hi], "attempt": attempt, "error": str(ex), "stamp": stamp()})
            print(f"RESTART {lo}-{hi} attempt {attempt}: {ex}", flush=True)
            attempt += 1
            if attempt > 3:
                for idx in range(lo, hi):
                    results.setdefault(str(idx), {})
                break
    with open(OUTJSON, "w") as f:
        json.dump({"exe": EXE, "fens": FENFILE, "maxdepth": MAXDEPTH, "results": results,
                   "errors": errors, "restarts": restarts,
                   "options_sent": sent}, f)
    print(f"{hi}/{len(fens)} done {time.time()-t0:.1f}s", flush=True)

print(f"TOTAL {time.time()-t0:.1f}s, restarts {len(restarts)}, errors {len(errors)}")
print(f"options sent per process: {sent}")
