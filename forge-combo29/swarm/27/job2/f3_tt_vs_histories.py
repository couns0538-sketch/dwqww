#!/usr/bin/env python3
"""f3_tt_vs_histories.py <exe> <fens> <outdir>

Isolates the cause of the drift f2 measured. Three ways to search position X after a warm-up:
  (a) no clearing at all                       -> histories AND the TT carry over
  (b) `ucinewgame` (searcher.clear())          -> histories AND the TT are cleared
  (c) `setoption name Clear Hash`              -> the TT is cleared, the HISTORIES ARE NOT
      (Searcher::clear_hash() in src/search.cpp:2666-2669 clears shared_.tt and calls
       worker->clear_caches(), which is only evaluator_.clear(); Worker::clear() -- which zeroes
       ButterflyHistory etc., src/search.cpp:1019-1030 -- is NOT called.)
So (c) keeps exactly the histories and drops the table. If (c) still differs from (b), the history
state is what moved the answer.
`ucinewgame` is sent ONCE at the start of each variant; the difference is only what is sent
between the warm-up and the measurement.
"""
import argparse
import os
import re
import subprocess
import sys
import time

S14 = [l for l in """setoption name LmrQuietBase value 93
setoption name LmrQuietDivisor value 205
setoption name LmrNoisyBase value 13
setoption name LmrNoisyDivisor value 333
setoption name LmrHistoryDivisor value 5643
setoption name NullMoveBase value 5
setoption name LmpBase value 8
setoption name HistoryPruneMultiplier value 2220
setoption name HistoryBonusQuadratic value 24
setoption name HistoryBonusLinear value 54
setoption name HistoryBonusMax value 2212
setoption name SingularDepth value 6
setoption name IirDepth value 2
setoption name NonPawnCorrection value true""".splitlines() if l.strip()]

WARMUP = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"


class Engine:
    def __init__(self, exe, threads=1, hash_mb=16):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.send("uci"); self.await_("uciok")
        self.send("setoption name Hash value %d" % hash_mb)
        self.send("setoption name Threads value %d" % threads)
        for line in S14:
            self.send(line)
        self.send("isready"); self.await_("readyok")
        self.send("ucinewgame"); self.send("isready"); self.await_("readyok")

    def send(self, line):
        self.p.stdin.write(line + "\n"); self.p.stdin.flush()

    def await_(self, token, timeout=180):
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            line = self.p.stdout.readline()
            if not line:
                return False
            if line.strip() == token:
                return True
        return False

    def go(self, fen, depth):
        self.send("position fen " + fen)
        self.send("isready"); self.await_("readyok")
        self.send("go depth %d" % depth)
        t0 = time.monotonic()
        infos, bm = [], None
        while time.monotonic() - t0 < 300:
            line = self.p.stdout.readline()
            if not line:
                break
            s = line.strip()
            if s.startswith("info depth"):
                infos.append(s)
            elif s.startswith("bestmove"):
                bm = s.split()[1]
                break
        # GUARD (S-W1): zero info lines => no score/nodes. Raise rather than record a None row.
        if not infos:
            raise RuntimeError("no 'info depth' line for %r (row aborted)" % fen)
        last = infos[-1]
        n = re.search(r"nodes (\d+)", last)
        sc = re.search(r"score (cp|mate) (-?\d+)", last)
        return {"bestmove": bm, "nodes": int(n.group(1)) if n else None,
                "score": (sc.group(1), int(sc.group(2))) if sc else None}

    def clear_hash(self):
        self.send("setoption name Clear Hash")
        self.send("isready"); self.await_("readyok")

    def ucinewgame(self):
        self.send("ucinewgame")
        self.send("isready"); self.await_("readyok")

    def close(self):
        try:
            self.send("quit"); self.p.wait(timeout=30)
        except Exception:
            self.p.kill()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe"); ap.add_argument("fens"); ap.add_argument("outdir")
    ap.add_argument("--depth", type=int, default=10)
    ap.add_argument("--limit", type=int, default=20)
    a = ap.parse_args()
    exe = os.path.realpath(a.exe)
    os.makedirs(a.outdir, exist_ok=True)
    fens = [l.strip() for l in open(a.fens) if l.strip()][:a.limit]

    def measure(clear):
        e = Engine(exe)
        e.go(WARMUP, a.depth)             # warm the histories
        out = []
        for fen in fens:
            if clear == "none":
                pass
            elif clear == "ucinewgame":
                e.ucinewgame()
            elif clear == "hash":
                e.clear_hash()
            out.append(e.go(fen, a.depth))
        e.close()
        return out

    no_clear = measure("none")
    with_newgame = measure("ucinewgame")
    with_hash_clear = measure("hash")

    def cmp(x, y):
        return {"bm": x["bestmove"] == y["bestmove"], "nodes": x["nodes"] == y["nodes"],
                "score": x["score"] == y["score"]}

    rows = []
    for i, fen in enumerate(fens):
        rows.append({
            "fen": fen,
            "no_clear": no_clear[i], "newgame": with_newgame[i], "hash": with_hash_clear[i],
            "vs_newgame_none": cmp(no_clear[i], with_newgame[i]),
            "vs_newgame_hash": cmp(with_hash_clear[i], with_newgame[i]),
        })

    n = len(rows)
    stat = {
        "no_clear_vs_ucinewgame": {k: sum(1 for r in rows if not r["vs_newgame_none"][k]) for k in ("bm", "nodes", "score")},
        "hash_clear_vs_ucinewgame": {k: sum(1 for r in rows if not r["vs_newgame_hash"][k]) for k in ("bm", "nodes", "score")},
    }

    with open(os.path.join(a.outdir, "table.txt"), "w") as f:
        f.write("| fen | bm none | bm ucinewgame | bm ClearHash | nodes none | nodes ucinewgame | nodes ClearHash | score none | score ucinewgame | score ClearHash |\n")
        f.write("|---|---|---|---|---|---|---|---|---|---|\n")
        for r in rows:
            def s(x):
                return ("%s %s" % x["score"]) if x["score"] else "-"
            f.write("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |\n" % (
                r["fen"], r["no_clear"]["bestmove"], r["newgame"]["bestmove"], r["hash"]["bestmove"],
                r["no_clear"]["nodes"], r["newgame"]["nodes"], r["hash"]["nodes"],
                s(r["no_clear"]), s(r["newgame"]), s(r["hash"])))
    with open(os.path.join(a.outdir, "RESULT.txt"), "w") as f:
        f.write("exe: %s\nsha256: %s\ndepth: %d\npositions: %d\ndate_utc: %s\n\n" % (
            exe, subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0],
            a.depth, n, subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                       capture_output=True, text=True).stdout.strip()))
        f.write("Differences from the ucinewgame baseline (histories AND table cleared):\n")
        f.write("  no clearing      : bestmove %d/%d, nodes %d/%d, score %d/%d\n" % (
            stat["no_clear_vs_ucinewgame"]["bm"], n, stat["no_clear_vs_ucinewgame"]["nodes"], n,
            stat["no_clear_vs_ucinewgame"]["score"], n))
        f.write("  Clear Hash only  : bestmove %d/%d, nodes %d/%d, score %d/%d   (table cleared, histories KEPT)\n" % (
            stat["hash_clear_vs_ucinewgame"]["bm"], n, stat["hash_clear_vs_ucinewgame"]["nodes"], n,
            stat["hash_clear_vs_ucinewgame"]["score"], n))
    print(open(os.path.join(a.outdir, "RESULT.txt")).read())


if __name__ == "__main__":
    main()
