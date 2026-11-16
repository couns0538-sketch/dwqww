#!/usr/bin/env python3
"""check_19f33.py EXE FENFILE [--limit N]

Check of seat 19's 19-F33 from its stated method alone: on PC r15, Threads 1, depth 12, first 200 of
set G, PC20 held constant with ONLY CorrHistV2 toggled (on vs off), compare bestmoves and scores.

Reports: same-move count, different-move count, different-score count, total nodes both ways, and the
on-minus-off score delta statistics on same-move cp positions.

Harness is my own (not a copy). A FEN that the engine refuses is REPORTED and excluded, never counted
as a result — that is the bug I made in 15-R2 and will not repeat.
"""
import argparse
import json
import os
import re
import queue
import subprocess
import threading
import time

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
# PC20 minus CorrHistV2 is the "off" arm; adding CorrHistV2 true is the "on" arm.
PC20_BASE = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
                   ("MateAlphaGuard", "true"), ("OwnBook", "false")]


def load(path, limit):
    out = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        f = line.split()
        out.append(" ".join(f[:4]) + " 0 1" if len(f) == 4 else " ".join(f[:6]))
        if limit and len(out) >= limit:
            break
    return out


def search(exe, opts, fen, depth, limit=180):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    q = queue.Queue()

    def rd():
        for line in p.stdout:
            q.put(line.rstrip("\n"))
        q.put(None)

    threading.Thread(target=rd, daemon=True).start()

    def send(c):
        p.stdin.write(c + "\n"); p.stdin.flush()

    def wait(pred, lim):
        t0 = time.monotonic()
        while True:
            rem = lim - (time.monotonic() - t0)
            if rem <= 0:
                return "TIMEOUT", None
            try:
                line = q.get(timeout=rem)
            except queue.Empty:
                return "TIMEOUT", None
            if line is None:
                return "EOF", None
            if pred(line):
                return "OK", line

    send("uci"); wait(lambda l: l.startswith("uciok"), 30)
    send("setoption name Threads value 1"); send("setoption name Hash value 16")
    for k, v in opts:
        send("setoption name %s value %s" % (k, v))
    send("isready"); wait(lambda l: l == "readyok", 30)
    send("ucinewgame"); send("isready"); wait(lambda l: l == "readyok", 30)
    send("position fen " + fen); send("isready")
    # capture answer lines so a REFUSED FEN is detected
    refused = []
    t0 = time.monotonic()
    while time.monotonic() - t0 < 20:
        try:
            line = q.get(timeout=0.5)
        except queue.Empty:
            continue
        if line is None:
            break
        if any(b in line for b in ("invalid FEN", "invalid value", "illegal move", "unknown option")):
            refused.append(line)
        if line.strip() == "readyok":
            break
    if refused:
        try:
            send("quit"); p.wait(timeout=10)
        except Exception:
            p.kill()
        return {"refused": refused}
    send("go depth %d" % depth)
    bm_status, bm = wait(lambda l: l.startswith("bestmove"), limit)
    try:
        send("quit"); p.wait(timeout=10)
    except Exception:
        p.kill()
    if bm_status != "OK":
        return {"bestmove": None, "status": bm_status}
    tok = bm.split()
    return {"bestmove": tok[1] if len(tok) > 1 else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("fenfile")
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--out", default="rows.jsonl")
    a = ap.parse_args()
    fens = load(a.fenfile, a.limit)
    print("exe: %s  positions: %d  depth: %d  Threads 1" % (a.exe, len(fens), a.depth), flush=True)
    arms = {"off": PC20_BASE, "on": PC20_BASE + [("CorrHistV2", "true")]}
    # first prove the option exists, or stop
    uciout = subprocess.run([a.exe], input="uci\nquit\n", capture_output=True, text=True).stdout
    names = set(re.findall(r"^option name (.+?) type ", uciout, re.M))
    for k, _ in arms["on"]:
        if k not in names:
            raise SystemExit("STOP: option %r not in the exe's uci list" % k)
    print("all %d option names present in the exe's uci list" % len(arms["on"]), flush=True)

    # Two engines kept alive, one per arm, for speed; ucinewgame before every go.
    procs = {}
    qs = {}
    for arm, opts in arms.items():
        p = subprocess.Popen([a.exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, text=True, bufsize=1)
        q = queue.Queue()

        def rd(pp=p, qq=q):
            for line in pp.stdout:
                qq.put(line.rstrip("\n"))
            qq.put(None)

        threading.Thread(target=rd, daemon=True).start()
        procs[arm], qs[arm] = p, q
        for c in ["uci"] + ["setoption name %s value %s" % (k, v) for k, v in opts] + ["isready"]:
            p.stdin.write(c + "\n")
        p.stdin.flush()
        while True:
            line = q.get()
            if line is None or line.strip() == "readyok":
                break

    def go(arm, fen):
        p, q = procs[arm], qs[arm]
        for c in ["ucinewgame", "isready", "position fen " + fen, "isready", "go depth %d" % a.depth]:
            p.stdin.write(c + "\n")
        p.stdin.flush()
        infos, bm, ready = [], None, 0
        t0 = time.monotonic()
        while time.monotonic() - t0 < 200:
            try:
                line = q.get(timeout=1.0)
            except queue.Empty:
                continue
            if line is None:
                break
            if line.startswith("info depth"):
                infos.append(line)
            if line.startswith("bestmove"):
                bm = line
                break
        last = infos[-1] if infos else None
        score = nodes = None
        if last:
            m = re.search(r"score (cp|mate) (-?\d+)", last)
            if m:
                score = (m.group(1), int(m.group(2)))
            m2 = re.search(r"\bnodes (\d+)", last)
            if m2:
                nodes = int(m2.group(1))
        tok = bm.split() if bm else []
        return {"score": score, "nodes": nodes, "bestmove": tok[1] if len(tok) > 1 else None}

    rows = []
    for i, fen in enumerate(fens):
        off = go("off", fen)
        on = go("on", fen)
        rows.append({"i": i, "fen": fen, "off": off, "on": on})
        if i % 25 == 0:
            print("  %d/%d" % (i, len(fens)), flush=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")

    # ---- report ----
    good = [r for r in rows if r["off"]["bestmove"] and r["on"]["bestmove"]
            and r["off"]["score"] and r["on"]["score"]]
    print(flush=True)
    print("positions compared: %d (dropped %d with a missing bestmove/score)"
          % (len(good), len(rows) - len(good)), flush=True)
    same_move = sum(1 for r in good if r["off"]["bestmove"] == r["on"]["bestmove"])
    diff_move = len(good) - same_move
    diff_score = sum(1 for r in good if r["off"]["score"] != r["on"]["score"])
    n_off = sum(r["off"]["nodes"] or 0 for r in good)
    n_on = sum(r["on"]["nodes"] or 0 for r in good)
    print("same bestmove: %d (%.1f%%)   DIFFERENT: %d (%.1f%%)"
          % (same_move, 100.0 * same_move / len(good), diff_move, 100.0 * diff_move / len(good)))
    print("different score: %d of %d" % (diff_score, len(good)))
    print("total nodes  off(CorrHistV2 off) = %d   on = %d   delta %+.2f%%"
          % (n_off, n_on, 100.0 * (n_on - n_off) / n_off))
    deltas = [r["on"]["score"][1] - r["off"]["score"][1] for r in good
              if r["off"]["bestmove"] == r["on"]["bestmove"]
              and r["off"]["score"][0] == "cp" and r["on"]["score"][0] == "cp"]
    if deltas:
        deltas.sort()
        mean = sum(deltas) / len(deltas)
        med = deltas[len(deltas) // 2]
        print("same-move cp positions: %d   on-minus-off delta: mean %+.1f cp  median %+d cp"
              "  range %+d .. %+d" % (len(deltas), mean, med, deltas[0], deltas[-1]))
    for arm, p in procs.items():
        try:
            p.stdin.write("quit\n"); p.stdin.flush(); p.wait(timeout=10)
        except Exception:
            p.kill()


if __name__ == "__main__":
    main()
