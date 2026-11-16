#!/usr/bin/env python3
"""tsan_pc_sweep.py — TSan over MANY positions on the PC build, with per-thread-count planted proof.

Generalises job5/tsan_pc.py from one position to a list. For each position and thread count it runs the real
exe; the planted exe is run once per thread count so the proof covers every concurrency level used.

Writes one JSONL row per real search, plus a per-run stderr file whenever reports appear (so a finding always
has its raw TSan text beside it).

Usage: tsan_pc_sweep.py REAL PLANTED OUTDIR --positions F --threads 1,4 --depth 12 --limit 200
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


def opts_for(name, threads, hash_mb=16):
    base = [("Hash", hash_mb), ("Threads", threads)]
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
    time.sleep(0.3)
    reports = sum(1 for l in err if "WARNING: ThreadSanitizer" in l)
    mv = ""
    for ln in got:
        if ln.startswith("bestmove"):
            mv = ln
    return {"bestmove": mv, "move": mv.split()[1] if len(mv.split()) > 1 else "",
            "wall": round(wall, 2), "tsan_reports": reports, "problems": problems,
            "stderr": err}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("real_exe")
    ap.add_argument("planted_exe")
    ap.add_argument("outdir")
    ap.add_argument("--positions", required=True)
    ap.add_argument("--settings", default="pc20")
    ap.add_argument("--threads", default="1,4")
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--stop-after", type=int, default=15)
    ap.add_argument("--hash", type=int, default=16,
                    help="Hash in MB; small values force heavy TT eviction, which is the point of a table test")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    os.makedirs(os.path.join(a.outdir, "stderr"), exist_ok=True)
    fens = [l.strip().split(";")[0].strip() for l in open(a.positions) if l.strip()]
    fens = fens[:a.stop_after]
    threads = [int(x) for x in a.threads.split(",")]

    rm, pm = nmcount(a.real_exe), nmcount(a.planted_exe)
    print("proof 1 (nm __tsan_): real=%d planted=%d" % (rm, pm))
    if rm <= 0 or pm <= 0:
        print("INTEGRITY FAILURE: no __tsan_ symbols")
        sys.exit(1)
    print()
    print("proof 2: planted fault per thread count")
    planted_counts = {}
    for th in threads:
        r = run(a.planted_exe, fens[0], opts_for(a.settings, th, a.hash), min(a.depth, 10), a.limit)
        planted_counts[th] = r["tsan_reports"]
        print("  planted T%-3d reports=%d move=%s %s"
              % (th, r["tsan_reports"], r["move"], "; ".join(r["problems"])))
    if not any(v > 0 for v in planted_counts.values()):
        print("INTEGRITY FAILURE: planted fault never reported — a zero would be 'not shown'")
        sys.exit(1)

    print()
    rows = []
    total = 0
    print("%5s %-5s %-8s %10s %s" % ("pos", "thr", "move", "reports", "wall"))
    for i, fen in enumerate(fens):
        for th in threads:
            r = run(a.real_exe, fen, opts_for(a.settings, th, a.hash), a.depth, a.limit)
            r.update({"pos": i, "threads": th, "fen": fen, "exe": a.real_exe,
                      "settings": a.settings, "depth": a.depth, "hash_mb": a.hash})
            rows.append(r)
            total += r["tsan_reports"]
            print("%5d %-5d %-8s %10d %5.2fs %s"
                  % (i, th, r["move"] or "-", r["tsan_reports"], r["wall"],
                     ("PROBLEM:" + ";".join(r["problems"])) if r["problems"] else ""))
            if r["tsan_reports"] or r["problems"]:
                open(os.path.join(a.outdir, "stderr", "pos%02d_t%d.txt" % (i, th)), "w").write(
                    "\n".join(r["stderr"]))
            sys.stdout.flush()

    with open(os.path.join(a.outdir, "sweep.jsonl"), "w") as f:
        for r in rows:
            f.write(json.dumps({"pos": r["pos"], "threads": r["threads"], "fen": r["fen"],
                                "move": r["move"], "wall": r["wall"],
                                "tsan_reports": r["tsan_reports"],
                                "problems": r["problems"], "settings": r["settings"],
                                "depth": r["depth"]}) + "\n")
    probs = [r for r in rows if r["problems"]]
    print()
    print("searches: %d   positions: %d   thread counts: %s" % (len(rows), len(fens), threads))
    print("TOTAL TSan reports on the real build: %d" % total)
    print("planted proof per thread count: %s" % planted_counts)
    if probs:
        print("INTEGRITY FAILURE: %d search(es) had problems (see stderr/)" % len(probs))
        sys.exit(1)
    print("VERDICT: %s" % ("0 reports, with both proofs satisfied"
                           if total == 0 else "%d reports — see stderr/" % total))


if __name__ == "__main__":
    main()
