#!/usr/bin/env python3
"""engine_perft.py EXE FENFILE MAXDEPTH OUTJSON [BATCH]
Sends, for every FEN line, `position fen <fen>` + isready, then `go perft d` for d = 1..MAXDEPTH,
one engine process per BATCH positions (a process that dies is restarted, the restart is recorded and counted).
Raw per-process transcripts go to OUTJSON.raw/ ; the JSON is {exe, results:{idx:{d:nodes}}, errors, restarts}.
An engine line containing an error word is recorded, never hidden."""
import json, os, subprocess, sys, time

EXE, FENFILE, MAXDEPTH, OUTJSON = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
BATCH = int(sys.argv[5]) if len(sys.argv) > 5 else 500
ERRWORDS = ("unknown option", "invalid value", "invalid FEN", "illegal move")

fens = [l.strip() for l in open(FENFILE) if l.strip()]
rawdir = OUTJSON + ".raw"
os.makedirs(rawdir, exist_ok=True)
results, errors, restarts = {}, [], []
stamp = lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class Engine:
    def __init__(self, rawpath):
        self.raw = open(rawpath, "w")
        self.p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)

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
            if any(w in s for w in ERRWORDS):
                errors.append((idx, what, s))

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
    e.send("isready"); e.read_until("readyok", lo, "isready")
    e.send("ucinewgame"); e.send("isready"); e.read_until("readyok", lo, "ucinewgame")
    for idx in range(lo, hi):
        e.send(f"position fen {fens[idx]}")
        e.send("isready")
        e.read_until("readyok", idx, "position")
        res.setdefault(idx, {})
        for d in range(1, MAXDEPTH + 1):
            e.send(f"go perft {d}")
            got, cur = None, idx
            while True:
                line = e.p.stdout.readline()
                if line == "":
                    raise RuntimeError(f"engine died at position {idx} depth {d}")
                e.raw.write(line); e.raw.flush()
                s = line.strip()
                if s.startswith("nodes "):
                    got = int(s.split()[1]); break
                if s.startswith("go perft") or s.startswith("perft "):
                    pass
                if any(w in s for w in ERRWORDS):
                    errors.append((idx, f"perft{d}", s))
            res[idx][d] = got
            cur = None
    e.close()
    return res


t0 = time.time()
for lo in range(0, len(fens), BATCH):
    hi = min(lo + BATCH, len(fens))
    attempt = 1
    while True:
        try:
            res = run_batch(lo, hi, attempt)
            results.update({str(k): v for k, v in res.items()})
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
                   "errors": errors, "restarts": restarts}, f)
    print(f"{hi}/{len(fens)} done {time.time()-t0:.1f}s", flush=True)

print(f"TOTAL {time.time()-t0:.1f}s, restarts {len(restarts)}, errors {len(errors)}")
