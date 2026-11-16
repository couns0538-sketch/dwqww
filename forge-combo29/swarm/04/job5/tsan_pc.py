#!/usr/bin/env python3
"""tsan_pc.py — ThreadSanitizer verdict for the PC build (r15), WITH the planted-fault proof.

Area 4 requires BOTH proofs before a "0 sanitizer lines" result counts:
  (1) the .meta records `nm -C <exe> | grep -c __tsan_` > 0 for the exe actually run;
  (2) a scratch copy with ONE planted fault, built the same way and driven by THIS SAME RUNNER, is reported.

The planted fault used here is an unlocked global counter incremented at the top of Worker::search, so every
worker writes it and TSan must report the pair. If the planted build does not produce a report through this
runner, the runner cannot count sanitizer lines and the real build's zero means "not shown".

Every search is a fresh process; `ucinewgame` before `position` (seat 10's cold-start rule).

Usage: tsan_pc.py REAL_EXE PLANTED_EXE OUTDIR --settings pc20 --threads 1,4 --depth 12 --runs 2
"""
import argparse
import json
import os
import queue
import subprocess
import sys
import threading
import time

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5),
       ("LmpBase", 8), ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24),
       ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212), ("SingularDepth", 6),
       ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
ORD = "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"


def opts_for(name, threads):
    base = [("Hash", 16), ("Threads", threads)]
    if name == "none":
        return base
    if name == "s14":
        return base + S14 + [("OwnBook", "false")]
    return base + S14 + PC20_EXTRA


def nmcount(exe):
    r = subprocess.run("nm -C %s | grep -c __tsan_" % exe, shell=True,
                       capture_output=True, text=True)
    try:
        return int(r.stdout.strip() or 0)
    except ValueError:
        return 0


def run(exe, fen, opts, depth, limit):
    env = dict(os.environ)
    env.pop("ASAN_OPTIONS", None)
    env.pop("TSAN_OPTIONS", None)
    env["TSAN_OPTIONS"] = "halt_on_error=0 second_deadlock_stack=1"
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1, env=env)
    q = queue.Queue()
    threading.Thread(target=lambda: [q.put(l.rstrip("\r\n")) for l in p.stdout], daemon=True).start()
    err = []
    threading.Thread(target=lambda: [err.append(l.rstrip()) for l in p.stderr], daemon=True).start()
    problems = []

    def send(c):
        try:
            p.stdin.write(c + "\n")
            p.stdin.flush()
        except (BrokenPipeError, ValueError):
            pass

    def until(tok, lim=180.0):
        got = []
        deadline = time.monotonic() + lim
        while time.monotonic() < deadline:
            try:
                ln = q.get(timeout=0.05)
            except queue.Empty:
                if p.poll() is not None and q.empty():
                    break
                continue
            got.append(ln)
            if ln == tok or ln.startswith(tok):
                return got, True
        return got, False

    send("uci")
    until("uciok", 60)
    for name, val in opts:
        send("setoption name %s value %s" % (name, val))
        send("isready")
        lines, ok = until("readyok", 60)
        if not ok:
            problems.append("no readyok after %s" % name)
        for ln in lines:
            if "unknown option" in ln or "invalid value" in ln:
                problems.append("refused: " + ln)
    send("ucinewgame")
    send("isready")
    until("readyok", 60)
    send("position fen " + fen)
    send("isready")
    lines, _ = until("readyok", 60)
    for ln in lines:
        if "invalid FEN" in ln:
            problems.append("invalid FEN: " + ln)
    t0 = time.monotonic()
    send("go depth %d" % depth)
    got, ok = until("bestmove", limit)
    wall = time.monotonic() - t0
    if not ok:
        problems.append("no bestmove within %ss" % limit)
    send("quit")
    try:
        p.wait(timeout=30)
    except Exception:
        p.kill()
    time.sleep(0.4)   # let the stderr pump finish
    reports = sum(1 for l in err if l.startswith("WARNING: ThreadSanitizer") or
                  l.strip().startswith("WARNING: ThreadSanitizer"))
    mv = ""
    for ln in got:
        if ln.startswith("bestmove"):
            mv = ln
    return {"bestmove": mv, "move": mv.split()[1] if len(mv.split()) > 1 else "",
            "wall": round(wall, 2), "tsan_reports": reports,
            "problems": problems, "stderr": err}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("real_exe")
    ap.add_argument("planted_exe")
    ap.add_argument("outdir")
    ap.add_argument("--settings", default="pc20")
    ap.add_argument("--threads", default="1,4")
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--limit", type=float, default=300.0)
    ap.add_argument("--fen", default=ORD)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    rm, pm = nmcount(a.real_exe), nmcount(a.planted_exe)
    print("proof 1: nm -C | grep -c __tsan_   real=%d  planted=%d" % (rm, pm))
    if rm <= 0 or pm <= 0:
        print("INTEGRITY FAILURE: a build without __tsan_ symbols cannot show sanitizer lines")
        sys.exit(1)

    rows = []
    print()
    print("== proof 2: the planted fault must be REPORTED through this runner ==")
    for th in [int(x) for x in a.threads.split(",")]:
        r = run(a.planted_exe, a.fen, opts_for(a.settings, th), a.depth, a.limit)
        r.update({"exe": a.planted_exe, "role": "planted", "threads": th})
        rows.append(r)
        print("  planted T%-3d tsan_reports=%d move=%s %s"
              % (th, r["tsan_reports"], r["move"], "; ".join(r["problems"])))
    planted_ok = any(r["tsan_reports"] > 0 for r in rows if r["role"] == "planted")
    if not planted_ok:
        print("INTEGRITY FAILURE: the planted fault produced no report — the runner cannot count"
              " sanitizer lines, so the real build's result would be 'not shown'")
        for r in rows:
            os.makedirs(a.outdir, exist_ok=True)
        with open(os.path.join(a.outdir, "tsan_pc.jsonl"), "w") as f:
            for r in rows:
                f.write(json.dumps({k: v for k, v in r.items() if k != "stderr"}) + "\n")
        sys.exit(1)

    print()
    print("== the real PC build under the same runner ==")
    real_rows = []
    for th in [int(x) for x in a.threads.split(",")]:
        for i in range(a.runs):
            r = run(a.real_exe, a.fen, opts_for(a.settings, th), a.depth, a.limit)
            r.update({"exe": a.real_exe, "role": "real", "threads": th, "run": i})
            real_rows.append(r)
            rows.append(r)
            print("  real    T%-3d r%d tsan_reports=%d move=%-6s %5.2fs %s"
                  % (th, i, r["tsan_reports"], r["move"], r["wall"], "; ".join(r["problems"])))
    if os.path.exists("/home/ubuntu/runs/pctsan"):
        pass
    with open(os.path.join(a.outdir, "tsan_pc.jsonl"), "w") as f:
        for r in rows:
            f.write(json.dumps({k: v for k, v in r.items() if k != "stderr"}) + "\n")
    os.makedirs(os.path.join(a.outdir, "stderr"), exist_ok=True)
    for idx, r in enumerate(rows):
        if r["stderr"]:
            open(os.path.join(a.outdir, "stderr", "%02d_%s_t%d.txt"
                              % (idx, r["role"], r["threads"])), "w").write("\n".join(r["stderr"]))

    probs = [r for r in real_rows if r["problems"]]
    print()
    if probs:
        print("INTEGRITY FAILURE: %d real run(s) had problems" % len(probs))
        for r in probs[:5]:
            print("   T%d: %s" % (r["threads"], "; ".join(r["problems"])))
        sys.exit(1)
    total = sum(r["tsan_reports"] for r in real_rows)
    print("VERDICT: %d sanitizer report(s) from the real PC build over %d runs, with proof 1 (nm=%d)"
          " and proof 2 (planted reported=%d) both satisfied."
          % (total, len(real_rows), rm, sum(r["tsan_reports"] for r in rows if r["role"] == "planted")))


if __name__ == "__main__":
    main()
