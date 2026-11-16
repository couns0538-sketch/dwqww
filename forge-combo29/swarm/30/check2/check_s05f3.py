#!/usr/bin/env python3
"""check_s05f3.py -- MY OWN check of seat 05's S-F3: is the fifty-move draw applied "early",
or is the H=91 drop simply where a depth-10 search meets halfmove 100?

Written from their finding sentence and their board. One process per case, synchronised:
position fen -> isready/readyok -> go depth D (with S14 options) -> wait for that search's
bestmove -> quit.

The measurement that separates "early threshold" from "horizon": hold the COUNTER at 91 and
change the DEPTH. If the threshold is a bug, depth 7 also reports cp 0 at H=91. If it is the
horizon, depth 7 cannot see ply 9 at all and must report a real score.

usage: check_s05f3.py EXE OUTDIR
"""
import json
import os
import subprocess
import sys
import threading
import time

S14 = [
    ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
    ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5),
    ("LmpBase", 8), ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24),
    ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212), ("SingularDepth", 6),
    ("IirDepth", 2), ("NonPawnCorrection", "true"),
]
BOARD = "1K6/8/8/3R4/8/8/8/k7 w - - %d 1"
RAMP = [0, 60, 75, 80, 85, 88, 90, 91, 92, 93, 94, 95, 99, 100]
DEPTHS = [7, 9, 10, 12]


def run(exe, fen, depth):
    rec = {"fen": fen, "depth": depth, "score": None, "bestmove": None, "nodes": None,
           "seldepth": None, "info_lines": 0, "san": []}
    env = {k: v for k, v in os.environ.items()
           if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS", "LSAN_OPTIONS")}
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1, env=env,
                         start_new_session=True)
    out, err = [], []
    lock = threading.Lock()

    def pump(stream, sink):
        try:
            for l in stream:
                with lock:
                    sink.append(l.rstrip("\n"))
        except Exception:
            pass

    threading.Thread(target=pump, args=(p.stdout, out), daemon=True).start()
    threading.Thread(target=pump, args=(p.stderr, err), daemon=True).start()

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def sync_ready(timeout=120.0):
        with lock:
            mark = len(out)
        send("isready")
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            with lock:
                if any(x.strip() == "readyok" for x in out[mark:]):
                    return True
            if p.poll() is not None:
                return False
            time.sleep(0.003)
        return False

    send("uci")
    time.sleep(0.05)
    for name, value in S14:
        send("setoption name %s value %s" % (name, value))
    sync_ready()
    send("position fen " + fen)
    sync_ready()
    with lock:
        mark = len(out)
    send("go depth %d" % depth)
    t0 = time.monotonic()
    while time.monotonic() - t0 < 300:
        with lock:
            if any(x.startswith("bestmove") for x in out[mark:]):
                break
        if p.poll() is not None:
            break
        time.sleep(0.005)
    with lock:
        block = list(out[mark:])
        rec["san"] = [l for l in err if "Sanitizer" in l or "runtime error" in l][:3]
    send("quit")
    try:
        p.wait(timeout=30)
    except Exception:
        pass
    infos = [l for l in block if l.startswith("info") and " pv" in l]
    rec["info_lines"] = len(infos)
    if infos:
        t = infos[-1].split()
        if "score" in t:
            i = t.index("score")
            rec["score"] = " ".join(t[i + 1:i + 3])
        for k in ("nodes", "seldepth"):
            if k in t:
                rec[k] = t[t.index(k) + 1]
    for l in block:
        if l.startswith("bestmove"):
            pr = l.split()
            rec["bestmove"] = pr[1] if len(pr) > 1 else ""
    return rec


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    rows = []
    print("=== A. their ramp at depth 10 (S14), board as they used it")
    for h in RAMP:
        r = run(exe, BOARD % h, 10)
        r["halfmove"], r["arm"] = h, "ramp"
        rows.append(r)
        print("H=%-4d score=%-10s nodes=%-9s bestmove=%s" % (
            h, r["score"], r["nodes"], r["bestmove"]))
    print("=== B. THE DISCRIMINATOR: counter 91 and 92 across four depths")
    for h in (91, 92):
        for d in DEPTHS:
            r = run(exe, BOARD % h, d)
            r["halfmove"], r["arm"] = h, "discriminator"
            rows.append(r)
            print("H=%-4d depth=%-3d score=%-10s nodes=%-10s seldepth=%s" % (
                h, d, r["score"], r["nodes"], r["seldepth"]))
    print("=== C. first halfmove with cp 0, as a function of depth")
    collapse = {}
    for d in DEPTHS:
        first = None
        for h in range(85, 101):
            r = run(exe, BOARD % h, d)
            r["halfmove"], r["arm"] = h, "collapse-scan"
            rows.append(r)
            if r["score"] == "cp 0":
                first = h
                break
        collapse[d] = first
        print("depth %-3d first halfmove with cp 0: %s" % (d, first))
    with open(os.path.join(outdir, "results.json"), "w") as f:
        json.dump({"exe": os.path.realpath(exe), "board": BOARD, "s14": S14,
                   "rows": rows, "first_cp0_by_depth": collapse}, f, indent=1)


if __name__ == "__main__":
    main()
