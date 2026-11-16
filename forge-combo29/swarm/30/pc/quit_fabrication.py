#!/usr/bin/env python3
"""quit_fabrication.py -- WHEN does closing stdin mid-search fabricate a bestmove, and is it
harmful on the PC build (the engine the owner plays)?

19-F12 reported it on the base tree. This script measures it on BOTH builds along three axes:
  * the go form (depth / nodes / movetime / infinite / clock),
  * whether the fabricated move is LEGAL and whether it is the same move the finished search
    would have played (i.e. is it harmful, or merely unlabelled?).

Every probe is a fresh process. A pipelined probe writes all lines at once (quit lands mid-search).
A control probe waits for bestmove, then writes quit.

usage: quit_fabrication.py OUTDIR
"""
import json
import os
import subprocess
import sys
import threading
import time

EXES = {"base": "/home/ubuntu/b/rel/forge", "pc": "/home/ubuntu/b/pc/forge"}
POSITIONS = {
    "startpos": "position startpos",
    "middlegame": "position fen r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 0 1",
    "matein1": "position fen 6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1",
}
GOS = ["go depth 12", "go nodes 200000", "go movetime 2000", "go infinite",
       "go wtime 5000 btime 5000"]
ENV = {k: v for k, v in os.environ.items()
       if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS", "LSAN_OPTIONS")}


def _spawn(exe):
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
    return p, out, lock


def _parse(lines, mark=0):
    blk = lines[mark:]
    infos = [l for l in blk if l.startswith("info depth")]
    bms = [l.split()[1] for l in blk if l.startswith("bestmove") and len(l.split()) > 1]
    nodes = None
    if infos:
        t = infos[-1].split()
        if "nodes" in t:
            nodes = int(t[t.index("nodes") + 1])
    return {"info_lines": len(infos), "bestmove": bms[0] if bms else None,
            "n_bestmoves": len(bms), "nodes": nodes}


def pipelined(exe, pos, go, delay_ms=0):
    p, out, lock = _spawn(exe)
    p.stdin.write("uci\nisready\n%s\n%s\n" % (pos, go))
    p.stdin.flush()
    if delay_ms:
        time.sleep(delay_ms / 1000.0)
    try:
        p.stdin.write("quit\n")
        p.stdin.flush()
    except Exception:
        pass
    try:
        p.wait(timeout=90)
    except Exception:
        p.kill()
    time.sleep(0.05)
    with lock:
        lines = list(out)
    return _parse(lines)


def waited(exe, pos, go, timeout=150.0):
    p, out, lock = _spawn(exe)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    send("uci")
    time.sleep(0.05)
    send("isready")
    time.sleep(0.05)
    send(pos)
    with lock:
        mark = len(out)
    send(go)
    if go.strip() == "go infinite":
        time.sleep(2.0)
        send("stop")
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        with lock:
            if any(x.startswith("bestmove") for x in out[mark:]):
                break
        time.sleep(0.005)
    with lock:
        lines = list(out)
    send("quit")
    try:
        p.wait(timeout=60)
    except Exception:
        pass
    return _parse(lines, mark)


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    report = {"generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "rows": []}
    print("%-5s %-11s %-24s %-26s %-26s %s" % (
        "build", "position", "go", "quit IMMEDIATELY", "control (waited)", "move"))
    for bname, exe in EXES.items():
        for pname, pos in POSITIONS.items():
            for go in GOS:
                fast = pipelined(exe, pos, go, delay_ms=0)
                ctrl = waited(exe, pos, go)
                row = {"build": bname, "position": pname, "go": go,
                       "immediate": fast, "control": ctrl,
                       "same_move": fast["bestmove"] == ctrl["bestmove"],
                       "fabricated_unlabelled": fast["info_lines"] == 0,
                       "fabricated_and_wrong": (fast["info_lines"] == 0
                                                and fast["bestmove"] != ctrl["bestmove"])}
                report["rows"].append(row)
                print("%-5s %-11s %-24s %-26s %-26s %s" % (
                    bname, pname, go,
                    "bm=%s n=%s i=%s" % (fast["bestmove"], fast["nodes"], fast["info_lines"]),
                    "bm=%s n=%s" % (ctrl["bestmove"], ctrl["nodes"]),
                    "SAME" if row["same_move"] else "DIFFERENT"))
    fabricated = [r for r in report["rows"] if r["fabricated_unlabelled"]]
    differ = [r for r in report["rows"] if r["fabricated_and_wrong"]]
    report["summary"] = {
        "rows": len(report["rows"]),
        "fabricated_unlabelled": len(fabricated),
        "fabricated_and_a_different_move": len(differ),
        "builds_affected": sorted({r["build"] for r in fabricated}),
        "gos_affected": sorted({r["go"] for r in fabricated}),
        "positions_affected": sorted({r["position"] for r in fabricated}),
    }
    print()
    print(json.dumps(report["summary"], indent=1))
    with open(os.path.join(outdir, "quit_fabrication.json"), "w") as f:
        json.dump(report, f, indent=1)


if __name__ == "__main__":
    main()
