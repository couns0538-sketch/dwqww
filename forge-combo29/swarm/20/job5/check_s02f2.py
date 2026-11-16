#!/usr/bin/env python3
"""check_s02f2.py — seat 20, area 10 job 5: my OWN check of seat 02's S-F2 (empty searchmoves -> 0000).

My harness, written from their one-sentence claim. Reads the full answer of each command, so it can see both
the `info string` line and the bestmove, and counts nodes from the info lines.

usage: check_s02f2.py <release-exe> <asan-exe> <outdir>
"""
import json
import os
import re
import subprocess
import sys
import threading
import time

REL, ASAN, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)
START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def ask(exe, lines, timeout=40.0):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    out = []
    lock = threading.Lock()

    def rd():
        try:
            for l in p.stdout:
                with lock:
                    out.append(l.rstrip("\n"))
        except Exception:
            pass
    threading.Thread(target=rd, daemon=True).start()
    for line in lines:
        p.stdin.write(line + "\n")
        p.stdin.flush()
        if line.startswith("go"):
            t0 = time.monotonic()
            while time.monotonic() - t0 < timeout:
                with lock:
                    if any(x.startswith("bestmove") for x in out):
                        break
                time.sleep(0.002)
    try:
        p.stdin.write("quit\n")
        p.stdin.flush()
        p.wait(timeout=15)
    except Exception:
        p.kill()
    with lock:
        return list(out)


def classify(transcript):
    bests = [x.split()[1] for x in transcript if x.startswith("bestmove")]
    infostr = [x for x in transcript if x.startswith("info string")]
    depths = [x for x in transcript if x.startswith("info depth")]
    nodes = 0
    for x in depths:
        m = re.search(r"nodes (\d+)", x)
        if m:
            nodes = max(nodes, int(m.group(1)))
    return {"bestmove": bests[-1] if bests else "<none>", "count": len(bests),
            "info_string": infostr, "depth_lines": len(depths), "max_nodes": nodes}


PRE = ["uci", "setoption name OwnBook value false", "isready", "ucinewgame", "isready"]
CASES = [
    ("a_empty_searchmoves", "go searchmoves depth 2", "the keyword with nothing after it"),
    ("b_illegal_searchmove", "go searchmoves e7e5 depth 2", "a black move, white to move"),
    ("c_positive_control", "go searchmoves a2a3 b2b3 depth 4", "two legal moves"),
    ("d_plain_depth2", "go depth 2", "no restriction"),
    ("e_plain_movetime", "go movetime 20", "no restriction"),
    ("f_legal_one", "go searchmoves a2a3 depth 4", "one legal move"),
]

report = {"exe": {"release": REL, "asan": ASAN}, "fen": START, "cases": []}
for idx, (label, go, why) in enumerate(CASES):
    for which, exe in (("release", REL), ("asan", ASAN)):
        lines = PRE + [f"position fen {START}", "isready", go]
        tr = ask(exe, lines)
        r = classify(tr)
        r.update({"case": label, "go": go, "why": why, "exe": which, "transcript": tr})
        report["cases"].append(r)
        print(f"{which:8s} {label:22s} bestmove={r['bestmove']:6s} "
              f"info_string={len(r['info_string'])} depth_lines={r['depth_lines']:2d} "
              f"max_nodes={r['max_nodes']:5d}")
        for s in r["info_string"]:
            print(f"          | {s}")

# raw transcripts to disk (full answer of every case, both builds)
with open(os.path.join(OUT, "check_s02f2.json"), "w") as f:
    json.dump(report, f, indent=1)
with open(os.path.join(OUT, "check_s02f2.txt"), "w") as f:
    for r in report["cases"]:
        f.write(f"### {r['exe']} / {r['case']} : {r['go']}\n")
        for line in r["transcript"]:
            if line.startswith("option"):
                continue
            f.write("  " + line + "\n")
        f.write("\n")
print("\nwrote", os.path.join(OUT, "check_s02f2.txt"))
