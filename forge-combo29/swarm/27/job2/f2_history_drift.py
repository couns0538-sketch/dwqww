#!/usr/bin/env python3
"""f2_history_drift.py <exe> <fens-file> <outdir> [--depth D] [--limit N]

Quantifies the history carry-over: each position is searched
  (i)  in a FRESH process ("cold"),
  (ii) in ONE process after a fixed warm-up position, in a fixed order ("warm").
For every position: node count, score and bestmove of the last finished iteration are compared.
A difference in any of the three means the same engine, same options, same depth answered
differently because of state left behind by an earlier search.

Every engine process is paced (one line at a time, bestmove awaited), because a whole-session
write aborts each search with the next command.
"""
import argparse
import os
import re
import subprocess
import sys
import time

S14 = """setoption name LmrQuietBase value 93
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
setoption name NonPawnCorrection value true"""

WARMUP = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"


class Engine:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.buf = []
        self.send("uci")
        self.await_("uciok")
        for line in S14.splitlines():
            self.send(line)
        self.send("isready")
        self.await_("readyok")

    def send(self, line):
        self.p.stdin.write(line + "\n")
        self.p.stdin.flush()

    def await_(self, token, timeout=180):
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            line = self.p.stdout.readline()
            if not line:
                break
            self.buf.append(line.rstrip("\n"))
            if line.strip() == token or line.startswith(token):
                return True
        return False

    def search(self, fen, depth, timeout=180):
        self.send("ucinewgame")
        self.send("isready")
        self.await_("readyok")
        self.send("position fen " + fen)
        self.send("isready")
        self.await_("readyok")
        self.send("go depth %d" % depth)
        t0 = time.monotonic()
        infos = []
        bm = None
        while time.monotonic() - t0 < timeout:
            line = self.p.stdout.readline()
            if not line:
                break
            s = line.strip()
            self.buf.append(s)
            if s.startswith("info depth"):
                infos.append(s)
            if s.startswith("bestmove"):
                bm = s.split()[1]
                break
        last = infos[-1] if infos else ""
        n = re.search(r"nodes (\d+)", last)
        sc = re.search(r"score (cp|mate) (-?\d+)", last)
        dp = re.search(r"depth (\d+)", last)
        return {"fen": fen, "bestmove": bm,
                "nodes": int(n.group(1)) if n else None,
                "score": (sc.group(1), int(sc.group(2))) if sc else None,
                "depth": int(dp.group(1)) if dp else None,
                "last_info": last}

    def search_warm(self, fen, depth, timeout=180):
        """Same as search() but WITHOUT ucinewgame: the histories carry over on purpose."""
        self.send("position fen " + fen)
        self.send("isready")
        self.await_("readyok")
        self.send("go depth %d" % depth)
        t0 = time.monotonic()
        infos = []
        bm = None
        while time.monotonic() - t0 < timeout:
            line = self.p.stdout.readline()
            if not line:
                break
            s = line.strip()
            self.buf.append(s)
            if s.startswith("info depth"):
                infos.append(s)
            if s.startswith("bestmove"):
                bm = s.split()[1]
                break
        last = infos[-1] if infos else ""
        n = re.search(r"nodes (\d+)", last)
        sc = re.search(r"score (cp|mate) (-?\d+)", last)
        dp = re.search(r"depth (\d+)", last)
        return {"fen": fen, "bestmove": bm,
                "nodes": int(n.group(1)) if n else None,
                "score": (sc.group(1), int(sc.group(2))) if sc else None,
                "depth": int(dp.group(1)) if dp else None,
                "last_info": last}

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=30)
        except Exception:
            self.p.kill()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("fens")
    ap.add_argument("outdir")
    ap.add_argument("--depth", type=int, default=10)
    ap.add_argument("--limit", type=int, default=40)
    args = ap.parse_args()
    exe = os.path.realpath(args.exe)
    os.makedirs(args.outdir, exist_ok=True)
    fens = [ln.strip() for ln in open(args.fens) if ln.strip()
            and not ln.startswith("#")][:args.limit]

    cold = []
    for fen in fens:
        e = Engine(exe)
        cold.append(e.search(fen, args.depth))
        e.close()

    # warm run: one process, warm-up first, then every position in order with no ucinewgame
    e = Engine(exe)
    e.search(WARMUP, args.depth)
    warm = []
    for fen in fens:
        warm.append(e.search_warm(fen, args.depth))
    e.close()

    rows = []
    for c, w in zip(cold, warm):
        same_nodes = c["nodes"] == w["nodes"]
        same_score = c["score"] == w["score"]
        same_bm = c["bestmove"] == w["bestmove"]
        delta = ""
        if c["score"] and w["score"] and c["score"][0] == w["score"][0] == "cp":
            delta = w["score"][1] - c["score"][1]
        rows.append({
            "fen": c["fen"], "cold_bm": c["bestmove"], "warm_bm": w["bestmove"],
            "cold_nodes": c["nodes"], "warm_nodes": w["nodes"],
            "cold_score": c["score"], "warm_score": w["score"],
            "same_bm": same_bm, "same_nodes": same_nodes, "same_score": same_score,
            "cp_delta": delta, "cold_last": c["last_info"], "warm_last": w["last_info"],
        })

    tot = len(rows)
    diff_bm = sum(1 for r in rows if not r["same_bm"])
    diff_nodes = sum(1 for r in rows if not r["same_nodes"])
    diff_score = sum(1 for r in rows if not r["same_score"])
    deltas = [abs(r["cp_delta"]) for r in rows if isinstance(r["cp_delta"], int)]
    with open(os.path.join(args.outdir, "table.txt"), "w") as f:
        f.write("| fen | cold bm | warm bm | cold nodes | warm nodes | cold score | warm score | cp delta |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for r in rows:
            f.write("| %s | %s | %s | %s | %s | %s %s | %s %s | %s |\n" % (
                r["fen"], r["cold_bm"], r["warm_bm"], r["cold_nodes"], r["warm_nodes"],
                r["cold_score"][0] if r["cold_score"] else "-",
                r["cold_score"][1] if r["cold_score"] else "-",
                r["warm_score"][0] if r["warm_score"] else "-",
                r["warm_score"][1] if r["warm_score"] else "-",
                r["cp_delta"]))
    with open(os.path.join(args.outdir, "RESULT.txt"), "w") as f:
        f.write("exe: %s\n" % exe)
        f.write("sha256: %s\n" % subprocess.run(["sha256sum", exe], capture_output=True,
                                                 text=True).stdout.split()[0])
        f.write("depth: %d\npositions: %d\nwarmup: %s\n" % (args.depth, tot, WARMUP))
        f.write("date_utc: %s\n" % subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                                   capture_output=True, text=True).stdout.strip())
        f.write("\ncold  = fresh process per position, ucinewgame before the search\n")
        f.write("warm  = one process, one warm-up search, then every position with no ucinewgame\n")
        f.write("\nbestmove differs : %d of %d\n" % (diff_bm, tot))
        f.write("nodes differ     : %d of %d\n" % (diff_nodes, tot))
        f.write("score differs    : %d of %d\n" % (diff_score, tot))
        if deltas:
            deltas.sort()
            f.write("cp delta warm-cold: median %.1f, max %d, mean %.1f\n" % (
                deltas[len(deltas) // 2], deltas[-1], sum(deltas) / len(deltas)))
    print(open(os.path.join(args.outdir, "RESULT.txt")).read())


if __name__ == "__main__":
    main()
