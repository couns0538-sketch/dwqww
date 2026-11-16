#!/usr/bin/env python3
"""mate_rate_strict.py -- the lone-king mate REPORTING rate, measured with a STRICT harness.

WHY THIS FILE EXISTS: my first PC20 measurement (30-F36) used a loose harness — setoption and
isready sent in a burst with 4 ms sleeps and no readyok verification — and its numbers were not
reproducible (8 of 40 boards flipped between runs). A strict harness (every setoption followed by
isready read to readyok, every search awaited) shows the engine is deterministic: 5/5 identical
scores and identical node counts on repeated fresh processes. The numbers below come from the
strict harness only; 30-F36's loose numbers are retracted in FINDINGS.md.

Settings: Threads 1, Hash 16, OwnBook false, then either nothing (defaults) or the full PC20 list.

usage: mate_rate_strict.py OUTDIR [N_PER_KIND] [DEPTH]
"""
import json
import os
import subprocess
import sys
import threading
import time

PCX = "/home/ubuntu/b/pc/forge"
BASE = "/home/ubuntu/b/rel/forge"
ENV = {k: v for k, v in os.environ.items()
       if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS", "LSAN_OPTIONS")}
S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5),
       ("LmpBase", 8), ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24),
       ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212), ("SingularDepth", 6),
       ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
DEF = [("OwnBook", "false")]


def search_strict(exe, fen, depth, settings, timeout=240.0):
    """Every setoption confirmed by readyok; every search awaited. Returns score/nodes/move."""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1, env=ENV)
    out = []
    lock = threading.Lock()

    def pump():
        try:
            for l in p.stdout:
                with lock:
                    out.append(l.rstrip("\n"))
        except Exception:
            pass

    threading.Thread(target=pump, daemon=True).start()

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def ready(timeout=90.0):
        with lock:
            m = len(out)
        send("isready")
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            with lock:
                if any(x.strip() == "readyok" for x in out[m:]):
                    return True
            if p.poll() is not None:
                return False
            time.sleep(0.002)
        return False

    send("uci")
    t0 = time.monotonic()
    while time.monotonic() - t0 < 60:
        with lock:
            if any(x.strip() == "uciok" for x in out):
                break
        time.sleep(0.002)
    send("setoption name Threads value 1")
    ready()
    send("setoption name Hash value 16")
    ready()
    bad = []
    for name, value in settings:
        with lock:
            m = len(out)
        send("setoption name %s value %s" % (name, value))
        if not ready():
            bad.append("no readyok after %s" % name)
        with lock:
            bad += [x for x in out[m:] if "unknown option" in x or "invalid value" in x]
    send("ucinewgame")
    ready()
    send("position fen " + fen)
    ready()
    with lock:
        mark = len(out)
    send("go depth %d" % depth)
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        with lock:
            if any(x.startswith("bestmove") for x in out[mark:]):
                break
        time.sleep(0.003)
    with lock:
        blk = out[mark:]
    try:
        send("quit")
    except Exception:
        pass
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()
    infos = [x for x in blk if x.startswith("info depth") and " pv" in x]
    score = nodes = bm = None
    if infos:
        t = infos[-1].split()
        if "score" in t:
            score = " ".join(t[t.index("score") + 1:t.index("score") + 3])
        if "nodes" in t:
            nodes = int(t[t.index("nodes") + 1])
    for l in blk:
        if l.startswith("bestmove"):
            parts = l.split()
            bm = parts[1] if len(parts) > 1 else None
    return {"score": score, "nodes": nodes, "bestmove": bm,
            "reports_mate": bool(score and score.startswith("mate")), "bad": bad}


def main():
    outdir = sys.argv[1]
    n_per = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    depth = int(sys.argv[3]) if len(sys.argv) > 3 else 12
    os.makedirs(outdir, exist_ok=True)
    boards = json.load(open(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "out_bareking20", "bare_king_mates.json")))["rows"]
    boards = [b for b in boards][:n_per * 2]
    report = {"depth": depth, "boards": len(boards), "runs": {}}
    for label, exe, settings in (("base_default", BASE, DEF),
                                 ("pc_default", PCX, DEF),
                                 ("pc_PC20", PCX, PC20)):
        res = []
        for b in boards:
            r = search_strict(exe, b["fen"], depth, settings)
            r.update({"fen": b["fen"], "kind": b["kind"], "mate_plies": b["mate_plies"]})
            res.append(r)
        by = {}
        for r in res:
            d = by.setdefault(r["kind"], {"n": 0, "mate": 0})
            d["n"] += 1
            if r["reports_mate"]:
                d["mate"] += 1
        tot_m = sum(d["mate"] for d in by.values())
        report["runs"][label] = {"by_kind": by, "mate": tot_m, "n": len(res),
                                 "rows": res,
                                 "bad_option_lines": sum(1 for r in res if r["bad"])}
        print("%-13s mate %2d/%2d   %s" % (
            label, tot_m, len(res),
            "  ".join("%s %d/%d" % (k, d["mate"], d["n"]) for k, d in sorted(by.items()))))
    # determinism check: repeat the pc_PC20 arm and compare
    rep = []
    for b in boards[:8]:
        rep.append(search_strict(PCX, b["fen"], depth, PC20)["score"])
    first8 = [r["score"] for r in report["runs"]["pc_PC20"]["rows"][:8]]
    report["pc20_repeat_matches_first_run"] = rep == first8
    report["pc20_repeat_first8"] = rep
    report["pc20_first8"] = first8
    print()
    print("pc_PC20 repeated on the first 8 boards, identical:", rep == first8)
    with open(os.path.join(outdir, "mate_rate_strict.json"), "w") as f:
        json.dump(report, f, indent=1)


if __name__ == "__main__":
    main()
