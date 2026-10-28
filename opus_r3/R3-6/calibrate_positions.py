#!/usr/bin/env python3
"""R3-6: pick the 30 positions and their fixed depths.

Candidates (in priority order; the first N of each class that pass the screen are kept):
  opening    10: bench.0, bench.4, bench.7 and the forge-10000 openings of positions50.fen
                 (Forge-1, -1429, -2858, -4286, -5715, -7143, -8572; spares: the other Forge-* lines)
  middlegame 12: bench.1, bench.2, bench.5 and nine ECM lines of positions50.fen
                 (ECM.946, 1066, 1131, 1218, 1304, 1377, 1423, 1503, 1602; spares: the other ECM lines)
  endgame     8: bench.3, bench.6 and low-material lines of the lock suites (at most 4 non-pawn
                 pieces, no queens): WAC.002, 086, 087, 100, ECM.1257, 1536, 1584, 1578 (spares
                 ECM.1546, WAC.107, WAC.229)
Screen and depth: one Threads=1 run per candidate (fresh process, Hash 64, ucinewgame,
`go depth 60`, stopped once an iteration ends after 10 s or 16 s have passed). A Threads=1
fixed-depth search is deterministic, so the info line of depth d gives the exact nodes and the
time-to-depth of `go depth d`. Kept depth = the deepest d with time <= --target-s (default 5.5 s),
moved one deeper if that takes < 2 s and the next one <= 10 s. Candidates that show a mate score
at any depth >= 8, or whose chosen depth would take < 2 s or > 10 s, are dropped (next spare).

usage: calibrate_positions.py <exe> <positions50.fen> <lock_archive_dir> <out.tsv> [--log calib.jsonl]
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from smp_ttd import Engine, INFO  # noqa: E402

OPENING = ["bench.0", "bench.4", "bench.7", "Forge-1", "Forge-1429", "Forge-2858", "Forge-4286", "Forge-5715",
           "Forge-7143", "Forge-8572", "Forge-715", "Forge-2143", "Forge-3572", "Forge-5001", "Forge-6429",
           "Forge-7858", "Forge-9286"]
MIDDLE = ["bench.1", "bench.2", "bench.5", "ECM.946", "ECM.1066", "ECM.1131", "ECM.1218", "ECM.1304", "ECM.1377",
          "ECM.1423", "ECM.1503", "ECM.1602", "ECM.1009", "ECM.1179", "ECM.1267", "ECM.1340", "ECM.1561"]
ENDGAME = ["bench.3", "bench.6", "WAC.002", "WAC.086", "WAC.087", "WAC.100", "ECM.1257", "ECM.1536", "ECM.1584",
           "ECM.1578", "ECM.1546", "WAC.107", "WAC.229"]
WANT = {"opening": 10, "middlegame": 12, "endgame": 8}


def suite_fens(path):
    out = {}
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.strip()
        if not line:
            continue
        f = line.split()
        m = re.search(r'id "?([^";]+)', line)
        out[m.group(1) if m else f"{path}:{n}"] = " ".join(f[:4]) + " 0 1"
    return out


def calibrate(exe, fen, cap_s=16.0, stop_after_ms=10000):
    eng = Engine(exe)
    eng.send("uci")
    eng.until(lambda l: l == "uciok", 60)
    for name, value in (("Hash", 64), ("Threads", 1), ("OwnBook", "false")):
        eng.send(f"setoption name {name} value {value}")
    eng.send("ucinewgame")
    eng.send("isready")
    eng.until(lambda l: l == "readyok", 60)
    eng.send(f"position fen {fen}")
    t0 = time.perf_counter()
    eng.send("go depth 60")
    rows, stopped = {}, False
    while True:
        try:
            _, line = eng.lines.get(timeout=0.2)
        except Exception:
            line = ""
        if line is None:
            raise RuntimeError("engine exited")
        m = INFO.match(line) if line else None
        if m:
            d = int(m.group(1))
            rows.setdefault(d, {"depth": d, "time_ms": int(m.group(8)), "nodes": int(m.group(5)),
                                "score": f"{m.group(3)} {m.group(4)}"})
            if int(m.group(8)) >= stop_after_ms and not stopped:
                eng.send("stop")
                stopped = True
        if line and line.startswith("bestmove"):
            break
        if not stopped and time.perf_counter() - t0 > cap_s:
            eng.send("stop")
            stopped = True
    eng.send("quit")
    eng.proc.wait(timeout=60)
    return [rows[d] for d in sorted(rows)]


def choose(rows, target_s, lo_s=2.0, hi_s=10.0):
    if any(r["score"].startswith("mate") for r in rows if r["depth"] >= 8):
        return None, "mate score"
    ok = [r for r in rows if r["time_ms"] <= target_s * 1000]
    if not ok:
        return None, "first iterations already too slow"
    pick = ok[-1]
    nxt = [r for r in rows if r["depth"] == pick["depth"] + 1]
    if pick["time_ms"] < lo_s * 1000 and nxt and nxt[0]["time_ms"] <= hi_s * 1000:
        pick = nxt[0]
    if not lo_s * 1000 <= pick["time_ms"] <= hi_s * 1000:
        return None, f"no depth in [{lo_s}, {hi_s}] s"
    return pick, "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("positions50")
    ap.add_argument("lock_archive")
    ap.add_argument("out")
    ap.add_argument("--log")
    ap.add_argument("--target-s", type=float, default=5.5)
    a = ap.parse_args()
    fens = {}
    for line in open(a.positions50, encoding="utf-8"):
        if " ; " in line:
            fen, ident = [x.strip() for x in line.split(" ; ", 1)]
            fens[ident] = fen
    for suite in ("wac300.epd", "ecm_gcp.epd"):
        for ident, fen in suite_fens(f"{a.lock_archive}/4_tests/suites/{suite}").items():
            fens.setdefault(ident, fen)
    kept = []
    log = open(a.log, "a", encoding="utf-8", newline="\n") if a.log else None
    for cls, ids in (("opening", OPENING), ("middlegame", MIDDLE), ("endgame", ENDGAME)):
        n = 0
        for ident in ids:
            if n == WANT[cls]:
                break
            rows = calibrate(a.exe, fens[ident])
            pick, why = choose(rows, a.target_s)
            if log:
                log.write(json.dumps({"id": ident, "class": cls, "fen": fens[ident], "rows": rows,
                                      "pick": pick, "why": why}) + "\n")
                log.flush()
            print(f"{cls} {ident}: {why} {pick}", flush=True)
            if pick:
                kept.append((ident, cls, pick["depth"], fens[ident], pick))
                n += 1
        if n < WANT[cls]:
            print(f"WARNING: only {n} {cls} positions", flush=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# id\tclass\tdepth\tfen   (R3-6 calibrate_positions.py; T1 calibration time/nodes in the log)\n")
        for ident, cls, depth, fen, _ in kept:
            fh.write(f"{ident}\t{cls}\t{depth}\t{fen}\n")
    print(f"wrote {len(kept)} positions to {a.out}")


if __name__ == "__main__":
    main()
