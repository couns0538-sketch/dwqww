#!/usr/bin/env python3
"""quit_timing.py -- the fabrication needs quit to land WHILE the search runs. Find the window.

My previous probe waited 1.5 s before sending `quit`; a depth-12 startpos search finishes in ~32 ms,
so nothing was interrupted and nothing was fabricated. That is itself the finding: the fault is
TIMING-dependent, which is why it survived so long (a GUI that always reads `bestmove` never sees it,
and neither does a test that sleeps first).

This script sends `quit` at a range of delays after `go` and reports, for each, whether the answer
had zero info lines (fabricated) and whether it differed from the uninterrupted answer.

usage: quit_timing.py OUTDIR
"""
import json
import os
import subprocess
import sys
import threading
import time

import chess

EXES = {"base": "/home/ubuntu/b/rel/forge", "pc": "/home/ubuntu/b/pc/forge"}
CASES = {
    "startpos_depth12": ("position startpos", "go depth 12"),
    "matein1_depth12": ("position fen 6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1", "go depth 12"),
}
DELAYS_MS = [0, 1, 2, 5, 10, 20, 40, 80, 200]
ENV = {k: v for k, v in os.environ.items()
       if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS", "LSAN_OPTIONS")}


def spawn(exe):
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


def parse(out, mark, fen):
    blk = out[mark:]
    infos = [l for l in blk if l.startswith("info depth")]
    bms = [l.split()[1] for l in blk if l.startswith("bestmove") and len(l.split()) > 1]
    legal = None
    if bms:
        b = chess.Board(fen)
        legal = bms[0] == "0000" or any(m.uci() == bms[0] for m in b.legal_moves)
    return {"info_lines": len(infos), "bestmove": bms[0] if bms else None, "legal": legal}


def fen_of(pos):
    return pos.split("fen ", 1)[1] if "fen " in pos else chess.STARTING_FEN


def one(exe, pos, go, delay_ms):
    p, out, lock = spawn(exe)

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
    if delay_ms:
        time.sleep(delay_ms / 1000.0)
    try:
        send("quit")
    except Exception:
        pass
    try:
        p.wait(timeout=30)
    except Exception:
        p.kill()
    time.sleep(0.05)
    with lock:
        return parse(out, mark, fen_of(pos))


def control(exe, pos, go):
    p, out, lock = spawn(exe)

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
    t0 = time.monotonic()
    while time.monotonic() - t0 < 180:
        with lock:
            if any(x.startswith("bestmove") for x in out[mark:]):
                break
        time.sleep(0.005)
    with lock:
        r = parse(out, mark, fen_of(pos))
    send("quit")
    try:
        p.wait(timeout=20)
    except Exception:
        pass
    return r


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    report = {"delays_ms": DELAYS_MS, "rows": []}
    for bname, exe in EXES.items():
        for cname, (pos, go) in CASES.items():
            ctrl = control(exe, pos, go)
            print("== %-4s %-16s control: bm=%s infos=%s" % (
                bname, cname, ctrl["bestmove"], ctrl["info_lines"]))
            for d in DELAYS_MS:
                r = one(exe, pos, go, d)
                r.update({"build": bname, "case": cname, "delay_ms": d,
                          "control_bestmove": ctrl["bestmove"],
                          "fabricated": r["info_lines"] == 0 and r["bestmove"] is not None,
                          "same_as_control": r["bestmove"] == ctrl["bestmove"]})
                report["rows"].append(r)
                flag = "  <-- FABRICATED" + (" and WRONG" if not r["same_as_control"] else "") \
                    if r["fabricated"] else ""
                print("   quit at %4d ms -> bm=%-6s infos=%-3s legal=%-5s%s" % (
                    d, r["bestmove"], r["info_lines"], r["legal"], flag))
    fab = [r for r in report["rows"] if r["fabricated"]]
    wrong = [r for r in fab if not r["same_as_control"]]
    report["summary"] = {"probes": len(report["rows"]),
                        "fabricated": len(fab),
                        "fabricated_and_wrong": len(wrong),
                        "earliest_fabrication_ms": min((r["delay_ms"] for r in fab), default=None),
                        "latest_fabrication_ms": max((r["delay_ms"] for r in fab), default=None)}
    with open(os.path.join(outdir, "quit_timing.json"), "w") as f:
        json.dump(report, f, indent=1)
    print()
    print(json.dumps(report["summary"], indent=1))


if __name__ == "__main__":
    main()
