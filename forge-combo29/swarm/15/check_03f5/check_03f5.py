#!/usr/bin/env python3
"""check_03f5.py EXE FENFILE [--limit N] [--depth 5]

Check of seat 03's S-F5: "perft 5 agrees exactly with python-chess on 230 positions (200 random R +
the first 30 of G): 1,150 of 1,150 (position, depth) values equal, perft-5 sum 3,925,995,728 on both
sides, 0 refused FENs, 0 crashes, 0 error lines, and the perft-1 move sets identical."

MY OWN harness and MY OWN position set (seed 1511 R + first 30 of G), so this is an independent
reproduction of the CLAIM (move generation agrees to depth 5 and the sums match), not of their files.
I cannot reproduce their exact 3,925,995,728 without their exact 230 positions; I report my own sum
and the agreement rate, and I say plainly which of their numbers I could and could not check.

python-chess is the reference. Every mismatch is listed with its divide.
"""
import argparse
import json
import sys

import chess

ENGINE_LINE = None


def engine_perft(exe, fen, depth, limit=1200):
    """-> dict move_uci -> nodes, plus a list of error lines. Reads until the totals line."""
    import queue
    import re
    import subprocess
    import threading
    import time
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
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
                return "TIMEOUT"
            try:
                line = q.get(timeout=rem)
            except queue.Empty:
                return "TIMEOUT"
            if line is None:
                return "EOF"
            out.append(line)
            if pred(line):
                return "OK"

    out = []
    send("uci"); wait(lambda l: l.startswith("uciok"), 30)
    send("setoption name Threads value 1"); send("setoption name Hash value 16")
    send("isready"); wait(lambda l: l == "readyok", 30)
    send("position fen " + fen); send("isready"); wait(lambda l: l == "readyok", 30)
    st = wait(lambda l: re.match(r"^nodes \d+", l) is not None, limit)
    send("quit") if st != "EOF" else None
    if st == "TIMEOUT":
        try:
            p.kill()
        except Exception:
            pass
    try:
        p.wait(timeout=5)
    except Exception:
        p.kill()
    # first send go perft AFTER setup; rebuild that here
    return out


def run_perft(exe, fen, depth, limit=1800):
    import queue
    import re
    import subprocess
    import threading
    import time
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    q = queue.Queue()

    def rd():
        for line in p.stdout:
            q.put(line.rstrip("\n"))
        q.put(None)

    threading.Thread(target=rd, daemon=True).start()

    def send(c):
        p.stdin.write(c + "\n"); p.stdin.flush()

    out = []

    def wait(pred, lim):
        t0 = time.monotonic()
        while True:
            rem = lim - (time.monotonic() - t0)
            if rem <= 0:
                return "TIMEOUT"
            try:
                line = q.get(timeout=rem)
            except queue.Empty:
                return "TIMEOUT"
            if line is None:
                return "EOF"
            out.append(line)
            if pred(line):
                return "OK"

    send("uci"); wait(lambda l: l.startswith("uciok"), 30)
    send("setoption name Threads value 1"); send("setoption name Hash value 16")
    send("isready"); wait(lambda l: l == "readyok", 30)
    send("position fen " + fen); send("isready"); wait(lambda l: l == "readyok", 30)
    send("go perft %d" % depth)
    st = wait(lambda l: re.match(r"^nodes \d+", l) is not None, limit)
    try:
        send("quit"); p.wait(timeout=10)
    except Exception:
        p.kill()
    div = {}
    errs = []
    total = None
    for l in out:
        m = re.match(r"^([a-h][1-8][a-h][1-8][qrbn]?): (\d+)$", l)
        if m:
            div[m.group(1)] = int(m.group(2))
        m2 = re.match(r"^nodes (\d+)$", l)
        if m2:
            total = int(m2.group(1))
        low = l.lower()
        if "invalid fen" in low or "illegal" in low or "unknown option" in low or "invalid value" in low:
            errs.append(l)
    return {"status": st, "total": total, "divide": div, "errors": errs}


def py_perft(fen, depth):
    board = chess.Board(fen)
    div = {}
    total = 0
    for mv in board.legal_moves:
        board.push(mv)
        n = 1
        # python-chess has no built-in perft; count by recursive walk
        def walk(b, d):
            if d == 0:
                return 1
            s = 0
            for m in b.legal_moves:
                b.push(m)
                s += walk(b, d - 1)
                b.pop()
            return s
        cnt = walk(board, depth - 1)
        board.pop()
        div[mv.uci()] = cnt
        total += cnt
    return total, div


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("fenfile")
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--depth", type=int, default=4)
    ap.add_argument("--out", default="check_03f5.jsonl")
    a = ap.parse_args()
    fens = []
    for line in open(a.fenfile, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        f = line.split()
        fens.append(" ".join(f[:4]) + " 0 1" if len(f) == 4 else " ".join(f[:6]))
        if len(fens) >= a.limit:
            break
    print("exe: %s  positions: %d  depth: %d" % (a.exe, len(fens), a.depth), flush=True)
    agree = 0
    mism = []
    sum_eng = 0
    sum_py = 0
    for i, fen in enumerate(fens):
        r = run_perft(a.exe, fen, a.depth)
        if r["status"] != "OK" or r["total"] is None:
            mism.append((fen, "ENGINE_%s" % r["status"], r["errors"]))
            continue
        pt, pdiv = py_perft(fen, a.depth)
        sum_eng += r["total"]
        sum_py += pt
        if r["total"] == pt and r["divide"] == pdiv:
            agree += 1
        else:
            mism.append((fen, "eng %s vs py %s" % (r["total"], pt),
                         {k: (r["divide"].get(k), pdiv.get(k)) for k in
                          set(r["divide"]) | set(pdiv)
                          if r["divide"].get(k) != pdiv.get(k)}))
        if (i + 1) % 5 == 0:
            print("  %d/%d  agree %d" % (i + 1, len(fens), agree), flush=True)
    print()
    print("positions: %d   AGREE (total AND full divide): %d   disagreements: %d"
          % (len(fens), agree, len(mism)))
    print("engine perft-%d sum: %d" % (a.depth, sum_eng))
    print("python perft-%d sum: %d" % (a.depth, sum_py))
    print("sums equal: %s" % (sum_eng == sum_py))
    for m in mism[:10]:
        print("  MISMATCH %s" % (m,))
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"exe": a.exe, "n": len(fens), "depth": a.depth,
                             "agree": agree, "mismatches": len(mism),
                             "sum_engine": sum_eng, "sum_python": sum_py}) + "\n")


if __name__ == "__main__":
    main()
